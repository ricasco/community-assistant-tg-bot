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
new_group_members = {}  # Add this at the top of your script to track new users for the session

call_timestamps = {}
call_timestamps1 = {}
call_timestamps2 = {}
call_timestamps3 = {}
call_timestamps4 = {}

async def check_for_admin_request(text, update, context, BOT_USERNAME):
    admin_phrases = ["I need admin", "I need an admin", "looking for admin", "looking for support", "I need support", "i need support", "i need an admin", "how can I contact an admin", "how can i contact an admin", "looking for an admin"]
    logging.info("Checking for admin request")  # Debug log

    if any(phrase.lower() in text.lower() for phrase in admin_phrases):
        logging.info("Admin request identified")  # Debug log
        admins = await context.bot.get_chat_administrators(chat_id=update.effective_chat.id)
        admin_mentions = ", ".join([f"[{admin.user.first_name}](tg://user?id={admin.user.id})" for admin in admins if admin.user.username != BOT_USERNAME])
        await update.message.reply_text(f"📢 Calling admins 🫡 {admin_mentions}", parse_mode="Markdown", reply_to_message_id=update.message.message_id)
        return True

    logging.info("No admin request found")  # Debug log
    return False

async def check_for_developer_request(text, update, context):
    developer_phrases = ["Who needs developer", "Does anyone need developer", "do you need developer", "looking for developer", "do you need a developer"]
    logging.info("Checking for developer request")  # Debug log

    if any(phrase.lower() in text.lower() for phrase in developer_phrases):
      logging.info("Developer request identified")  # Debug log
      await update.message.reply_text("You are welcome to send your CV to cv@botbuddy.co. Our team will contact you if there's room for further discussion.", reply_to_message_id=update.message.message_id)
      return True

    logging.info("No developer request found")  # Debug log
    return False

async def check_for_airdrop_request(text, update, context):
    airdrop_phrases = ["Wen airdrop", "When airdrop", "wen IDO", "when IDO", "wen TGE", "when TGE"]
    logging.info("Checking for airdrop request")  # Debug log

    if any(phrase.lower() in text.lower() for phrase in airdrop_phrases):
      logging.info("airdrop request identified")  # Debug log
      await update.message.reply_text("The TGE and related Airdrop of the $BOT token will happen on Q2. You can find more detailed information by visiting https://botbuddy.gitbook.io/botbuddy-docs/tokenomics-usdbot.", 
reply_to_message_id=update.message.message_id)
      return True

    logging.info("No airdrop request found")  # Debug log
    return False

async def check_for_dump_request(text, update, context):
    dump_phrases = ["why dump", "Why the token is dumping", "why LAKE is dumping", "why lake dump", "wen pump"]
    logging.info("Checking for dump request")  # Debug log

    if any(phrase.lower() in text.lower() for phrase in dump_phrases):
      logging.info("dump request identified")  # Debug log
      await update.message.reply_text("Where were you during the pump? Remember nobody queues for a flat rollercoaster, and if this is not your cup of tea, we can suggest you to start studying the Government Bonds", 
reply_to_message_id=update.message.message_id)
      return True

    logging.info("No dump request found")  # Debug log
    return False

def escape_markdown_v2(text):
    """Escape special characters for MarkdownV2."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(['\\' + char if char in special_chars else char for char in text])

async def handle_command_request(text, update, context):
    global call_timestamps
    command_phrases = ["!help", "/help"]
    chat_id = update.effective_chat.id

    if any(phrase in text.lower() for phrase in command_phrases):
        current_time = time.time()

        # Filter timestamps to keep only those within the last 60 minutes
        recent_calls = call_timestamps.get(chat_id, [])
        recent_calls = [timestamp for timestamp in recent_calls if current_time - timestamp < 3600]
        call_timestamps[chat_id] = recent_calls

        # Check if the function has been called less than 3 times in the last 60 minutes
        if len(recent_calls) < 5:
            call_timestamps[chat_id].append(current_time)  # Record the current call timestamp
            command_response = "🤖 Hello Buddy!\n\n" \
          "Here's the list of commands available:\n" \
          "!price  → to display the prices of the Community Assistant.\n\n" \
          "!tokenomics → to display the link to the tokenomics page of the docs.\n\n" \
          "!affiliate → to display the link to the Affiliate Program page of the docs.\n\n" \
          "!roadmap → to display the roadmap of BotBuddy and the link to the roadmap page of the docs."
            # The line to send the photo has been removed
            await update.message.reply_text(command_response)
        else:
            # Rate limit exceeded; inform the user
            await update.message.reply_text("You've reached the maximum number of requests for the last 60 minutes. Try again in less than one hour.")
        return True
    return False

async def handle_tokenomics_request(text, update, context):
    global call_timestamps1
    tokenomics_phrases = ["!tokenomics", "/tokenomics"]
    chat_id = update.effective_chat.id

    # Check for tokenomics phrase in the message
    if any(phrase in text.lower() for phrase in tokenomics_phrases):
        current_time = time.time()

        # Filter timestamps to keep only those within the last 60 minutes
        recent_calls = call_timestamps1.get(chat_id, [])
        recent_calls = [timestamp for timestamp in recent_calls if current_time - timestamp < 3600]
        call_timestamps1[chat_id] = recent_calls

        # Check if the function has been called less than 3 times in the last 60 minutes
        if len(recent_calls) < 5:
            call_timestamps1[chat_id].append(current_time)  # Record the current call timestamp
            tokenomics_response = "The tokenomics of $BOT has not yet been revealed. You can find some hints and more detailed information by visiting: https://botbuddy.gitbook.io/botbuddy-docs/tokenomics-usdbot."
            await update.message.reply_text(tokenomics_response, disable_web_page_preview=True)
        else:
            # Rate limit exceeded; inform the user
            await update.message.reply_text("You've reached the maximum number of requests for the last 60 minutes. Try again in less than one hour.")
        return True
    return False

async def handle_affiliate_request(text, update, context):
    global call_timestamps2
    affiliate_phrases = ["!affiliate", "/affiliate"]
    chat_id = update.effective_chat.id

    # Check for tokenomics phrase in the message
    if any(phrase in text.lower() for phrase in affiliate_phrases):
        current_time = time.time()

        # Filter timestamps to keep only those within the last 60 minutes
        recent_calls = call_timestamps2.get(chat_id, [])
        recent_calls = [timestamp for timestamp in recent_calls if current_time - timestamp < 3600]
        call_timestamps2[chat_id] = recent_calls

        # Check if the function has been called less than 3 times in the last 60 minutes
        if len(recent_calls) < 5:
            call_timestamps2[chat_id].append(current_time)  # Record the current call timestamp
            affiliate_response = "For more information about our Affiliate Program ask detailed questions in the chat to get an answer or visit the related page on our docs https://botbuddy.gitbook.io/botbuddy-docs/affiliate-program-bot-airdrop"
            await update.message.reply_text(affiliate_response, disable_web_page_preview=True)
        else:
            # Rate limit exceeded; inform the user
            await update.message.reply_text("You've reached the maximum number of requests for the last 60 minutes. Try again in less than one hour.")
        return True
    return False

async def handle_tokenomics_mention_request(text, replied_text, update, context, original_user_first_name, original_user_id):
  tokenomics_phrases = ["tokenomics"]
  if any(phrase in replied_text.lower() for phrase in tokenomics_phrases):
      tokenomics_response = escape_markdown_v2("The tokenomics of $BOT has not yet been revealed. You can find some hints and more detailed information by visiting: https://botbuddy.gitbook.io/botbuddy-docs/tokenomics-usdbot.") 
      escaped_name = escape_markdown_v2(original_user_first_name)
      mention = f"[{escaped_name}](tg://user?id={original_user_id})"
      full_response = f"{tokenomics_response}\n\n📢 {mention}"
      await update.message.reply_text(full_response, parse_mode="MarkdownV2", reply_to_message_id=update.message.message_id)
      return True
  return False

async def handle_affiliate_mention_request(text, replied_text, update, context, original_user_first_name, original_user_id):
  affiliate_phrases = ["affiliate"]
  if any(phrase in replied_text.lower() for phrase in affiliate_phrases):
      affiliate_response = escape_markdown_v2("For more information about our Affiliate Program ask detailed questions in the chat to get an answer or visit the related page on our docs https://botbuddy.gitbook.io/botbuddy-docs/affiliate-program-bot-airdrop")
      escaped_name = escape_markdown_v2(original_user_first_name)
      mention = f"[{escaped_name}](tg://user?id={original_user_id})"
      full_response = f"{affiliate_response}\n\n📢 {mention}"
      await update.message.reply_text(full_response, parse_mode="MarkdownV2", reply_to_message_id=update.message.message_id)
      return True
  return False

async def handle_roadmap_request(text, update, context):
    global call_timestamps3
    roadmap_phrases = ["!roadmap", "/roadmap"]
    chat_id = update.effective_chat.id

    # Check for tokenomics phrase in the message
    if any(phrase in text.lower() for phrase in roadmap_phrases):
        current_time = time.time()

        # Filter timestamps to keep only those within the last 60 minutes
        recent_calls = call_timestamps3.get(chat_id, [])
        recent_calls = [timestamp for timestamp in recent_calls if current_time - timestamp < 3600]
        call_timestamps3[chat_id] = recent_calls

        # Check if the function has been called less than 3 times in the last 60 minutes
        if len(recent_calls) < 5:
            call_timestamps3[chat_id].append(current_time)  # Record the current call timestamp
            roadmap_response = "🛣 For more information about our roadmap ask detailed questions in the chat to get an answer or visit the related page on our docs https://botbuddy.gitbook.io/botbuddy-docs/roadmap"
            roadmap_image_url = "https://ibb.co/7GWmRGP"
            await context.bot.send_photo(chat_id=chat_id, photo=roadmap_image_url)
            await update.message.reply_text(roadmap_response, disable_web_page_preview=True)
        else:
            # Rate limit exceeded; inform the user
            await update.message.reply_text("You've reached the maximum number of requests for the last 60 minutes. Try again in less than one hour.")
        return True
    return False

async def handle_price_request(text, update, context):
    global call_timestamps4
    price_phrases = ["!price", "/price"]
    chat_id = update.effective_chat.id

    # Check for tokenomics phrase in the message
    if any(phrase in text.lower() for phrase in price_phrases):
        current_time = time.time()

        # Filter timestamps to keep only those within the last 60 minutes
        recent_calls = call_timestamps4.get(chat_id, [])
        recent_calls = [timestamp for timestamp in recent_calls if current_time - timestamp < 3600]
        call_timestamps4[chat_id] = recent_calls

        # Check if the function has been called less than 3 times in the last 60 minutes
        if len(recent_calls) < 5:
            call_timestamps4[chat_id].append(current_time)  # Record the current call timestamp
            price_response = "For more information about our Community Assistant and its prices visit the related page on our docs: https://botbuddy.gitbook.io/botbuddy-docs/our-services/telegram-discord-community-assistant"
            price_image_url = "https://ibb.co/MM5pGhz"
            await context.bot.send_photo(chat_id=chat_id, photo=price_image_url)
            await update.message.reply_text(price_response, disable_web_page_preview=True)
        else:
            # Rate limit exceeded; inform the user
            await update.message.reply_text("You've reached the maximum number of requests for the last 60 minutes. Try again in less than one hour.")
        return True
    return False

async def handle_roadmap_mention_request(text, replied_text, update, context, original_user_first_name, original_user_id):
  roadmap_phrases = ["roadmap"]
  if any(phrase in replied_text.lower() for phrase in roadmap_phrases):
      roadmap_response = escape_markdown_v2("For more information about our roadmap ask detailed questions in the chat to get an answer or visit the related page on our docs https://botbuddy.gitbook.io/botbuddy-docs/roadmap")
      roadmap_image_url = "https://ibb.co/7GWmRGP"  
      escaped_name = escape_markdown_v2(original_user_first_name)
      mention = f"[{escaped_name}](tg://user?id={original_user_id})"
      full_response = f"{roadmap_response}\n\n📢 {mention}"
      await context.bot.send_photo(chat_id=update.effective_chat.id, photo=roadmap_image_url)
      await update.message.reply_text(full_response, parse_mode="MarkdownV2", reply_to_message_id=update.message.message_id)
      return True
  return False

async def handle_price_mention_request(text, replied_text, update, context, original_user_first_name, original_user_id):
  price_phrases = ["Community Assistant price", "price of the Community Assistant"]
  if any(phrase in replied_text.lower() for phrase in price_phrases):
      price_response = escape_markdown_v2("For more information about our Community Assistant and its prices visit the related page on our docs: https://botbuddy.gitbook.io/botbuddy-docs/our-services/telegram-discord-community-assistant")
      price_image_url = "https://ibb.co/MM5pGhz"  
      escaped_name = escape_markdown_v2(original_user_first_name)
      mention = f"[{escaped_name}](tg://user?id={original_user_id})"
      full_response = f"{price_response}\n\n📢 {mention}"
      await context.bot.send_photo(chat_id=update.effective_chat.id, photo=price_image_url)
      await update.message.reply_text(full_response, parse_mode="MarkdownV2", reply_to_message_id=update.message.message_id)
      return True
  return False

def filter_ai_sentences(response_text):
    filtered_sentences = []
    for sentence in response_text.split('.'):
        # Check if the sentence starts with 'I am' or 'I'm'
        if not sentence.strip().startswith('I am') and not sentence.strip().startswith("I'm") and not sentence.strip().startswith("I cannot") and not sentence.strip().startswith("My purpose") and not sentence.strip().startswith("It is not specified") and not sentence.strip().startswith("I can't") and not sentence.strip().startswith("It's not specified") and not sentence.strip().startswith("I do not know") and not sentence.strip().startswith("I don't know") and not sentence.strip().startswith("The context") and not sentence.strip().startswith("If you have") and not sentence.strip().startswith("Please provide") and not sentence.strip().startswith("Based on the given context") and not sentence.strip().startswith("Can I") and not sentence.strip().startswith("Can you"):
            filtered_sentences.append(sentence)
    return '.'.join(filtered_sentences).strip()

def append_campaign(query, response):
  campaign_keyword = "affiliate program"
  campaign_link = "https://botbuddy.gitbook.io/botbuddy-docs/affiliate-program-bot-airdrop"
  additional_text = "Learn more about the BotBuddy Affiliate Program by visiting: " + campaign_link

  # Check if 'OTC' is in the user's query
  if campaign_keyword.lower() in query.lower():
      # Check if the link is not in the response
      if campaign_link not in response:
          # Append the additional text to the response
          response += "\n" + additional_text

  return response

def append_how_to_buy(query, response):
    how_to_buy_keywords = [
        "how can I buy BOT",
        "where to purchase BOT",
        "how can I buy $BOT",
        "where can I buy BOT",
        "where can I buy $BOT"        
    ]
    how_to_buy_link = "https://botbuddy.gitbook.io/botbuddy-docs/tokenomics-usdbot"
    additional_text = "Visit https://botbuddy.gitbook.io/botbuddy-docs/tokenomics-usdbot for all the details regarding the BOT token"

    # Convert query to lower case for case-insensitive comparison
    query_lower = query.lower()

    # Check if any of the keywords are in the user's query
    if any(keyword.lower() in query_lower for keyword in how_to_buy_keywords):
        # Check if the link is not in the response
        if how_to_buy_link not in response:
            # Append the additional text to the response
            response += "\n" + additional_text

    return response

def append_proposal(query, response):
    proposal_keywords = ["marketing proposal", "listing proposal", "commercial proposal", "partnership proposal"]
    proposal_email = "proposal@botbuddy.co"
    additional_text = "For proposals, please email: " + proposal_email

    # Convert query to lower case for case-insensitive comparison
    query_lower = query.lower()

    # Check if any of the keywords are in the user's query
    if any(keyword.lower() in query_lower for keyword in proposal_keywords):
        # Check if the link is not in the response
        if proposal_email not in response:
            # Append the additional text to the response
            response += "\n" + additional_text

    return response

async def check_for_proposal(text, update, context, BOT_USERNAME):
  proposal_phrases = ["marketing proposal", "listing proposal", "commercial proposal", "partnership proposal"]
  logging.info("Checking for proposal request")  # Debug log

  if any(phrase.lower() in text.lower() for phrase in proposal_phrases):
      logging.info("Proposal request identified")  # Debug log
      # Send a fixed message
      await update.message.reply_text(
          "For proposals, please email: proposal@botbuddy.co",
          reply_to_message_id=update.message.message_id
      )
      return True

  logging.info("No proposal request found")  # Debug log
  return False

async def is_user_admin(chat_id, user_id, context):
    # Check if the chat type is either 'group' or 'supergroup'
    chat_type = context.bot_data.get(f"{chat_id}_chat_type", None)
    if chat_type not in ['group', 'supergroup']:
        return False  # Not a group or supergroup, so no admins exist

    try:
        chat_administrators = await context.bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in chat_administrators)
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False

# List of specific usernames
SPECIAL_USERNAMES = [""]  # Add the usernames you want to check

async def is_special_user(username):
  return username in SPECIAL_USERNAMES

def get_crypto_market_cap(ticker):
    coingecko_api_url = os.getenv("COINGECKO_API_URL")

    try:
        coins_list_response = requests.get(f"{coingecko_api_url}/coins/list")
        if coins_list_response.status_code != 200:
            return "Don't overdo it with requests every two seconds. Let me breathe for a minute and try again when this message disappears 😤"

        coins_list = coins_list_response.json()
        matching_coins = [coin for coin in coins_list if coin['symbol'].lower() == ticker.lower()]

        if not matching_coins:
            return f"Could not find data for the specified ticker 🤔\n\nThere are a few possible reasons:\n1\) You might have typed the project's name instead of its ticker symbol\. Wake up 💤\n2\) The shitcoin you are inquiring about may not yet be listed on CoinGecko\. Better checking [DexScreener](https://dexscreener\.com/) for the latest listings\.\n3\) You are definitely drunk\!"

        # Fetch market cap for each matching coin and select the one with the largest market cap
        max_market_cap = 0
        selected_coin = None
        for coin in matching_coins:
            coin_id = coin['id']
            url = f"{coingecko_api_url}/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true"
            response = requests.get(url)
            data = response.json()

            if coin_id in data and 'usd_market_cap' in data[coin_id]:
                market_cap = data[coin_id]['usd_market_cap']
                if market_cap > max_market_cap:
                    max_market_cap = market_cap
                    selected_coin = coin

        if not selected_coin:
            return f"Don't overdo it with requests every two seconds. Let me breathe for a minute and try again when this message disappears 😤"

        market_cap_formatted = f"${max_market_cap:,.0f}"
        # Assuming real-time or near real-time updates, adjust as needed
        last_updated = "1 minute ago"  # Placeholder, can be adjusted to use actual timestamp data

        return f"The market cap of {selected_coin['name']} \(${ticker.upper()}\) is: {market_cap_formatted} \(Last updated: {last_updated}\)\n\n*Made with 💚 by *[*BotBuddy*](https://botbuddy\.co/)\n\-\-\-\n_Data provided by CoinGecko_"

    except Exception as e:
        # Escape the exception message for MarkdownV2
        exception_message = "Don't overdo it with requests every two seconds. Let me breathe for a minute and try again when this message disappears 😤"
        escaped_exception_message = escape_markdown_v2(exception_message)
        return escaped_exception_message

def get_crypto_price_info(ticker):
    coingecko_api_url = os.getenv("COINGECKO_API_URL")

    try:
        coins_list_response = requests.get(f"{coingecko_api_url}/coins/list")
        if coins_list_response.status_code != 200:
            return escape_markdown_v2(f"Don't overdo it with requests every two seconds. Let me breathe for a minute and try again when this message disappears 😤")

        coins_list = coins_list_response.json()
        if not isinstance(coins_list, list):
            return escape_markdown_v2("Unexpected response format from API.")

        # Filter all coins matching the ticker
        matching_coins = [coin for coin in coins_list if coin['symbol'].lower() == ticker.lower()]
        if not matching_coins:
            return f"Could not find data for the specified ticker 🤔\n\nThere are a few possible reasons:\n1\) You might have typed the project's name instead of its ticker symbol\. Wake up 💤\n2\) The shitcoin you are inquiring about may not yet be listed on CoinGecko\. Better checking [DexScreener](https://dexscreener\.com/) for the latest listings\.\n3\) You are definitely drunk\!"

        # Fetch market data for matching coins
        coin_ids = ','.join([coin['id'] for coin in matching_coins])
        markets_response = requests.get(f"{coingecko_api_url}/coins/markets", params={'vs_currency': 'usd', 'ids': coin_ids})
        if markets_response.status_code != 200:
            return escape_markdown_v2("Error fetching market data for matching coins.")

        markets_data = markets_response.json()
        if not markets_data:
            return escape_markdown_v2("No market data available for matching coins.")

        # Find the coin with the highest market cap
        coin = max(markets_data, key=lambda x: x.get('market_cap') if x.get('market_cap') is not None else -1)

        # Check for valid coin data (assuming coin is now a single coin with the highest market cap)
        coin_id = coin['id']
        coin_data_response = requests.get(f"{coingecko_api_url}/coins/{coin_id}")
        if coin_data_response.status_code != 200:
            return escape_markdown_v2("Don't overdo it with requests every two seconds. Let me breathe for a minute and try again when this message disappears 😤")

        coin_data = coin_data_response.json()
        if not isinstance(coin_data, dict):
            return escape_markdown_v2("Unexpected coin data format.")

        # Extracting data...
        if 'market_data' not in coin_data or 'current_price' not in coin_data['market_data']:
            return escape_markdown_v2("Market data not available for " + ticker + ".")

        market_data = coin_data['market_data']
        name = coin_data.get('name', 'N/A')
        symbol = ticker.upper()
        price = str(market_data.get('current_price', {}).get('usd', 'N/A'))
        price_change_1h_data = market_data.get('price_change_percentage_1h_in_currency', {}).get('usd', 'N/A')
        price_change_1h = "{:.2f}".format(float(price_change_1h_data)) if price_change_1h_data != 'N/A' else "0.00"
        price_change_24h_data = market_data.get('price_change_percentage_24h_in_currency', {}).get('usd', 'N/A')
        price_change_24h = "{:.2f}".format(float(price_change_24h_data)) if price_change_24h_data != 'N/A' else "0.00"
        price_change_7d_data = market_data.get('price_change_percentage_7d_in_currency', {}).get('usd', 'N/A')
        price_change_7d = "{:.2f}".format(float(price_change_7d_data)) if price_change_7d_data != 'N/A' else "0.00"
        high_24h = str(market_data.get('high_24h', {}).get('usd', 'N/A'))
        low_24h = str(market_data.get('low_24h', {}).get('usd', 'N/A'))
        volume_24h = f"{float(market_data.get('total_volume', {}).get('usd', 0)):,.0f}"
        market_cap = f"{float(market_data.get('market_cap', {}).get('usd', 0)):,.0f}"

        # Apply escape_markdown_v2 to each component individually
        name_escaped = escape_markdown_v2(name)
        symbol_escaped = escape_markdown_v2(symbol)
        price_escaped = escape_markdown_v2(price)
        price_change_1h_escaped = escape_markdown_v2(price_change_1h)
        price_change_24h_escaped = escape_markdown_v2(price_change_24h)
        price_change_7d_escaped = escape_markdown_v2(price_change_7d)
        high_24h_escaped = escape_markdown_v2(high_24h)
        low_24h_escaped = escape_markdown_v2(low_24h)
        volume_24h_escaped = escape_markdown_v2(volume_24h)
        market_cap_escaped = escape_markdown_v2(market_cap)

        response_message = (
            f"{name_escaped} \| ${symbol_escaped}\n"
            f"💸 Price: ${price_escaped}\n"
            f"▶️ 1h: {price_change_1h_escaped}%\n"
            f"▶️ 24h: {price_change_24h_escaped}%\n"
            f"▶️ 7d: {price_change_7d_escaped}%\n"
            f"⚖️ 24h High/Low: ${high_24h_escaped} \| ${low_24h_escaped}\n"
            f"📊 24h Volume: ${volume_24h_escaped}\n"
            f"💹 Market Cap: ${market_cap_escaped}\n"
            f"📈 [Chart](https://www.coingecko.com/en/coins/{coin_id})\n\n"
            f"*Made with 💚 by *[*BotBuddy*](https://botbuddy\.co/)\n\-\-\-\n_Data provided by CoinGecko_"
        )

        return response_message
    except Exception as e:
        return escape_markdown_v2("Failed to fetch price info for " + ticker + ": " + str(e))

async def handle_leaving_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the update is a left chat member update
    if update.message.left_chat_member:
        try:
            # Attempt to delete the message
            await context.bot.delete_message(chat_id=update.message.chat_id,
                                           message_id=update.message.message_id)
            logging.info(f"Deleted message about {update.message.left_chat_member.first_name} leaving the group.")
        except Exception as e:
            logging.error(f"Failed to delete message about user leaving: {e}")

def check_user_message_limit(user_id: int) -> bool:
    current_time = datetime.now()
    user_data = user_message_limits.get(user_id)

    # If the user is new or their count has reset
    if user_data is None or current_time - user_data['first_message_time'] > timedelta(days=1):
        user_message_limits[user_id] = {'count': 1, 'first_message_time': current_time}
        return False  # User has not exceeded the limit

    # If the user has sent 50 or more messages in the last 24 hours
    if user_data['count'] >= 15:
        return True  # User has exceeded the limit

    # Increment the message count and allow the message
    user_data['count'] += 1
    return False