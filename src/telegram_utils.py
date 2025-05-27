import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_alert(message: str) -> dict:
    """ส่งข้อความแจ้งเตือนไปยัง Telegram chat ที่กำหนด"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError('Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment variables')
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    return response.json()
