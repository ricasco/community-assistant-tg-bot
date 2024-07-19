from telegram.ext import CallbackContext, ContextTypes
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
import requests
import os
from datetime import datetime, timedelta
import json
import unicodedata
import regex
from telegram.error import BadRequest
import asyncio
import re
import time

# Dictionary to track users' message counts and timestamps
user_message_limits = {}
active_users = {}
new_group_members = {}

keyboard = [[InlineKeyboardButton("Menu", callback_data='menu')]]
reply_markup = InlineKeyboardMarkup(keyboard)

async def handle_setup_request(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Verify that the command is coming from an admin
    admins = await context.bot.get_chat_administrators(chat_id=chat_id)
    if any(admin.user.id == user_id for admin in admins):
        # Define the buttons to show on the menu
        keyboard = [
            [InlineKeyboardButton("Menu", callback_data='menu')],
            # Add other buttons here if needed
        ]

        # Convert to InlineKeyboardMarkup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the private message with the keyboard
        await context.bot.send_message(chat_id=user_id, 
                                       text="Click on the menu to see options", 
                                       reply_markup=reply_markup)
        return True
    else:
        await update.message.reply_text("Only the admins can run this command and you are not. So, what are you trying to do? 🤌")
        return False

# Callback query handler for the menu options
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # This is necessary to provide feedback to Telegram

    # Here you handle the callback data and set the bot's status
    if query.data == 'enable_auto_refresh':
        context.bot_data["bot_active"] = True  # Enable the bot
        await query.edit_message_text(text="The bot is enabled.", reply_markup=reply_markup)

    elif query.data == 'disable_auto_refresh':
        context.bot_data["bot_active"] = False  # Disable the bot
        await query.edit_message_text(text="The bot is disabled.", reply_markup=reply_markup)

    elif query.data == 'add_spam_kw':
        context.bot_data['awaiting_spam_keyword'] = True  # Set a flag to await spam keyword
        context.bot_data['awaiting_remove_spam_keyword'] = False  # Ensure this is false
        await query.edit_message_text(text="Please send the spam keyword you want to add:")

    elif query.data == 'remove_spam_kw':
        context.bot_data['awaiting_spam_keyword'] = False  # Set a flag to await spam keyword
        context.bot_data['awaiting_remove_spam_keyword'] = True
        await query.edit_message_text(text="Please send the spam keyword you want to remove:")

    elif query.data == 'spamkw_list':
        await spamkw_list(update, context)

    elif query.data == 'add_faq':
        context.bot_data[f'awaiting_faq_question_{update.effective_user.id}'] = True
        await query.edit_message_text(text="Please send the FAQ question you want to add:")

    elif query.data == 'remove_faq':
        context.bot_data[f'awaiting_faq_removal_{update.effective_user.id}'] = True
        await query.edit_message_text(text="Please send the FAQ question you want to remove:")

    if query.data == 'menu':
        # Define the menu options
        menu_keyboard = [
          [InlineKeyboardButton("🟢 Enable", callback_data='enable_auto_refresh'), InlineKeyboardButton("🔴 Disable", callback_data='disable_auto_refresh')],
          [InlineKeyboardButton("➕ Add Ban KW", callback_data='add_spam_kw'), InlineKeyboardButton("➖ Remove Ban KW", callback_data='remove_spam_kw')],
          [InlineKeyboardButton("📜 Ban KW List", callback_data='spamkw_list')],
          [InlineKeyboardButton("➕ Add FAQ", callback_data='add_faq'), InlineKeyboardButton("➖ Remove FAQ", callback_data='remove_faq')]
        ]

        menu_markup = InlineKeyboardMarkup(menu_keyboard)

        await query.edit_message_text(text="Select an option:", reply_markup=menu_markup)

async def handle_new_spam_keyword(update: Update, context: CallbackContext):
    if context.bot_data.get('awaiting_spam_keyword'):
        new_keyword = update.message.text.strip()
        try:
            # Open the file in read mode, load the JSON content
            with open("spamkw.json", "r") as file:
                data = json.load(file)
                # Add the new keyword to the spam_keywords list
                data["spam_keywords"].append(new_keyword)

            # Open the file in write mode and write the updated JSON content
            with open("spamkw.json", "w") as file:
                json.dump(data, file, indent=4)  # Use indent for pretty-printing

            context.bot_data['awaiting_spam_keyword'] = False

            await update.message.reply_text(f"The keyword '{new_keyword}' has been added to the spam list.", reply_markup=reply_markup)
        except Exception as e:
            await update.message.reply_text("Failed to add the new spam keyword. Please try again.", reply_markup=reply_markup)
            print(f"Error adding new spam keyword: {e}")
    else:
        # Handle other text messages normally
        pass  # You can put existing text message handling code here

async def handle_remove_spam_keyword(update: Update, context: CallbackContext):
    if context.bot_data.get('awaiting_remove_spam_keyword'):  # Check if we are awaiting a keyword to remove
        keyword_to_remove = update.message.text.strip()
        try:
            with open("spamkw.json", "r") as file:
                data = json.load(file)
                # Check if the keyword is in the list and remove it
                if keyword_to_remove in data["spam_keywords"]:
                    data["spam_keywords"].remove(keyword_to_remove)
                    # Write the updated list back to the file
                    with open("spamkw.json", "w") as outfile:
                        json.dump(data, outfile, indent=4)

                    await update.message.reply_text(f"The keyword '{keyword_to_remove}' has been removed from the spam list.", reply_markup=reply_markup)
                else:
                    await update.message.reply_text(f"The keyword '{keyword_to_remove}' was not found in the spam list.", reply_markup=reply_markup)
            context.bot_data['awaiting_remove_spam_keyword'] = False  # Reset the flag
        except Exception as e:
            await update.message.reply_text("Failed to remove the spam keyword. Please try again.", reply_markup=reply_markup)
            print(f"Error removing spam keyword: {e}")
    else:
        # Handle other text messages normally
        pass  # You can put existing text message handling code here

async def handle_new_faq_question(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id  # Get the user ID
    if context.bot_data.get(f'awaiting_faq_question_{user_id}'):  # Use the user-specific flag
        new_question = update.message.text.strip()
        context.bot_data[f'new_faq_question_{user_id}'] = new_question  # Store the new question with user-specific key
        context.bot_data.pop(f'awaiting_faq_question_{user_id}', None)  # Clear the FAQ question awaiting flag
        context.bot_data[f'awaiting_faq_answer_{user_id}'] = True  # Set a flag to await the new FAQ answer, user-specific
        await update.message.reply_text(f"Received question: '{new_question}'. Now, please send the answer.")

async def handle_new_faq_answer(update: Update, context: CallbackContext, client, collection_config, vectorstore):
    user_id = update.message.from_user.id  # Get the user ID
    if context.bot_data.get(f'awaiting_faq_answer_{user_id}'):  # Use the user-specific flag
        new_answer = update.message.text.strip()
        new_question = context.bot_data.get(f'new_faq_question_{user_id}', 'Unknown')  # Retrieve the stored question
        try:
            # Append new FAQ to the file
            with open("botbuddy.txt", "a") as file:
                file.write(f"\n\nQ: {new_question}\nA: {new_answer}")

            # Clear the flags
            context.bot_data.pop(f'awaiting_faq_answer_{user_id}', None)
            context.bot_data.pop(f'new_faq_question_{user_id}', None)

            # Notify the user
            response_message = f"The new FAQ has been added: '{new_question}' - '{new_answer}'"

            await update.message.reply_text(response_message, reply_markup=reply_markup)

            # Additional: Send the same message to @usernameisrick in a private chat
            usernameisrick_chat_id = context.bot_data.get('usernameisrick_chat_id')  # Retrieve the stored chat ID
            if usernameisrick_chat_id:  # Check if we have the chat ID
                bb_msg = f"BOT BUDDY BOT: {response_message}"
                await context.bot.send_message(chat_id=usernameisrick_chat_id, text=bb_msg)
            else:
                print("Chat ID for @usernameisrick not found. Please ensure the user has initiated a chat with the bot.")

            # Re-read the updated file and split into chunks
            with open("botbuddy.txt", "r") as f:
                raw_text = f.read()
            texts = get_chunks(raw_text)

            # Refresh the vectorstore content
            client.delete_collection(collection_name=os.getenv("QDRANT_COLLECTION"))  # Remove existing data
            client.recreate_collection(collection_name=os.getenv("QDRANT_COLLECTION"), vectors_config=collection_config)  # Recreate the collection
            vectorstore.add_texts(texts)  # Add new data

        except Exception as e:
            await update.message.reply_text("Failed to add the new FAQ. Please try again.", reply_markup=reply_markup)
            print(f"Error adding new FAQ: {e}")

# Function to split a text into chunks of Q&A pairs
def get_chunks(text):
    separator = "\n\n"
    qna_pairs = text.split(separator)
    chunks = [pair for pair in qna_pairs if pair]
    return chunks

async def handle_remove_faq_question(update: Update, context: CallbackContext, client, collection_config, vectorstore):
    user_id = update.message.from_user.id  # Get the user ID
    if context.bot_data.get(f'awaiting_faq_removal_{user_id}', False):  # Use the user-specific flag
        question_to_remove = update.message.text.strip()
        try:
            # Read the existing FAQs
            with open("botbuddy.txt", "r") as file:
                lines = file.readlines()

            # Combine lines to reconstruct Q&A pairs
            qa_pairs = get_chunks(''.join(lines))

            # Check if the question exists in the current Q&A pairs
            if any(pair.startswith(f"Q: {question_to_remove}\n") for pair in qa_pairs):
                # Filter out the Q&A pair to remove
                updated_qa_pairs = [pair for pair in qa_pairs if not pair.startswith(f"Q: {question_to_remove}\n")]

                # Write the updated FAQs back to the file
                with open("botbuddy.txt", "w") as file:
                  file.write("\n\n".join(updated_qa_pairs))

                # Notify the user
                response_message = f"The FAQ with the question: '{question_to_remove}' has been removed."

                await update.message.reply_text(response_message, reply_markup=reply_markup)

                # Additional: Send the same message to @usernameisrick in a private chat
                usernameisrick_chat_id = context.bot_data.get('usernameisrick_chat_id')  # Retrieve the stored chat ID
                if usernameisrick_chat_id:  # Check if we have the chat ID
                    bb_msg = f"BOT BUDDY BOT: {response_message}"
                    await context.bot.send_message(chat_id=usernameisrick_chat_id, text=bb_msg)
                else:
                    print("Chat ID for @usernameisrick not found. Please ensure the user has initiated a chat with the bot.")

                # Refresh the vectorstore content
                client.delete_collection(collection_name=os.getenv("QDRANT_COLLECTION"))  # Remove existing data
                client.recreate_collection(collection_name=os.getenv("QDRANT_COLLECTION"), vectors_config=collection_config)  # Recreate the collection
                vectorstore.add_texts(updated_qa_pairs)  # Add new data
            else:
                # Notify the user that the question does not exist

                await update.message.reply_text(f"The question: '{question_to_remove}' is not included in the knowledge base.", reply_markup=reply_markup)

            # Clear the flag
            context.bot_data.pop(f'awaiting_faq_removal_{user_id}', None)

        except Exception as e:
          await update.message.reply_text("Failed to remove the FAQ. Please try again.", reply_markup=reply_markup)
          print(f"Error removing FAQ: {e}")

async def spamkw_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        with open("spamkw.json", "r") as file:
            data = json.load(file)
            spam_keywords = data.get("spam_keywords", [])
            message_text = "*Spam Keywords List:*\n" + "\n".join(spam_keywords)

        await query.edit_message_text(text=message_text, parse_mode='Markdown', disable_web_page_preview= True, reply_markup=reply_markup)
    except Exception as e:
        await query.edit_message_text(text="Failed to retrieve the spam keywords list.")
        print(f"Error retrieving spam keywords list: {e}")