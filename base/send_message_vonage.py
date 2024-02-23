import logging
logger = logging.getLogger(__name__)
import re
import vonage
from django.conf import settings
# from .models import TextMessage
import time
import requests
from .aws_kms_functions import decrypt_data

client = vonage.Client(key=settings.VONAGE_KEY, secret=settings.VONAGE_SECRET, timeout=100)
sms = vonage.Sms(client)

def splitter(message):
    # Add logging for message splitting
    logger.info("Splitting message...")
    tb = message.encode('utf-8')
    if len(tb) < 1200:
        return [message]
    else:
        rgx = re.compile(b"[\s\S]*\W")
        m = rgx.match(tb[:1200])
        split_messages = [tb[:len(m[0])].decode('utf-8')] + splitter(tb[len(m[0]):].decode('utf-8'))
        logger.info(f"Split messages: {split_messages}")
        return split_messages

def send_message_vonage(message, phone_number, route,include_name):
    # Add logging for sending messages via Vonage
    logger.info(f"Sending message: {message} to phone number: {phone_number.pk}, route: {route}")
    name = decrypt_data(phone_number.name, phone_number.name_key)
    if message and include_name:
        if phone_number.language == "es":
            message = f"Hola {name}, {message}"
        else:
            message = f"Hi {name}, {message}"

    
    if phone_number.active:
        for message_text in splitter(message):
            logger.info(f"Sending message: {message_text}")
            # Send the message using Vonage SMS
            to_phone_number = decrypt_data(phone_number.phone_number, phone_number.phone_number_key)
            # print("from: ", settings.VONAGE_NUMBER, "to: ", str(to_phone_number))
            response_data = sms.send_message({"from": settings.VONAGE_NUMBER, "to": str(to_phone_number), "text": message_text, "type": "unicode"})
            logger.info(f"Message response: {response_data}")
            if response_data["messages"][0]["status"] == "0":
                logger.info("Message sent successfully.")
                logger.info(f"Message details: {response_data}")
            else:
                error_message = response_data['messages'][0]['error-text']
                logger.error(f"Message failed with error: {error_message}")
    else:
        logger.info("Phone number is not active. Message not sent.")

def retry_send_message_vonage(message, phone_number, route, max_retries=3, retry_delay=5,include_name=True):
    for attempt in range(max_retries):
        try:
            send_message_vonage(message, phone_number, route, include_name)
            return True  # Message sent successfully
        except requests.exceptions.ConnectionError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    return False  # All retry attempts failed

def text_josh_opt_in(message):
    number = settings.JOSH_NUMBER
    if number:
        response_data = sms.send_message({"from": settings.VONAGE_NUMBER, "to": str(number), "text": message, "type": "unicode"})
        return response_data
    return None