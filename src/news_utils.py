import requests
import os
from dotenv import load_dotenv
from googletrans import Translator
import time

load_dotenv()
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

def translate_text(text: str, retries: int = 3) -> str:
    """
    แปลข้อความจากอังกฤษเป็นไทย พร้อม retry กรณีแปลไม่สำเร็จ
    """
    translator = Translator()
    for i in range(retries):
        try:
            # หน่วงเวลาเล็กน้อยระหว่าง retry
            if i > 0:
                time.sleep(1)
            result = translator.translate(text, src='en', dest='th')
            if result and result.text:
                return result.text
        except Exception as e:
            print(f'Translation attempt {i+1} failed: {e}')
            if i == retries - 1:  # ถ้าเป็นครั้งสุดท้ายแล้วยังไม่สำเร็จ
                return f"[ไม่สามารถแปลได้: {text}]"
    return f"[ไม่สามารถแปลได้: {text}]"

def get_latest_news() -> str | None:
    """ดึงข่าวเศรษฐกิจล่าสุดจาก Finnhub API และแปลเป็นภาษาไทยก่อนส่งออก"""
    if not FINNHUB_API_KEY:
        raise ValueError('Missing FINNHUB_API_KEY in environment variables')
    url = f'https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_list = response.json()
        if isinstance(news_list, list) and news_list:
            latest = news_list[0]
            headline = latest.get('headline', 'ไม่มีหัวข้อข่าว')
            summary = latest.get('summary', '')
            news_url = latest.get('url', '')

            # แปล headline และ summary ก่อนส่งออก
            headline_th = translate_text(headline)
            summary_th = translate_text(summary)

            news_message = (
                f"ข่าวล่าสุด (EN): {headline}\n"
                f"ข่าวล่าสุด (TH): {headline_th}\n\n"
                f"เนื้อหา (EN): {summary}\n"
                f"เนื้อหา (TH): {summary_th}\n\n"
                f"อ่านต่อ: {news_url}"
            )
            return news_message
        return None
    except Exception as e:
        print(f'Error fetching news: {e}')
        return None
