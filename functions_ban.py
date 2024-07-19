from telegram.ext import CallbackContext, ContextTypes, ChatMemberHandler
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

# Dictionary to track users' message counts and timestamps
user_message_limits = {}
active_users = {}
new_group_members = {}

def normalize_text(text: str) -> str:
  # Ensure text is a string
  if not isinstance(text, str):
      return ''  # Return empty string or some other default string if text is not a string
  # Define RTL characters and invisible characters to remove
  rtl_chars = ['\u200F', '\u200E', '\u202B', '\u202E', '\u202C', '\u202A', '\u202D', '\u2066', '\u2067', '\u2068', '\u2069']
  invisible_chars = ['\u200B', '\u200C', '\uFEFF']
  # Combine all characters to remove
  chars_to_remove = rtl_chars + invisible_chars
  remove_pattern = f"[{''.join(chars_to_remove)}]"
  # Remove defined characters
  cleaned_text = re.sub(remove_pattern, '', text)

  # Define and replace homoglyphs with their base characters
  homoglyphs_replacements = {
      'а': 'a', 'ɑ': 'a', 'α': 'a', 'а': 'a', 'ᴀ': 'a', 'ạ': 'a', 'ặ': 'a', 'ả': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a', 'ₐ': 'a', 'Ḁ': 'a', 'ḁ': 'a', 'ἀ': 'a', 'ἁ': 'a', 'ἂ': 'a', 'ἃ': 'a', 'ἄ': 'a', 'ἅ': 'a', 'ἆ': 'a', 'ἇ': 'a', 'Ἀ': 'a', 'Ἁ': 'a', 'Ἂ': 'a', 'Ἃ': 'a', 'Ἄ': 'a', 'Ἅ': 'a', 'Ἆ': 'a', 'Ἇ': 'a', 'ᾀ': 'a', 'ᾁ': 'a', 'ᾂ': 'a', 'ᾃ': 'a', 'ᾄ': 'a', 'ᾅ': 'a', 'ᾆ': 'a', 'ᾇ': 'a', 'ᾈ': 'a', 'ᾉ': 'a', 'ᾊ': 'a', 'ᾋ': 'a', 'ᾌ': 'a', 'ᾍ': 'a', 'ᾎ': 'a', 'ᾏ': 'a', 'А': 'a', 'Α': 'a',  # Extends 'a' with various homoglyphs
      'і': 'i', 'Ꭵ': 'i', '᎐': 'i', '᎑': 'i', 'ı': 'i', 'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i', 'į': 'i', 'ĩ': 'i', 'ī': 'i', 'ĭ': 'i', 'Ì': 'i', 'Í': 'i', 'Î': 'i', 'Ï': 'i', 'и': 'i', 'і': 'i', 'ї': 'i', 'ǐ': 'i', 'ỉ': 'i', 'ȉ': 'i', 'ȋ': 'i', 'ị': 'i', 'ḭ': 'i', 'ḯ': 'i', 'ἰ': 'i', 'ἱ': 'i', 'ἲ': 'i', 'ἳ': 'i', 'ἴ': 'i', 'ἵ': 'i', 'ἶ': 'i', 'ἷ': 'i', 'ὶ': 'i', 'ί': 'i', 'ῐ': 'i', 'ῑ': 'i', 'ῒ': 'i', 'ΐ': 'i', 'ῖ': 'i', 'ῗ': 'i', 'і': 'i', 'ӏ': 'i', 'ᴉ': 'i', 'ᵢ': 'i', 'ⁱ': 'i', 'ℹ': 'i', 'ⅈ': 'i', 'ﬁ': 'i', 'ﬃ': 'i',   # Extends 'i' with various homoglyphs
      'o': 'o', 'о': 'o', 'ο': 'o', 'ό': 'o', 'ѻ': 'o', 'Ӧ': 'o', 'ӧ': 'o', 'Ө': 'o', 'ө': 'o', 'Ӫ': 'o', 'ọ': 'o', 'ỏ': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o', 'ọ': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ố': 'o', 'ồ': 'o', 'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o', 'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o', 'ö': 'o', 'ő': 'o', 'õ': 'o', 'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o', 'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'ọ': 'o', 'õ': 'o', 'ø': 'o', 'ō': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o', 'ō': 'o', 'ŏ': 'o', 'ő': 'o', 'ơ': 'o', 'ǒ': 'o', 'ǿ': 'o', 'ȯ': 'o', 'ȱ': 'o', 'ȫ': 'o', 'ȭ': 'o', 'ȯ': 'o', 'о': 'o', 'ӧ': 'o', 'ө': 'o', 'ǫ': 'o', 'ǭ': 'o', 'ɵ': 'o', 'ɔ': 'o', 'ѳ': 'o', 'Ѳ': 'o', 'ѻ': 'o', 'ԉ': 'o', 'ԓ': 'o', 'ᴏ': 'o', 'ᴑ': 'o', 'ᴓ': 'o', 'ᴼ': 'o', 'ｏ': 'o', 'Ｏ': 'o', 'Ⲟ': 'o', 'ⲟ': 'o',  # Extends 'o' with various homoglyphs
      'n': 'n', 'п': 'n', 'П': 'n', 'ṅ': 'n', 'ṇ': 'n', 'ṉ': 'n', 'ṋ': 'n', 'Ṇ': 'n', 'Ṉ': 'n', 'Ṋ': 'n', 'ń': 'n', 'ň': 'n', 'ñ': 'n', 'ņ': 'n', 'ŋ': 'n', 'ƞ': 'n', 'ɲ': 'n', 'ɳ': 'n', 'ȵ': 'n', 'ŉ': 'n', 'ᵰ': 'n', 'ᶇ': 'n', 'ɴ': 'n', 'ή': 'n', 'η': 'n', 'ν': 'n', 'и': 'n', 'й': 'n', 'и': 'n', 'ң': 'n', 'ҥ': 'n', 'ԉ': 'n', 'ԓ': 'n', 'ո': 'n', 'ռ': 'n', 'ነ': 'n', 'ኔ': 'n', 'ን': 'n', 'ኖ': 'n', 'ᑎ': 'n', 'ᑏ': 'n', 'ᑥ': 'n', 'ᴎ': 'n', 'ᴨ': 'n', 'ᴺ': 'n', 'ᵰ': 'n', 'ᶇ': 'n', 'ｎ': 'n', 'Ｎ': 'n',  # Extends 'n' with various homoglyphs
      'с': 'c', 'ϲ': 'c', 'с': 'c', 'ć': 'c', 'ĉ': 'c', 'č': 'c', 'ċ': 'c', 'ç': 'c', 'ȼ': 'c', '¢': 'c', 'ϲ': 'c', 'ҫ': 'c', 'ꜿ': 'c', 'ↄ': 'c', 'ⲥ': 'c', '𐐽': 'c', '𝑐': 'c', '𝒄': 'c', '𝒸': 'c', '𝓬': 'c', '𝔠': 'c', '𝕔': 'c', '𝖈': 'c', '𝗰': 'c', '𝘤': 'c', '𝙘': 'c', '𝚌': 'c', '𝓒': 'c', '𝕮': 'c', '𝖢': 'c', '𝗖': 'c', '𝘊': 'c', '𝙲': 'c', '𝒞': 'c', 'ℭ': 'c', '𝐂': 'c', '𝐶': 'c', '𝑪': 'c', 'ℂ': 'c', '𐊢': 'c', '𐌂': 'c', # Extends 'c' with various homoglyphs
      ',': ',', '،': ',', '፣': ',', '，': ',', '、': ',', '､': ',', ';': ',', ':': ',', '॰': ',', '᠂': ',', '᠈': ',', '、': ',', '︐': ',', '﹐': ',', '﹑': ',', '‚': ',', '，': ',', '、': ',', 'ꓹ': ',', '，': ',', '、': ',', '၊': ',', '⹁': ',', '、': ',', '︐': ',', '⁏': ',', '𐄁': ',' # Extends 'comma' with various homoglyphs
  }
  # Replace homoglyphs in the text
  for homoglyph, replacement in homoglyphs_replacements.items():
      cleaned_text = cleaned_text.replace(homoglyph, replacement)

  # Optional: Convert text to lower case for case-insensitive matching
  cleaned_text = cleaned_text.lower()

  # Return the normalized text
  return cleaned_text

async def handle_ban_command(update: Update, context: CallbackContext) -> bool:
  # Check if the message is a reply to another message
  if update.message.reply_to_message:
      # Load spam keywords from the file
      with open("spamkw.json", "r") as file:
          data = json.load(file)
          spam_keywords = data["spam_keywords"]

      # Normalize the text of the replied message
      replied_text = normalize_text(update.message.reply_to_message.text)

      # Check if the reply contains the '!ban' command
      if update.message.text.strip() == "!ban":
          # Check for any spam keyword in the replied message
          for keyword in spam_keywords:
              if keyword.lower() in replied_text:
                  # Get user_id from the replied message
                  user_id = update.message.reply_to_message.from_user.id
                  chat_id = update.message.chat.id
                  replied_message_id = update.message.reply_to_message.message_id
                  command_message_id = update.message.message_id

                  # Ban the user and delete the replied message
                  try:
                      await context.bot.ban_chat_member(chat_id, user_id)
                      await context.bot.delete_message(chat_id, replied_message_id)
                      # Send a confirmation message
                      confirmation_message = await context.bot.send_message(chat_id, "User banned and message deleted due to spam content.")
                      # Wait for 30 seconds
                      await asyncio.sleep(30)
                      # Delete the confirmation message and the command message
                      await context.bot.delete_message(chat_id, confirmation_message.message_id)
                      await context.bot.delete_message(chat_id, command_message_id)
                      return True
                  except Exception as e:
                      print(f"Failed to ban user or delete message: {e}")
                      return False
  return False

async def handle_potential_spam(update: Update, context: CallbackContext) -> bool:
# Load spam keywords from the JSON file
  with open("spamkw.json", "r") as file:
      data = json.load(file)
      spam_keywords = data["spam_keywords"]

  user_id = update.message.from_user.id
  username = update.message.from_user.username  # Get the username of the user
  chat_id = update.message.chat.id
  message_id = update.message.message_id 
  text = normalize_text(update.message.text)

  for keyword in spam_keywords:
      if keyword.lower() in text:
          try:
              await context.bot.ban_chat_member(chat_id, user_id)
              await context.bot.delete_message(chat_id, message_id)
              # Update the ban message to include the username
              ban_message = f"User @{username} has been banned for being a potential scammer."
              await context.bot.send_message(chat_id, ban_message)
              await context.bot.send_message(user_id, "If you think you're just banned by mistake, send a message to the admin @usernameisrick")
              return True
          except Exception as e:
              print(f"Failed to ban user, delete message or send private message: {e}")
              return False
  return False

def is_new_group_member(chat_id, user_id):
    """Check if a user is new member of the group."""
    is_new = user_id in new_group_members.get(chat_id, [])
    logging.info(f"Checking if user {user_id} is new in chat {chat_id}: {is_new}")
    return is_new

async def handle_new_user(update: Update, context: CallbackContext):
    logging.info("Handling new user")
    chat_id = update.message.chat.id
    new_users = update.message.new_chat_members
    logging.info(f"New users detected in chat {chat_id}: {[user.id for user in new_users]}")
    for user in new_users:
        if user.id not in new_group_members.get(chat_id, []):
            if chat_id not in new_group_members:
                new_group_members[chat_id] = []
            new_group_members[chat_id].append(user.id)
            logging.info(f"Added new user {user.id} to chat {chat_id}")

async def handle_forwarded_message(update: Update, context: CallbackContext) -> bool:
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    if update.message.forward_date and is_new_group_member(chat_id, user_id):
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.delete_message(chat_id, message_id)
            await context.bot.send_message(chat_id, "Banned a user for forwarding a message.")
            await context.bot.send_message(user_id, "If you think this was a mistake, contact admin.")
            new_group_members[chat_id].remove(user_id)
            logging.info(f"Banned and removed new user {user_id} from chat {chat_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to ban user {user_id} or delete message {message_id}: {e}")
            return False
    return False

ALLOWED_USERNAMES = ['usernameisrick', 'alloweduser2']  # Update this list with your actual usernames

async def handle_unauthorized_mention(update: Update, context: CallbackContext) -> bool:
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    username = update.message.from_user.username

    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention":
                mentioned_username = update.message.text[entity.offset:entity.offset+entity.length].strip("@")
                if mentioned_username not in ALLOWED_USERNAMES:
                    try:
                        await context.bot.ban_chat_member(chat_id, user_id)
                        await context.bot.delete_message(chat_id, message_id)
                        await context.bot.send_message(chat_id, f"User @{username} has been banned for being a potential scammer ⛔")
                        return True
                    except Exception as e:
                        print(f"Failed to ban user or delete message: {e}")
                        return False
    return False

ALLOWED_USERNAMES = ['usernameisrick', 'alloweduser2']  # Update this list with your actual usernames

async def handle_unauthorized_mention_with_image(update, context):
    # Extract chat and user information
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check if the user is an admin in the chat
    admin_status = await context.bot.get_chat_member(chat_id, user_id)
    if admin_status.status in ['administrator', 'creator']:
        return  # Do not process admins

    if update.message.photo and update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention":
                mentioned_username = update.message.text[entity.offset:entity.offset + entity.length].strip("@")
                if mentioned_username not in ALLOWED_USERNAMES:
                    message_id = update.message.message_id

                    # Delete the message
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

                    # Ban the user
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

                    # Notify the chat about the ban
                    ban_message = f"User @{username} has been banned for unauthorized mention with an image."
                    await context.bot.send_message(chat_id=chat_id, text=ban_message)

                    return  # Exit after handling






async def handle_ban_request(update: Update, context: CallbackContext):
  try:
      chat_id = update.effective_chat.id
      user_id = update.message.from_user.id
      original_message_id = update.message.message_id  # Store the original message id to delete it later
      logging.info(f"Handling ban request: {update.message.text}")

      # Check if the user is an admin of the group
      user = await context.bot.get_chat_member(chat_id, user_id)
      if user.status not in ['creator', 'administrator']:
          await update.message.reply_text("You must be an admin to use this command.")
          return

      # Extract username from the message
      message_text = update.message.text
      _, username = message_text.split()  # Assumes the message is "!ban @username"

      # Check if username is valid and remove '@' prefix
      if not username.startswith('@'):
          await update.message.reply_text("Please provide a valid username.")
          return
      username = username[1:]  # Remove '@'

      # Check if the username has interacted and is known
      known_user_id = context.bot_data.get('username_to_id_mapping', {}).get(username, None)
      if known_user_id is None:
          await update.message.reply_text(f"Could not ban {username}. They must have interacted in the chat before.")
          return

      # Attempt to ban the user by user ID
      try:
          await context.bot.ban_chat_member(chat_id, known_user_id)
          sent_message = await update.message.reply_text(f"{username} has been banned.")  # Store the sent message object
      except Exception as ban_error:
          logging.error(f"Error trying to ban: {ban_error}")
          await update.message.reply_text(f"Could not ban {username}. There might be another issue.")
          return

      # Wait for 30 seconds
      await asyncio.sleep(30)

      # Delete the original "!ban @username" message and the bot's response
      await context.bot.delete_message(chat_id, original_message_id)
      await context.bot.delete_message(chat_id, sent_message.message_id)

  except Exception as e:
      logging.error(f"Error in handle_ban_request: {e}")
      await update.message.reply_text("An error occurred while processing the ban request.")

async def handle_mute_request(update: Update, context: CallbackContext):
  try:
      chat_id = update.effective_chat.id
      user_id = update.message.from_user.id
      original_message_id = update.message.message_id
      logging.info(f"Handling mute request: {update.message.text}")

      # Check if the user is an admin of the group
      user = await context.bot.get_chat_member(chat_id, user_id)
      if user.status not in ['creator', 'administrator']:
          await update.message.reply_text("You must be an admin to use this command.")
          return

      # Extract username from the message
      message_text = update.message.text
      _, username = message_text.split()  # Assumes the message is "!mute @username"

      # Check if username is valid and remove '@' prefix
      if not username.startswith('@'):
          await update.message.reply_text("Please provide a valid username.")
          return
      username = username[1:]  # Remove '@'

      # Check if the username has interacted and is known
      known_user_id = context.bot_data.get('username_to_id_mapping', {}).get(username, None)
      if known_user_id is None:
          await update.message.reply_text(f"Could not mute {username}. They must have interacted in the chat before.")
          return

      # Attempt to mute the user by user ID
      try:
          # Adjust the permissions according to the API version you are using
          permissions = ChatPermissions(
              can_send_messages=False,
              can_send_polls=False,
              can_send_other_messages=False,
              can_add_web_page_previews=False,
              can_change_info=False,
              can_invite_users=False,
              can_pin_messages=False
          )
          await context.bot.restrict_chat_member(chat_id, known_user_id, permissions)
          sent_message = await update.message.reply_text(f"{username} has been muted.")  # Store the sent message object
      except Exception as mute_error:
          logging.error(f"Error trying to mute: {mute_error}")
          await update.message.reply_text(f"Could not mute {username}. There might be another issue.")
          return

      # Wait for 30 seconds
      await asyncio.sleep(30)

      # Delete the original "!mute @username" message and the bot's response
      await context.bot.delete_message(chat_id, original_message_id)
      await context.bot.delete_message(chat_id, sent_message.message_id)

  except Exception as e:
      logging.error(f"Error in handle_mute_request: {e}")
      await update.message.reply_text("An error occurred while processing the mute request.")

async def handle_unmute_request(update: Update, context: CallbackContext):
  try:
      chat_id = update.effective_chat.id
      user_id = update.message.from_user.id
      original_message_id = update.message.message_id
      logging.info(f"Handling unmute request: {update.message.text}")

      # Check if the user is an admin of the group
      user = await context.bot.get_chat_member(chat_id, user_id)
      if user.status not in ['creator', 'administrator']:
          await update.message.reply_text("You must be an admin to use this command.")
          return

      # Extract username from the message
      message_text = update.message.text
      _, username = message_text.split()  # Assumes the message is "!unmute @username"

      # Check if username is valid and remove '@' prefix
      if not username.startswith('@'):
          await update.message.reply_text("Please provide a valid username.")
          return
      username = username[1:]  # Remove '@'

      # Check if the username has interacted and is known
      known_user_id = context.bot_data.get('username_to_id_mapping', {}).get(username, None)
      if known_user_id is None:
          await update.message.reply_text(f"Could not unmute {username}. They must have interacted in the chat before.")
          return

      # Attempt to unmute the user by user ID
      try:
          permissions = ChatPermissions(
              can_send_messages=True,
              can_send_polls=True,
              can_send_other_messages=True,
              can_add_web_page_previews=True,
              can_change_info=None,
              can_invite_users=None,
              can_pin_messages=None
          )
          await context.bot.restrict_chat_member(chat_id, known_user_id, permissions)
          sent_message = await update.message.reply_text(f"{username} has been unmuted.")
      except Exception as unmute_error:
          logging.error(f"Error trying to unmute: {unmute_error}")
          await update.message.reply_text(f"Could not unmute {username}. There might be another issue.")
          return

      # Wait for 30 seconds
      await asyncio.sleep(30)

      # Delete the original "!unmute @username" message and the bot's response
      await context.bot.delete_message(chat_id, original_message_id)
      await context.bot.delete_message(chat_id, sent_message.message_id)

  except Exception as e:
      logging.error(f"Error in handle_unmute_request: {e}")
      await update.message.reply_text("An error occurred while processing the unmute request.")

allowed_channels_usernames = ['botbuddyannouncements']

async def check_and_ban_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Define the characters and patterns to look for
  rtl_chars = ['\u200F', '\u200E', '\u202B', '\u202E', '\u202C', '\u202A', '\u202D', '\u2066', '\u2067', '\u2068', '\u2069', '\u0591', '\u0592', '\u0593', '\u0594', '\u0595', '\u0596', '\u0597', '\u0598', '\u0599', '\u059A', '\u059B', '\u059C', '\u059D', '\u059E', '\u059F', '\u05A0', '\u05A1', '\u05A2', '\u05A3', '\u05A4', '\u05A5', '\u05A6', '\u05A7', '\u05A8', '\u05A9', '\u05AA', '\u05AB', '\u05AC', '\u05AD', '\u05AE', '\u05AF', '\u05C0', '\u05C3', '\u05C6', '\u0600', '\u0601', '\u0602', '\u0603', '\u0604', '\u0605', '\u0606', '\u0607', '\u0608', '\u0609', '\u060A', '\u060B', '\u060D', '\u0610', '\u0611', '\u0612', '\u0613', '\u0614', '\u0615', '\u0616', '\u0617', '\u0618', '\u0619', '\u061A', '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650', '\u0651', '\u0652', '\u0653', '\u0654', '\u0655', '\u0656', '\u0657', '\u0658', '\u0659', '\u065A', '\u065B', '\u065C', '\u065D', '\u065E', '\u065F', '\u0660', '\u0661', '\u0662', '\u0663', '\u0664', '\u0665', '\u0666', '\u0667', '\u0668', '\u0669', '\u06DD', '\u070F']
  # Define homoglyph patterns for specific scam-related words
  homoglyphs_patterns = [
    # Adidas variations with common homoglyphs for 'a', 'd', 'i', and 's'.
    'Ad[iіᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]d[aаɑαааᴀᴀạặảấầẩẫậắằẳẵặₐḀḁἀἁἂἃἄἅἆἇἈἉἊἋἌἍἎἏᾀᾁᾂᾃᾄᾅᾆᾇᾈᾉᾊᾋᾌᾍᾎᾏАΑαа]',  # Extends 'a' with various homoglyphs
    '11[,،፣，、､;:॰᠂᠈︐﹐﹑‚ꓹ၊⹁⁏𐄁]111',  # Extends comma with various homoglyphs

    # Nibiru variations - as an example, showing 'i' replacement. 
    'N[iіᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]b[iіᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]ru',

    # Crypto Whale variations - starting with 'c' and 'o', expand similarly for other letters.
    '[cсϲćĉčċçȼ¢ҫꜿↄⲥ𐐽𝑐𝒄𝒸𝓬𝔠𝕔𝖈𝗰𝘤𝙘𝚌𝓒𝕮𝖢𝗖𝘊𝙲𝒞ℭ𝐂𝐶𝑪ℂ𐊢𐌂]rypt[oоοόѻӦӧӨөӪọỏốồổỗộớờởỡợöőõôơǒǿȯȱȫȭǫǭɵɔѳѲԉԓᴏᴑᴓᴼｏＯⲞⲟ] wh[aаɑαааᴀᴀạặảấầẩẫậắằẳẵặₐḀḁἀἁἂἃἄἅἆἇἈἉἊἋἌἍἎἏᾀᾁᾂᾃᾄᾅᾆᾇᾈᾉᾊᾋᾌᾍᾎᾏАΑαа]le',

    # Cutt.ly variations - starting with 'c' and 'u', then dot obfuscation.
    'https://[cсϲćĉčċçȼ¢ҫꜿↄⲥ𐐽𝑐𝒄𝒸𝓬𝔠𝕔𝖈𝗰𝘤𝙘𝚌𝓒𝕮𝖢𝗖𝘊𝙲𝒞ℭ𝐂𝐶𝑪ℂ𐊢𐌂]utt[.]ly',  # Start with common link obfuscation by replacing dot

    # MND Airdrop variations - starting with 'M' and 'N', expand similarly.
    'M[NПпṅṇṈṉṊṋṆṈṊńňñņŋƞɲɳȵŉᵰᶇɴήηνиийңҥԉԓոռነኔንኖᑎᑏᑥᴎᴨᴺᵰᶇｎＮ]D A[iіᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]rdr[oоοόѻӦӧӨөӪọỏốồổỗộớờởỡợöőõôơǒǿȯȱȫȭǫǭɵɔѳѲԉԓᴏᴑᴓᴼｏＯⲞⲟ]p'
  ]

  # Look out for invisible characters
  invisible_chars = ['\u200B', '\u200C', '\u200E', '\u200F', '\u202A', '\u202B', '\u202C', '\u202D', '\u202E', '\u2060', '\u2061', '\u2062', '\u2063', '\u2064', '\uFEFF', '\uFFF9', '\uFFFA', '\uFFFB', '\u034F', '\u061C', '\u115F', '\u1160', '\u17B4', '\u17B5', '\u180B', '\u180C', '\u180D', '\u180E', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A', '\u2028', '\u2029', '\u205F', '\u3000', '\u3164', '\uFFA0', '\u00AD', '\uDB40\uDC00', '\uDB40\uDC01', '\uDB40\uDC02', '\uDB40\uDC03', '\uDB40\uDC04', '\uDB40\uDC05', '\uDB40\uDC06', '\uDB40\uDC07', '\uDB40\uDC08', '\uDB40\uDC09', '\uDB40\uDC0A', '\uDB40\uDC0B', '\uDB40\uDC0C', '\uDB40\uDC0D', '\uDB40\uDC0E', '\uDB40\uDC0F', '\uDB40\uDC10', '\uDB40\uDC11', '\uDB40\uDC12', '\uDB40\uDC13', '\uDB40\uDC14', '\uDB40\uDC15', '\uDB40\uDC16', '\uDB40\uDC17', '\uDB40\uDC18', '\uDB40\uDC19', '\uDB40\uDC1A', '\uDB40\uDC1B', '\uDB40\uDC1C', '\uDB40\uDC1D', '\uDB40\uDC1E', '\uDB40\uDC1F', '\uDB40\uDC20', '\uDB40\uDC21', '\uDB40\uDC22', '\uDB40\uDC23', '\uDB40\uDC24', '\uDB40\uDC25', '\uDB40\uDC26', '\uDB40\uDC27', '\uDB40\uDC28', '\uDB40\uDC29', '\uDB40\uDC2A', '\uDB40\uDC2B', '\uDB40\uDC2C', '\uDB40\uDC2D', '\uDB40\uDC2E', '\uDB40\uDC2F', '\uDB40\uDC30', '\uDB40\uDC31', '\uDB40\uDC32', '\uDB40\uDC33', '\uDB40\uDC34', '\uDB40\uDC35', '\uDB40\uDC36', '\uDB40\uDC37', '\uDB40\uDC38', '\uDB40\uDC39', '\uDB40\uDC3A', '\uDB40\uDC3B', '\uDB40\uDC3C', '\uDB40\uDC3D', '\uDB40\uDC3E', '\uDB40\uDC3F', '\uDB40\uDC40', '\uDB40\uDC41', '\uDB40\uDC42', '\uDB40\uDC43', '\uDB40\uDC44', '\uDB40\uDC45', '\uDB40\uDC46', '\uDB40\uDC47', '\uDB40\uDC48', '\uDB40\uDC49', '\uDB40\uDC4A', '\uDB40\uDC4B', '\uDB40\uDC4C', '\uDB40\uDC4D', '\uDB40\uDC4E', '\uDB40\uDC4F', '\uDB40\uDC50', '\uDB40\uDC51', '\uDB40\uDC52', '\uDB40\uDC53', '\uDB40\uDC54', '\uDB40\uDC55', '\uDB40\uDC56', '\uDB40\uDC57', '\uDB40\uDC58', '\uDB40\uDC59', '\uDB40\uDC5A', '\uDB40\uDC5B', '\uDB40\uDC5C', '\uDB40\uDC5D', '\uDB40\uDC5E', '\uDB40\uDC5F', '\uDB40\uDC60', '\uDB40\uDC61', '\uDB40\uDC62', '\uDB40\uDC63', '\uDB40\uDC64', '\uDB40\uDC65', '\uDB40\uDC66', '\uDB40\uDC67', '\uDB40\uDC68', '\uDB40\uDC69', '\uDB40\uDC6A', '\uDB40\uDC6B', '\uDB40\uDC6C', '\uDB40\uDC6D', '\uDB40\uDC6E', '\uDB40\uDC6F', '\uDB40\uDC70', '\uDB40\uDC71', '\uDB40\uDC72', '\uDB40\uDC73', '\uDB40\uDC74', '\uDB40\uDC75', '\uDB40\uDC76', '\uDB40\uDC77', '\uDB40\uDC78', '\uDB40\uDC79', '\uDB40\uDC7A', '\uDB40\uDC7B', '\uDB40\uDC7C', '\uDB40\uDC7D', '\uDB40\uDC7E', '\uDB40\uDC7F']
  # Combine all characters into a single pattern
  combined_pattern = f"[{''.join(rtl_chars + invisible_chars)}]|" + '|'.join(homoglyphs_patterns)

  # Check if the message is forwarded from a channel and if it's from an allowed channel
  sender_chat_username = update.message.sender_chat.username.lower() if update.message.sender_chat else ""
  if "@" + sender_chat_username in allowed_channels_usernames:
      # Message is from an allowed channel, skip spam check
      return False

  user_id = update.message.from_user.id
  username = update.message.from_user.username
  chat_id = update.effective_chat.id
  message_text = update.message.text

  # Check if the message matches the combined pattern
  if re.search(combined_pattern, message_text, re.IGNORECASE):
      # Ban the user and delete the message
      await context.bot.ban_chat_member(chat_id, user_id)
      await context.bot.delete_message(chat_id, update.message.message_id)
      ban_message = f"User @{username} has been banned for sending potential spam 😤"
      # Send a confirmation message to the group
      await context.bot.send_message(chat_id, ban_message)
      return True  # Indicates that a spam message was detected and handled
  return False  # Indicates that no spam was detected in the message

ALLOWED_CHANNELS = [
 'https://t.me/BotBuddyAnnouncements'
]

async def handle_channel_messages(update: Update, context: CallbackContext):
  # Check if the message is from a channel
  if update.message.sender_chat and update.message.sender_chat.type == 'channel':
      # Construct the channel's URL
      channel_url = f"https://t.me/{update.message.sender_chat.username}"

      # Check if the channel is not in the allowed list
      if channel_url not in ALLOWED_CHANNELS:
          # If the bot has the permissions, delete the message
          try:
              await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
              print(f"Deleted message from unauthorized channel: {channel_url}")
          except Exception as e:
              print(f"Failed to delete message: {e}")
      else:
          print(f"Message from allowed channel: {channel_url}")

allowed_channels_usernames = ['botbuddyannouncements']

async def check_and_ban_forwarded_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
  rtl_chars = ['\u200F', '\u200E', '\u202B', '\u202E', '\u202C', '\u202A', '\u202D', '\u2066', '\u2067', '\u2068', '\u2069', '\u0591', '\u0592', '\u0593', '\u0594', '\u0595', '\u0596', '\u0597', '\u0598', '\u0599', '\u059A', '\u059B', '\u059C', '\u059D', '\u059E', '\u059F', '\u05A0', '\u05A1', '\u05A2', '\u05A3', '\u05A4', '\u05A5', '\u05A6', '\u05A7', '\u05A8', '\u05A9', '\u05AA', '\u05AB', '\u05AC', '\u05AD', '\u05AE', '\u05AF', '\u05C0', '\u05C3', '\u05C6', '\u0600', '\u0601', '\u0602', '\u0603', '\u0604', '\u0605', '\u0606', '\u0607', '\u0608', '\u0609', '\u060A', '\u060B', '\u060D', '\u0610', '\u0611', '\u0612', '\u0613', '\u0614', '\u0615', '\u0616', '\u0617', '\u0618', '\u0619', '\u061A', '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650', '\u0651', '\u0652', '\u0653', '\u0654', '\u0655', '\u0656', '\u0657', '\u0658', '\u0659', '\u065A', '\u065B', '\u065C', '\u065D', '\u065E', '\u065F', '\u0660', '\u0661', '\u0662', '\u0663', '\u0664', '\u0665', '\u0666', '\u0667', '\u0668', '\u0669', '\u06DD', '\u070F']
  homoglyphs_patterns = ['Ad[іᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]d[аɑαааᴀᴀạặảấầẩẫậắằẳẵặₐḀḁἀἁἂἃἄἅἆἇἈἉἊἋἌἍἎἏᾀᾁᾂᾃᾄᾅᾆᾇᾈᾉᾊᾋᾌᾍᾎᾏАΑαа]', '11[،፣，、､;:॰᠂᠈︐﹐﹑‚ꓹ၊⹁⁏𐄁]111', 'N[іᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]b[іᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]ru', '[сϲćĉčċçȼ¢ҫꜿↄⲥ𐐽𝑐𝒄𝒸𝓬𝔠𝕔𝖈𝗰𝘤𝙘𝚌𝓒𝕮𝖢𝗖𝘊𝙲𝒞ℭ𝐂𝐶𝑪ℂ𐊢𐌂]rypt[оοόѻӦӧӨөӪọỏốồổỗộớờởỡợöőõôơǒǿȯȱȫȭǫǭɵɔѳѲԉԓᴏᴑᴓᴼｏＯⲞⲟ] wh[аɑαааᴀᴀạặảấầẩẫậắằẳẵặₐḀḁἀἁἂἃἄἅἆἇἈἉἊἋἌἍἎἏᾀᾁᾂᾃᾄᾅᾆᾇᾈᾉᾊᾋᾌᾍᾎᾏАΑαа]le', 'https://[сϲćĉčċçȼ¢ҫꜿↄⲥ𐐽𝑐𝒄𝒸𝓬𝔠𝕔𝖈𝗰𝘤𝙘𝚌𝓒𝕮𝖢𝗖𝘊𝙲𝒞ℭ𝐂𝐶𝑪ℂ𐊢𐌂]utt[.]ly', 'M[ПпṅṇṈṉṊṋṆṈṊńňñņŋƞɲɳȵŉᵰᶇɴήηνиийңҥԉԓոռነኔንኖᑎᑏᑥᴎᴨᴺᵰᶇｎＮ]D A[іᎥ᎐᎑ıíìîïįĩīĭÌÍÎÏиіїǐỉȉȋịḭḯἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗіӏᴉᵢⁱℹⅈﬁﬃ]rdr[оοόѻӦӧӨөӪọỏốồổỗộớờởỡợöőõôơǒǿȯȱȫȭǫǭɵɔѳѲԉԓᴏᴑᴓᴼｏＯⲞⲟ]p']
  invisible_chars = ['\u200B', '\u200C', '\u200E', '\u200F', '\u202A', '\u202B', '\u202C', '\u202D', '\u202E', '\u2060', '\u2061', '\u2062', '\u2063', '\u2064', '\uFEFF', '\uFFF9', '\uFFFA', '\uFFFB', '\u034F', '\u061C', '\u115F', '\u1160', '\u17B4', '\u17B5', '\u180B', '\u180C', '\u180D', '\u180E', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A', '\u2028', '\u2029', '\u205F', '\u3000', '\u3164', '\uFFA0', '\u00AD', '\uDB40\uDC00', '\uDB40\uDC01', '\uDB40\uDC02', '\uDB40\uDC03', '\uDB40\uDC04', '\uDB40\uDC05', '\uDB40\uDC06', '\uDB40\uDC07', '\uDB40\uDC08', '\uDB40\uDC09', '\uDB40\uDC0A', '\uDB40\uDC0B', '\uDB40\uDC0C', '\uDB40\uDC0D', '\uDB40\uDC0E', '\uDB40\uDC0F', '\uDB40\uDC10', '\uDB40\uDC11', '\uDB40\uDC12', '\uDB40\uDC13', '\uDB40\uDC14', '\uDB40\uDC15', '\uDB40\uDC16', '\uDB40\uDC17', '\uDB40\uDC18', '\uDB40\uDC19', '\uDB40\uDC1A', '\uDB40\uDC1B', '\uDB40\uDC1C', '\uDB40\uDC1D', '\uDB40\uDC1E', '\uDB40\uDC1F', '\uDB40\uDC20', '\uDB40\uDC21', '\uDB40\uDC22', '\uDB40\uDC23', '\uDB40\uDC24', '\uDB40\uDC25', '\uDB40\uDC26', '\uDB40\uDC27', '\uDB40\uDC28', '\uDB40\uDC29', '\uDB40\uDC2A', '\uDB40\uDC2B', '\uDB40\uDC2C', '\uDB40\uDC2D', '\uDB40\uDC2E', '\uDB40\uDC2F', '\uDB40\uDC30', '\uDB40\uDC31', '\uDB40\uDC32', '\uDB40\uDC33', '\uDB40\uDC34', '\uDB40\uDC35', '\uDB40\uDC36', '\uDB40\uDC37', '\uDB40\uDC38', '\uDB40\uDC39', '\uDB40\uDC3A', '\uDB40\uDC3B', '\uDB40\uDC3C', '\uDB40\uDC3D', '\uDB40\uDC3E', '\uDB40\uDC3F', '\uDB40\uDC40', '\uDB40\uDC41', '\uDB40\uDC42', '\uDB40\uDC43', '\uDB40\uDC44', '\uDB40\uDC45', '\uDB40\uDC46', '\uDB40\uDC47', '\uDB40\uDC48', '\uDB40\uDC49', '\uDB40\uDC4A', '\uDB40\uDC4B', '\uDB40\uDC4C', '\uDB40\uDC4D', '\uDB40\uDC4E', '\uDB40\uDC4F', '\uDB40\uDC50', '\uDB40\uDC51', '\uDB40\uDC52', '\uDB40\uDC53', '\uDB40\uDC54', '\uDB40\uDC55', '\uDB40\uDC56', '\uDB40\uDC57', '\uDB40\uDC58', '\uDB40\uDC59', '\uDB40\uDC5A', '\uDB40\uDC5B', '\uDB40\uDC5C', '\uDB40\uDC5D', '\uDB40\uDC5E', '\uDB40\uDC5F', '\uDB40\uDC60', '\uDB40\uDC61', '\uDB40\uDC62', '\uDB40\uDC63', '\uDB40\uDC64', '\uDB40\uDC65', '\uDB40\uDC66', '\uDB40\uDC67', '\uDB40\uDC68', '\uDB40\uDC69', '\uDB40\uDC6A', '\uDB40\uDC6B', '\uDB40\uDC6C', '\uDB40\uDC6D', '\uDB40\uDC6E', '\uDB40\uDC6F', '\uDB40\uDC70', '\uDB40\uDC71', '\uDB40\uDC72', '\uDB40\uDC73', '\uDB40\uDC74', '\uDB40\uDC75', '\uDB40\uDC76', '\uDB40\uDC77', '\uDB40\uDC78', '\uDB40\uDC79', '\uDB40\uDC7A', '\uDB40\uDC7B', '\uDB40\uDC7C', '\uDB40\uDC7D', '\uDB40\uDC7E', '\uDB40\uDC7F']
  combined_pattern = f"[{''.join(rtl_chars + invisible_chars)}]|" + '|'.join(homoglyphs_patterns)

  # Check if the message is forwarded from a channel and if it's from an allowed channel
  sender_chat_username = update.message.sender_chat.username.lower() if update.message.sender_chat else ""
  if "@" + sender_chat_username in allowed_channels_usernames:
      # Message is from an allowed channel, skip spam check
      return False

  user_id = update.message.from_user.id
  username = update.message.from_user.username
  chat_id = update.effective_chat.id
  # Check if the message is forwarded and set the text to check accordingly
  if update.message.forward_from or update.message.forward_from_chat:
      message_text = update.message.text  # Use the text of the forwarded message
  else:
      return False  # Skip checking if the message is not forwarded

  if re.search(combined_pattern, message_text, re.IGNORECASE):
      await context.bot.ban_chat_member(chat_id, user_id)
      await context.bot.delete_message(chat_id, update.message.message_id)
      ban_message = f"User @{username} has been banned for sending potential spam 😤"
      # Send a confirmation message to the group
      await context.bot.send_message(chat_id, ban_message)
      return True  
  return False

# Regular expression to match most emojis
emoji_pattern = re.compile("["
                         u"\U0001F600-\U0001F64F"  # emoticons
                         u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                         u"\U0001F680-\U0001F6FF"  # transport & map symbols
                         u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                         u"\U0001F700-\U0001F77F"  # alchemical symbols
                         u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                         u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                         u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                         u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                         u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                         u"\U00002702-\U000027B0"  # Dingbats
                         u"\U0001F910-\U0001F93A"  # Face Emotion
                         u"\U0001F93C-\U0001F945"  # Sport Symbols
                         u"\U0001F947-\U0001F9FF"  # Medals and other Sport Symbols
                         u"\U00002300-\U000023FF"  # Miscellaneous Technical
                         u"\U000024C2-\U0001F251"  # Enclosed characters
                         u"\U00002500-\U000027BF"  # Various symbols
                         u"\U00002B50-\U00002B55"  # More symbols
                         u"\U0001F004-\U0001F0CF"  # Mahjong tiles and playing cards
                         u"\U0001F0D0-\U0001F0FF"  # More game pieces
                         u"\U0001F201-\U0001F2FF"  # Enclosed characters with squares
                         u"\U0001F300-\U0001F5FF"  # Various pictographs
                         u"\U0001F650-\U0001F67F"  # Ornamental Dingbats
                         u"\U0001F680-\U0001F6FF"  # Transport and maps
                         u"\U0001F700-\U0001F77F"  # Alchemical symbols
                         u"\U0001F780-\U0001F7FF"  # Geometric shapes extended
                         u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                         u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                         u"\U0001FA00-\U0001FA6F"  # Chess symbols
                         u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                         u"\U00002600-\U000026FF"  # Miscellaneous Symbols
                         u"\U00002700-\U000027BF"  # Dingbats
                         u"\U0001F1E6-\U0001F1FF"  # Regional indicator symbols
                         u"\U0001F191-\U0001F19A"  # Squared symbols
                         u"\U0001F3FB-\U0001F3FF"  # Skin tone modifiers
                         u"\U0001F9D0-\U0001F9E6"  # Supplemental Faces and People Symbols
                         u"\U0001FAC0-\U0001FAC5"  # Health workers & people hugging (added in 2020)
                         u"\U0001FAF0-\U0001FAF6"  # Musical instruments (added in 2020)
                         u"\U0001F32D-\U0001F32F"  # Food items (hot dog, taco, burrito)
                         u"\U0001FAD0-\U0001FAD9"  # Additional food items (added in 2021)
                         "]+", flags=re.UNICODE)

# List of allowed channel usernames (without '@')
allowed_channels = ['botbuddyannouncements', 'raidarrobot', 'bobbybuybot']

# List of user usernames exempt from the ban (without '@')
exempt_users = ['bla', 'bla1']

async def handle_emoji_spam(update, context):
  # Extract sender chat (for messages forwarded from channels)
  sender_chat = update.message.sender_chat

  # Check if the message is forwarded from a channel and if it's from an allowed channel
  if sender_chat and sender_chat.username and sender_chat.username.lower() in (channel.lower() for channel in allowed_channels):

      # Message is from an allowed channel, so don't proceed with spam handling
      return False

  user_id = update.message.from_user.id
  username = update.message.from_user.username
  chat_id = update.effective_chat.id
  message_id = update.message.message_id
  text = update.message.text

  # Check if the user is in the exempt list
  if username and username.lower() in [user.lower() for user in exempt_users]:
      # User is exempt, so don't proceed with spam handling
      return False

  emojis = re.findall(emoji_pattern, text)
  unique_emojis = set(emojis)

  if len(unique_emojis) >= 3:
      try:
          await context.bot.ban_chat_member(chat_id, user_id)
          await context.bot.delete_message(chat_id, message_id)
          confirmation_message = f"User @{username} has been banned for being a potential scammer 😈"
          await context.bot.send_message(chat_id, confirmation_message)
          return True
      except Exception as e:
          logging.error(f"Failed to ban user or delete message: {e}")
  return False

# List of allowed channel usernames (without '@')
allowed_channels = ['botbuddyannouncements']

async def handle_gif_and_ban(update, context):
  # Extract sender chat (for messages forwarded from channels)
  sender_chat = update.message.sender_chat

  # Convert allowed channel names to lowercase for case insensitive comparison
  allowed_channels_lower = [channel.lower() for channel in allowed_channels]

  # Check if the message is forwarded from a channel and if it's from an allowed channel
  if sender_chat and sender_chat.username and sender_chat.username.lower() in allowed_channels_lower:
      # Message is from an allowed channel, so don't proceed with banning or deleting
      return

  # Check if the message contains a GIF and text longer than 20 characters
  if update.message.animation and update.message.caption and len(update.message.caption) > 10:
      user_id = update.message.from_user.id
      username = update.message.from_user.username  # Get the username of the user
      chat_id = update.message.chat.id
      message_id = update.message.message_id

      # Delete the message
      await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

      # Ban the user
      await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

      # Send a message to the chat about the ban including the username
      ban_message = f"User @{username} has been banned for being a potential scammer 🗿"
      await context.bot.send_message(chat_id=chat_id, text=ban_message)

      # Log the action (replace print with logging if you've set it up)
      print(f"Banned user @{username} (ID: {user_id}) for sending a GIF with a long message that might be a scam.")

# List of allowed channel usernames (without '@')
allowed_channels = ['botbuddyannouncements']

# List of user usernames exempt from the ban (without '@')
exempt_users = ['bla']

async def handle_image_and_ban(update, context):
  # Extract sender chat (for messages forwarded from channels)
  sender_chat = update.message.sender_chat

  # Check if the message is forwarded from a channel and if it's from an allowed channel
  if sender_chat and sender_chat.username and any(sender_chat.username.lower() == channel.lower() for channel in allowed_channels):
      # Message is from an allowed channel, so don't proceed with banning or deleting
      return

  # Extract chat and user IDs
  chat_id = update.message.chat.id
  user_id = update.message.from_user.id
  username = update.message.from_user.username

  # Check if the user is exempt
  if username and any(username.lower() == user.lower() for user in exempt_users):
      # The user is exempt, do not delete the message or ban the user
      return

  # Check if the user is an admin in the chat
  admin_status = await context.bot.get_chat_member(chat_id, user_id)
  if admin_status.status in ['administrator', 'creator']:
      # The user is an admin, do not delete the message or ban the user
      return

  # Check if the message contains an image, has a caption longer than 20 characters, and contains a URL
  if update.message.photo and update.message.caption:
      caption = update.message.caption
      if len(caption) > 140 and any(keyword in caption for keyword in ["https://", "www", "VIP", "molti profitti", "http://", ".site", "Yacht"]):
          message_id = update.message.message_id

          # Delete the message
          await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

          # Ban the user
          await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

          # Send a message to the chat about the ban including the username
          ban_message = f"User @{username} has been banned for sending a scamming image."
          await context.bot.send_message(chat_id=chat_id, text=ban_message)

          # Log the action
          logging.info(f"Banned user @{username} (ID: {user_id}) for sending an image with a URL in the caption.")

async def handle_forwarded_bot_message(update, context):
    message = update.message
    if message.forward_from and message.forward_from.is_bot:
        if message.reply_markup:  # Check if there are buttons in the message
            await message.delete()
            await context.bot.ban_chat_member(chat_id=message.chat_id, user_id=message.from_user.id)
            username = message.from_user.username
            ban_message = f"User @{username} has been banned for being a potential scammer 🤖"
            await context.bot.send_message(chat_id=message.chat_id, text=ban_message)
            logging.info(f"Banned user {username} for forwarding bot message with buttons.")
            return True
    return False

