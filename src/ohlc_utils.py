import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
TWELVE_DATA_KEY = os.getenv('TWELVE_DATA_KEY')

def fetch_ohlc_alphavantage() -> pd.DataFrame | None:
    """ดึงข้อมูล OHLC XAUUSD จาก Alpha Vantage (interval 60min)"""
    if not ALPHA_VANTAGE_KEY:
        raise ValueError('Missing ALPHA_VANTAGE_KEY in environment variables')
    url = f'https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=XAU&to_symbol=USD&interval=60min&apikey={ALPHA_VANTAGE_KEY}&outputsize=compact'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        ts = data.get('Time Series FX (60min)', {})
        if not ts:
            return None
        df = pd.DataFrame(ts).T
        df = df.rename(columns={
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
        })
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        print(f'Error fetching OHLC from Alpha Vantage: {e}')
        return None

def fetch_ohlc_twelvedata(symbol: str = 'XAU/USD', interval: str = '1h', outputsize: int = 30) -> pd.DataFrame | None:
    """ดึงข้อมูล OHLC จาก Twelve Data API"""
    if not TWELVE_DATA_KEY:
        raise ValueError('Missing TWELVE_DATA_KEY in environment variables')
    url = f'https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_KEY}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'values' not in data:
            return None
        df = pd.DataFrame(data['values'])
        df = df.rename(columns={
            'datetime': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
        })
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df = df[['Open', 'High', 'Low', 'Close']].astype(float)
        df = df.sort_index()
        return df
    except Exception as e:
        print(f'Error fetching OHLC from Twelve Data: {e}')
        return None
