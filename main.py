from typing import Final
import os
import logging
from telegram import Update
import telegram
from telegram.ext import ApplicationBuilder, filters, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, CallbackContext, ChatMemberHandler
from telegram.ext.filters import ChatType
from langchain_community.vectorstores import Qdrant
from langchain_openai.embeddings import OpenAIEmbeddings
import qdrant_client
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from langdetect import detect
from functions import check_for_admin_request, filter_ai_sentences, is_user_admin, is_special_user, get_crypto_market_cap, get_crypto_price_info, handle_leaving_user, check_user_message_limit, check_for_developer_request, check_for_proposal, check_for_airdrop_request, check_for_dump_request, handle_roadmap_request, handle_roadmap_mention_request, append_campaign, append_how_to_buy, append_proposal, handle_tokenomics_request, handle_tokenomics_mention_request, handle_price_request, handle_price_mention_request, handle_affiliate_request, handle_affiliate_mention_request
from functions_ban import handle_ban_command, handle_potential_spam, handle_new_user, handle_forwarded_message, handle_ban_request, handle_mute_request, handle_unmute_request, check_and_ban_spam, handle_channel_messages, check_and_ban_forwarded_spam, handle_emoji_spam, handle_gif_and_ban, handle_image_and_ban, handle_unauthorized_mention, is_new_group_member, handle_unauthorized_mention_with_image, handle_forwarded_bot_message
from functions_panel import handle_setup_request, handle_menu_callback, handle_new_spam_keyword, handle_remove_spam_keyword, handle_new_faq_question, handle_new_faq_answer, get_chunks, handle_remove_faq_question, spamkw_list
import json
import asyncio

# Environment variables are set for Qdrant and OpenAI
os.environ['QDRANT_HOST'] = os.getenv("QDRANT_HOST")
os.environ['QDRANT_API_KEY'] = os.getenv("QDRANT_API_KEY")
os.environ['QDRANT_COLLECTION'] = os.getenv("QDRANT_COLLECTION")
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

# Telegram bot token and username
TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")

# Basic logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

bot_active = True

# Global cache for recent questions (currently unused)
recent_questions = {}
MAX_QUESTIONS = 10
username_to_id_mapping = {}

embeddings = OpenAIEmbeddings()

# Initialize Qdrant client and set up the collection
client = qdrant_client.QdrantClient(os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
collection_config = qdrant_client.http.models.VectorParams(size=1536, distance=qdrant_client.http.models.Distance.COSINE)
client.recreate_collection(collection_name=os.getenv("QDRANT_COLLECTION"), vectors_config=collection_config)

# Create a vector store for embeddings
vectorstore = Qdrant(client=client, collection_name=os.getenv("QDRANT_COLLECTION"), embeddings=embeddings)

# Function to split a text into chunks of Q&A pairs
def get_chunks(text):
    separator = "\n\n"
    qna_pairs = text.split(separator)
    chunks = [pair for pair in qna_pairs if pair]
    return chunks

# Read and process a text file into chunks for the vector store
with open("botbuddy.txt") as f:
    raw_text = f.read()
texts = get_chunks(raw_text)
vectorstore.add_texts(texts)

# Instantiate the ChatOpenAI object with the gpt-4-turbo-preview model
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# Use this llm object when setting up the RetrievalQA
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())

# Define your list of keywords
KEYWORDS = [
    "BotBuddy", "Bot Buddy", "Co-founder", "CEO", "CTO", "Solidity", "Developer", "Advisor", "Web3", "Community Assistant", "Website AI Widget", "Telegram", "Discord", "tokenomics", "TGE", "$BOT", "Control Panel", "Coingecko", "spam", "security", "multi-language", "bot points", "Airdrop", "Galxe", "cold emailing", "KOL", "campaign", "Centralized Exchanges", "CEX", "blockchain integrations", "AI Software House", "Trading Bot", "DAO", "DeFi", "dApp", "GameFi", "Web2", "SME", "docs", "Medium", "Announcements", "Twitter", "LinkedIn", "email", "roadmap", "DEX", "Affiliate", "Affiliate Program"
]

# Global dictionary to track the number of messages per user
user_messages_count = {}

# Function to check if any keyword is in the text
def contains_keyword(text):
    return any(keyword.lower() in text.lower() for keyword in KEYWORDS)

# Function to handle queries using the QA chain
def handle_query(query):
    # Convert query to lower case for case-insensitive comparison
    query_lower = query.lower()

    # Check if the query contains any of the keywords
    if not contains_keyword(query):
        return None, False

    # Proceed with the existing process
    result = qa.invoke(query)
    response_text = result.get('result', None)

    if response_text:
        response_text_lower = response_text.lower()

        # Generate embeddings for the query and the response
        query_embedding = embeddings.embed_query(query_lower)
        response_embedding = embeddings.embed_query(response_text_lower)

        # Filter out sentences containing 'I am an AI' or 'I'm an AI'
        filtered_response_text = filter_ai_sentences(response_text)

        # Calculate cosine similarity using the filtered response text
        similarity = cosine_similarity([query_embedding], [embeddings.embed_query(filtered_response_text.lower())])[0][0]

        # Check for keywords in the query or response
        if contains_keyword(query) or contains_keyword(filtered_response_text):
            # Check if the similarity is above a certain threshold
            if similarity > 0.85:  # Threshold value, adjust based on testing
                # Append OTC link if needed
                filtered_response_text = append_campaign(query, filtered_response_text)
                # Append how to buy link if needed
                filtered_response_text = append_how_to_buy(query, filtered_response_text)
                # Append proposal email if needed
                filtered_response_text = append_proposal(query, filtered_response_text)
                return filtered_response_text, True
            else:
                return filtered_response_text, False
        else:
            return None, False

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm Leo, the BotBuddy Community Assistant. Ask me whatever you want regarding BotBuddy and the upcoming token $BOT.")

# Setup command handler
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("This command can only be used in group chats where I'm an admin.")
        return
    await handle_setup_request(update, context)

    # Wait for 5 seconds
    await asyncio.sleep(5)

    # Delete the "/setup" message
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, 
                                         message_id=update.message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def query(update: Update, context: CallbackContext):
  try:
      # Check if the update contains a message
      if update.message is None:
          logging.info("Update does not contain a message.")
          return

      user_id = update.message.from_user.id
      username = update.message.from_user.username
      user_input = update.message.text
      chat_id = update.effective_chat.id
            
      # Check if the message is from a private chat
      if chat_id == user_id:
          over_limit = check_user_message_limit(user_id)
          if over_limit:
              await update.message.reply_text("You have reached the maximum number of messages allowed in 24 hours.")
              return  # Stop processing this message
      message_id = update.message.message_id
      logging.info(f"Received message: {user_input}")

      # Store the username and user ID mapping
      if username:  # Ensure username is not None
          context.bot_data.setdefault('username_to_id_mapping', {})[username] = user_id

      # Check if the bot is in FAQ addition mode for this user in a private chat
      if chat_id == user_id:  # This checks if the chat is a private chat
          if context.bot_data.get(f'awaiting_faq_question_{user_id}', False):
              await handle_new_faq_question(update, context)
              return  # Stop further processing

          if context.bot_data.get(f'awaiting_faq_answer_{user_id}', False):
              await handle_new_faq_answer(update, context, client, collection_config, vectorstore)
              return  # Stop further processing

      if chat_id == user_id:  # This checks if the chat is a private chat
          if context.bot_data.get(f'awaiting_faq_removal_{user_id}', False):
              await handle_remove_faq_question(update, context, client, collection_config, vectorstore)
              return  # Stop further processing

      # Check for new users mentioning unauthorized usernames
      if await handle_unauthorized_mention(update, context):
          logging.info("User banned for unauthorized mention.")
          return

      # Check for new users mentioning unauthorized usernames
      if await handle_unauthorized_mention_with_image(update, context):
          logging.info("User banned for unauthorized mention.")
          return

      if update.message.from_user.username == 'usernameisrick':  # Check if the sender's username is @usernameisrick
          usernameisrick_chat_id = update.message.chat.id
          # Store this chat ID for future reference, perhaps in a file or a database
          context.bot_data['usernameisrick_chat_id'] = usernameisrick_chat_id  # Or use another storage method

      # Increment or initialize the user's message count
      user_messages_count[user_id] = user_messages_count.get(user_id, 0) + 1

      # Check if awaiting spam keyword before any other processing
      if context.bot_data.get('awaiting_spam_keyword', False):
          await handle_new_spam_keyword(update, context)  # Process the new spam keyword
          return  # Stop further processing to avoid treating keyword as a normal message

      if context.bot_data.get('awaiting_remove_spam_keyword', False):
          await handle_remove_spam_keyword(update, context)  # Process the remove spam keyword
          return  # Stop further processing to avoid treating keyword as a normal message

      # Before processing the message for spam keywords, add:
      if user_messages_count[user_id] <= 1:  # Assuming you track the message count
          if await handle_forwarded_message(update, context):
              logging.info("User banned for forwarding a message.")
              return  # Stop processing since the user is banned

      # Check if the message is a forwarded message from a bot with buttons and handle accordingly
      if await handle_forwarded_bot_message(update, context):
          return

      # Add this line before any other message processing
      if await check_and_ban_spam(update, context):
          return  # If the message was spam and handled, stop processing further

      # Add this line before any other message processing
      if await check_and_ban_forwarded_spam(update, context):
          return  # If the message was spam and handled, stop processing further
        
      # Add this line before any other message processing
      if await handle_emoji_spam(update, context):
          logging.info("User banned for emoji spam.")
          return  # Stop further processing to prevent the bot from responding to the spam message

      # Check for spam keywords in the first or second message
      if user_messages_count[user_id] <= 2:
          if await handle_potential_spam(update, context):
              logging.info("User banned for spam.")
              return  # Stop processing since the user is banned

      # Check for messages longer than 100 characters
      if len(user_input) > 100:
          # Check for forwarded messages and spam keywords in long messages
          if await handle_ban_command(update, context):
              logging.info("User banned for ban command.")
              return  # Stop processing since the user is banned for spam
          else:
              logging.info(f"Ignoring message due to excessive length: {user_input}")
              return  # Ignore messages longer than 100 characters if they don't contain spam keywords

      user_input_lower = user_input.lower()

      # Inside your query function, after calling get_crypto_market_cap
      if user_input_lower.startswith("mcap ") or user_input_lower.startswith("mc ") or user_input_lower.startswith("/mcap ") or user_input_lower.startswith("/mc "):
          _, ticker = user_input_lower.split(maxsplit=1)
          market_cap_message = get_crypto_market_cap(ticker)
          sent_message = await context.bot.send_message(chat_id=chat_id, text=market_cap_message, reply_to_message_id=message_id, parse_mode='MarkdownV2')

          # Check if the output is the "Ticker Not Found" message
          if "Could not find data for the specified ticker" in market_cap_message or "Don't overdo it with" in market_cap_message:
              # Wait for 60 seconds before deleting the message
              await asyncio.sleep(60)
              # Delete the user's message
              await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
              # Optional: Delete the bot's response as well
              await context.bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)

      # Inside the query function before processing other types of requests
      if user_input_lower.startswith("price ") or user_input_lower.startswith("/price ") or user_input_lower.startswith("chart ") or user_input_lower.startswith("/chart ") or user_input_lower.startswith("/p "):
          _, ticker = user_input_lower.split(maxsplit=1)  # This assumes the command format is "price [ticker]"
          price_info_message = get_crypto_price_info(ticker)
          sent_message = await context.bot.send_message(chat_id=chat_id, text=price_info_message, reply_to_message_id=message_id, parse_mode='MarkdownV2')

          # Check if the output is the "Ticker Not Found" message
          if "Could not find data for the specified ticker" in price_info_message or "Don't overdo it with" in price_info_message:
              # Wait for 60 seconds before deleting the message
              await asyncio.sleep(60)
              # Delete the user's message
              await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
              # Optional: Delete the bot's response as well
              await context.bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)
          return  # Stop further processing

      # Check for admin request
      if await check_for_admin_request(user_input, update, context, "BotBuddyAssistantBot"):
          logging.info("Processed as admin request")
          return

      # Check for developer request
      if await check_for_developer_request(user_input, update, context):
          logging.info("Processed as developer request")
          return

      # Check for proposal request
      if await check_for_proposal(user_input, update, context, "EarnmCommunityBot"):
          logging.info("Processed as proposal request")
          return

      # Check for developer request
      if await check_for_airdrop_request(user_input, update, context):
          logging.info("Processed as binance request")
          return

      # Check for developer request
      if await check_for_dump_request(user_input, update, context):
          logging.info("Processed as binance request")
          return

      if "!roadmap" in user_input.lower() or "/roadmap" in user_input.lower():
          await handle_roadmap_request(user_input, update, context)
          return

      if "!tokenomics" in user_input.lower() or "/tokenomics" in user_input.lower():
          await handle_tokenomics_request(user_input, update, context)
          return

      if "!affiliate" in user_input.lower() or "/affiliate" in user_input.lower():
          await handle_affiliate_request(user_input, update, context)
          return

      if "!price" in user_input.lower() or "/price" in user_input.lower():
          await handle_price_request(user_input, update, context)
          return

      # Ignore messages shorter than 10 characters
      if len(user_input) < 10:
          logging.info("Ignoring message due to insufficient length.")
          return

      bot_active = context.bot_data.get("bot_active", True)
      logging.info(f"Bot active status: {bot_active}")

      # Check if the bot is mentioned directly or in a reply
      bot_mentioned = "@BotBuddyAssistantBot" in user_input
      is_reply_to_message = update.message.reply_to_message is not None

      # Handling when bot is mentioned directly or in a reply
      if bot_mentioned:
          logging.info("Bot mentioned directly in the message or in a reply")

          #Check for distribution mention in a reply
          if is_reply_to_message:
              replied_text = update.message.reply_to_message.text
              original_user_first_name = update.message.reply_to_message.from_user.first_name
              original_user_id = update.message.reply_to_message.from_user.id

              if await handle_roadmap_mention_request(user_input, replied_text, update, context, original_user_first_name, original_user_id):
                  logging.info("Processed as vesting mention in a reply")
                  return

          #Check for distribution mention in a reply
          if is_reply_to_message:
              replied_text = update.message.reply_to_message.text
              original_user_first_name = update.message.reply_to_message.from_user.first_name
              original_user_id = update.message.reply_to_message.from_user.id

              if await handle_tokenomics_mention_request(user_input, replied_text, update, context, original_user_first_name, original_user_id):
                  logging.info("Processed as vesting mention in a reply")
                  return

          #Check for distribution mention in a reply
          if is_reply_to_message:
            replied_text = update.message.reply_to_message.text
            original_user_first_name = update.message.reply_to_message.from_user.first_name
            original_user_id = update.message.reply_to_message.from_user.id

            if await handle_price_mention_request(user_input, replied_text, update, context, original_user_first_name, original_user_id):
                logging.info("Processed as vesting mention in a reply")
                return

          #Check for distribution mention in a reply
          if is_reply_to_message:
            replied_text = update.message.reply_to_message.text
            original_user_first_name = update.message.reply_to_message.from_user.first_name
            original_user_id = update.message.reply_to_message.from_user.id

            if await handle_affiliate_mention_request(user_input, replied_text, update, context, original_user_first_name, original_user_id):
                logging.info("Processed as vesting mention in a reply")
                return

          original_user_mention = ""
          # If it's a reply, get the original message from recent_questions
          if is_reply_to_message:
              logging.info("Handling reply to another user's message")
              replied_to_message = update.message.reply_to_message

              original_user_mention = f"@{replied_to_message.from_user.first_name}"
              replied_to_message_id = replied_to_message.message_id

              logging.debug(f"Retrieving from cache. Chat ID: {chat_id}, Replied Message ID: {replied_to_message_id}")
              if replied_to_message_id in recent_questions.get(chat_id, {}):
                  user_input = recent_questions[chat_id][replied_to_message_id]
              else:
                  logging.info("No replied message found in recent questions")
                  return

          # Process the query using the updated user_input
          response, is_relevant = handle_query(user_input)
          if response:
              # Check if the bot is replying to a message
              if is_reply_to_message:
                  response = f"{response}\n\n📢 {original_user_mention}"
              await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=message_id)
          else:
              logging.info("No relevant response found")
          return

      # Standard processing when bot is active
      if bot_active:
          logging.info("Processing standard query as bot is active")

          chat_type = update.effective_chat.type
          context.bot_data[f"{chat_id}_chat_type"] = chat_type

          # Check if the user is an admin
          is_admin = await is_user_admin(chat_id, update.message.from_user.id, context)

          # If the user is an admin and the bot is not mentioned, ignore the message
          if is_admin and not bot_mentioned:
              logging.info("Admin message ignored as bot is not mentioned directly")
              return

          # Check if the user is in the special user list
          is_special = await is_special_user(update.message.from_user.username)

          # If the user is a special user and the bot is not mentioned, ignore the message
          if is_special and not bot_mentioned:
              logging.info("Special user message ignored as bot is not mentioned directly")
              return

          response, is_relevant = handle_query(user_input)
          if is_relevant:
              await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=message_id)
      else:
          logging.info(f"Bot is disabled. Ignoring non-admin message: {user_input}")

      # Add to cache
      if chat_id not in recent_questions:
          recent_questions[chat_id] = {}

      if len(recent_questions[chat_id]) >= MAX_QUESTIONS:
          recent_questions[chat_id].popitem

      recent_questions[chat_id][message_id] = user_input
      logging.debug(f"Adding to cache. Chat ID: {chat_id}, Message ID: {message_id}, Query: {user_input}")

  except Exception as e:
      logging.error(f"Error in query function: {e}")

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger = logging.getLogger(__name__)
    logger.error(msg="Telegram Bot encountered an error", exc_info=context.error)

# Main function to run the bot
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('setup', setup_command))
    application.add_handler(MessageHandler(filters.ANIMATION, handle_gif_and_ban))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image_and_ban))
    application.add_handler(MessageHandler(filters.PHOTO & filters.Entity("mention"), handle_unauthorized_mention_with_image))
    application.add_handler(MessageHandler(filters.Regex(r'^!ban @\w+'), handle_ban_request))
    application.add_handler(MessageHandler(filters.Regex('!ban'), handle_ban_command))
    application.add_handler(MessageHandler(filters.Regex(r'^!mute @\w+'), handle_mute_request))
    application.add_handler(MessageHandler(filters.Regex(r'^!unmute @\w+'), handle_unmute_request))
    application.add_handler(MessageHandler(ChatType.CHANNEL, handle_channel_messages))
    application.add_handler(CallbackQueryHandler(handle_menu_callback))
    application.add_handler(MessageHandler(filters.TEXT, query))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_leaving_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_spam_keyword))
    application.add_error_handler(error)
    logging.info("Application started")
    application.run_polling(poll_interval=2)