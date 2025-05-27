# signal_alert.py
# ระบบแจ้งเตือนสัญญาณซื้อขาย XAUUSD ด้วย Python

import requests
import os
from dotenv import load_dotenv
import time

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
GOLDAPI_KEY = os.getenv('GOLDAPI_KEY')

# ระดับราคาตัวอย่างสำหรับแจ้งเตือน
ALERT_PRICE = 2400.0  # ตัวอย่าง: แจ้งเตือนเมื่อราคาทองทะลุ 2400 USD

# ใช้ goldapi.io แทน finnhub

# --- Alpha Vantage ---
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
def get_xauusd_price_alpha():
    if not ALPHA_VANTAGE_KEY:
        return None
    url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=USD&apikey={ALPHA_VANTAGE_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        rate = data.get('Realtime Currency Exchange Rate', {}).get('5. Exchange Rate')
        if rate:
            return float(rate)
    except Exception as e:
        print(f'Error fetching Alpha Vantage: {e}')
    return None

# --- FreeForexAPI ---
def get_xauusd_price_freeforex():
    url = 'https://www.freeforexapi.com/api/live?pairs=XAUUSD'
    try:
        response = requests.get(url)
        data = response.json()
        rate = data.get('rates', {}).get('XAUUSD', {}).get('rate')
        if rate:
            return float(rate)
    except Exception as e:
        print(f'Error fetching FreeForexAPI: {e}')
    return None

# --- GoldAPI ---
def get_xauusd_price_goldapi():
    url = 'https://www.goldapi.io/api/XAU/USD'
    headers = {
        'x-access-token': GOLDAPI_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        print('GoldAPI response:', data)
        return data.get('price')
    except Exception as e:
        print(f'Error fetching GoldAPI: {e}')
        return None

# --- Finnhub (ข่าว) ---
def get_latest_news():
    url = f'https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}'
    try:
        response = requests.get(url)
        news_list = response.json()
        if isinstance(news_list, list) and len(news_list) > 0:
            latest = news_list[0]
            headline = latest.get('headline', 'ไม่มีหัวข้อข่าว')
            summary = latest.get('summary', '')
            url = latest.get('url', '')
            message = f"ข่าวล่าสุด: {headline}\n{summary}\nอ่านต่อ: {url}"
            return message
        else:
            return None
    except Exception as e:
        print(f'Error fetching news: {e}')
        return None

# --- รวม logic เลือก API ตามลำดับความสำคัญและ quota ---
def get_xauusd_price_smart():
    # 1. ใช้ FreeForexAPI ก่อน (ไม่ต้องสมัคร, ไม่จำกัด quota)
    price = get_xauusd_price_freeforex()
    if price:
        print(f'FreeForexAPI: {price}')
        return price, "FreeForexAPI"
    # 2. ใช้ GoldAPI (100 ครั้ง/วัน)
    price = get_xauusd_price_goldapi()
    if price:
        print(f'GoldAPI: {price}')
        return price, "GoldAPI"
    # 3. ใช้ Alpha Vantage (500 ครั้ง/วัน)
    price = get_xauusd_price_alpha()
    if price:
        print(f'Alpha Vantage: {price}')
        return price, "AlphaVantage"
    # ถ้าไม่ได้เลย
    return None, None

def send_telegram_alert(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    response = requests.post(url, data=data)
    return response.json()

# --- Main ---
def main():
    price, source = get_xauusd_price_smart()
    if price:
        print(f'ราคาทอง XAUUSD ล่าสุด ({source}): {price}')
        if price > ALERT_PRICE:
            send_telegram_alert(f'ราคาทอง XAUUSD ทะลุ {ALERT_PRICE} USD แล้ว!\nราคาปัจจุบัน: {price} (source: {source})')
        else:
            print('ยังไม่ถึงจุดแจ้งเตือน')
    else:
        print('ไม่สามารถดึงราคาทองได้จากทุกแหล่ง')

    # แจ้งข่าวล่าสุด (Finnhub quota สูง)
    news_message = get_latest_news()
    if news_message:
        send_telegram_alert(news_message)
    else:
        print('ไม่สามารถดึงข่าวล่าสุดได้')

if __name__ == '__main__':
    main()
