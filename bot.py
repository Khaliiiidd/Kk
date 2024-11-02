from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from instagrapi import Client
import logging
import imaplib
import email
import time
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
USER_DATA = {}

class InstagramSwapper:
    def __init__(self):
        self.client1 = Client()
        self.client2 = Client()

    def get_code_from_email(self, email_address, email_password):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(email_address, email_password)
            mail.select("inbox")

            # Wait 10 seconds to ensure the message arrives
            time.sleep(10)
            _, messages = mail.search(None, '(FROM "security@mail.instagram.com" UNSEEN)')
            
            if messages[0]:
                latest_email_id = messages[0].split()[-1]
                _, msg = mail.fetch(latest_email_id, "(RFC822)")
                email_body = msg[0][1]
                email_message = email.message_from_bytes(email_body)

                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        codes = re.findall(r'\b\d{6}\b', body)
                        if codes:
                            return codes[0]
            return None
        except Exception as e:
            logging.error(f"Error getting the code: {e}")
            return None

    def swap_usernames(self, username1, password1, username2, password2, email_address, email_password):
        try:
            # Attempt login for both accounts
            self.client1.login(username1, password1)
        except Exception:
            # If login fails, get verification code
            code = self.get_code_from_email(email_address, email_password)
            if code:
                self.client1.input_code(code)

        try:
            self.client2.login(username2, password2)
        except Exception:
            # If login fails, get verification code
            code = self.get_code_from_email(email_address, email_password)
            if code:
                self.client2.input_code(code)

        try:
            # Save original usernames
            old_username1 = username1
            old_username2 = username2
            
            # Change the first account's username to a temporary username
            temp_username = f"temp_{int(time.time())}"
            self.client1.account_set_username(temp_username)

            # Change the second account's username to the first account's original username
            self.client2.account_set_username(old_username1)

            # Change the temporary username back to the second account's original username
            self.client1.account_set_username(old_username2)

            return True, "Usernames swapped successfully!"
        except Exception as e:
            logging.error(f"Error during swap: {e}")
            return False, f"Error: {str(e)}"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! To start swapping usernames, send /swap")

def swap_command(update: Update, context: CallbackContext):
    update.message.reply_text("Send the first account username")
    USER_DATA[update.effective_chat.id] = {'step': 'username1'}

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in USER_DATA:
        return

    current_step = USER_DATA[chat_id]['step']
    message = update.message.text

    if current_step == 'username1':
        USER_DATA[chat_id]['username1'] = message
        USER_DATA[chat_id]['step'] = 'password1'
        update.message.reply_text("Send the first account password")
    
    elif current_step == 'password1':
        USER_DATA[chat_id]['password1'] = message
        USER_DATA[chat_id]['step'] = 'username2'
        update.message.reply_text("Send the second account username")
    
    elif current_step == 'username2':
        USER_DATA[chat_id]['username2'] = message
        USER_DATA[chat_id]['step'] = 'password2'
        update.message.reply_text("Send the second account password")
    
    elif current_step == 'password2':
        USER_DATA[chat_id]['password2'] = message
        USER_DATA[chat_id]['step'] = 'email'
        update.message.reply_text("Send the email associated with the accounts")
    
    elif current_step == 'email':
        USER_DATA[chat_id]['email'] = message
        USER_DATA[chat_id]['step'] = 'email_password'
        update.message.reply_text("Send the email password")
    
    elif current_step == 'email_password':
        USER_DATA[chat_id]['email_password'] = message
        swapper = InstagramSwapper()
        success, response_message = swapper.swap_usernames(
            USER_DATA[chat_id]['username1'],
            USER_DATA[chat_id]['password1'],
            USER_DATA[chat_id]['username2'],
            USER_DATA[chat_id]['password2'],
            USER_DATA[chat_id]['email'],
            USER_DATA[chat_id]['email_password']
        )
        update.message.reply_text(response_message)
        USER_DATA.pop(chat_id, None)

def main():
    updater = Updater("7199884330:AAFIVP5HzOjqW5fuUYWBcB6rEos78j5V0nk")
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("swap", swap_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
