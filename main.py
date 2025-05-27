from src.news_utils import get_latest_news
import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

def send_telegram_message(message: str, token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        logging.info("✅ ส่งข่าวล่าสุดไปยัง Telegram เรียบร้อยแล้ว")
    except Exception as e:
        logging.error("❌ ไม่สามารถส่งข่าวไปยัง Telegram ได้", exc_info=True)

def main():
    news_message = get_latest_news()
    if not news_message:
        logging.warning("❌ ไม่พบข่าวล่าสุดหรือดึงข่าวล้มเหลว")
        return

    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not telegram_token or not telegram_chat_id:
        logging.error("❌ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ไม่ถูกตั้งค่าใน .env")
        return

    # รองรับหลายแชท
    chat_ids = [cid.strip() for cid in telegram_chat_id.split(",")]
    for chat_id in chat_ids:
        send_telegram_message(news_message, telegram_token, chat_id)

if __name__ == "__main__":
    main()
