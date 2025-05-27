import requests
import os
from dotenv import load_dotenv

load_dotenv()

GOLDAPI_KEY = os.getenv('GOLDAPI_KEY')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

def get_xauusd_price_freeforex() -> float | None:
    """ดึงราคาทอง XAUUSD จาก FreeForexAPI (ไม่มี key, ฟรี)"""
    url = 'https://www.freeforexapi.com/api/live?pairs=XAUUSD'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        rate = data.get('rates', {}).get('XAUUSD', {}).get('rate')
        if rate:
            return float(rate)
    except Exception as e:
        print(f'Error fetching FreeForexAPI: {e}')
    return None

def get_xauusd_price_goldapi() -> float | None:
    """ดึงราคาทอง XAUUSD จาก GoldAPI (ต้องมี key)"""
    if not GOLDAPI_KEY:
        raise ValueError('Missing GOLDAPI_KEY in environment variables')
    url = 'https://www.goldapi.io/api/XAU/USD'
    headers = {
        'x-access-token': GOLDAPI_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('price')
    except Exception as e:
        print(f'Error fetching GoldAPI: {e}')
        return None

def get_xauusd_price_alpha() -> float | None:
    """ดึงราคาทอง XAUUSD จาก Alpha Vantage (ต้องมี key)"""
    if not ALPHA_VANTAGE_KEY:
        raise ValueError('Missing ALPHA_VANTAGE_KEY in environment variables')
    url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=USD&apikey={ALPHA_VANTAGE_KEY}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        rate = data.get('Realtime Currency Exchange Rate', {}).get('5. Exchange Rate')
        if rate:
            return float(rate)
    except Exception as e:
        print(f'Error fetching Alpha Vantage: {e}')
    return None

def get_xauusd_price_smart() -> tuple[float | None, str | None]:
    """เลือก API ที่เหมาะสมที่สุดสำหรับราคาทอง XAUUSD"""
    price = get_xauusd_price_freeforex()
    if price:
        return price, "FreeForexAPI"
    price = get_xauusd_price_goldapi()
    if price:
        return price, "GoldAPI"
    price = get_xauusd_price_alpha()
    if price:
        return price, "AlphaVantage"
    return None, None
