# signal_alert.py
# ระบบแจ้งเตือนสัญญาณซื้อขาย XAUUSD ด้วย Python

import requests
import os
from dotenv import load_dotenv
import time
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import yfinance as yf
from src.telegram_utils import send_telegram_alert
from src.news_utils import get_latest_news
from src.price_utils import get_xauusd_price_smart
from src.ohlc_utils import fetch_ohlc_twelvedata
from src.entry_logic import is_good_buy_entry
from src.chart_utils import plot_and_send_chart_tradingview_style

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
GOLDAPI_KEY = os.getenv('GOLDAPI_KEY')

# ระดับราคาตัวอย่างสำหรับแจ้งเตือน
ALERT_PRICE = 2400.0  # ตัวอย่าง: แจ้งเตือนเมื่อราคาทองทะลุ 2400 USD

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

    # วาดกราฟและส่งไป Telegram (TradingView style)
    if price:
        ohlc_df = fetch_ohlc_twelvedata(symbol='XAU/USD', interval='1h', outputsize=30)
        if ohlc_df is not None:
            is_entry, entry_msg = is_good_buy_entry(ohlc_df, price)
            plot_and_send_chart_tradingview_style(ohlc_df, logo_path=None, symbol='XAUUSD')
            send_telegram_alert(f'สัญญาณน่าเข้าซื้อ: {entry_msg}')
        else:
            print('ไม่สามารถดึงข้อมูล OHLC จาก Twelve Data')

if __name__ == '__main__':
    main()
