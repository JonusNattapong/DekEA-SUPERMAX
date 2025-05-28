import os
import logging
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional
from dotenv import load_dotenv
from src.utils.news_utils import sentiment_analysis

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SENTIMENT_DB_FILE = "sentiment_history.csv"
SENTIMENT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', SENTIMENT_DB_FILE)

# Sentiment score mapping
SENTIMENT_SCORES = {
    'bullish': 1.0,
    'neutral': 0.0,
    'bearish': -1.0
}

def track_sentiment(news_text: str, symbol: str, source: str = "news") -> Dict[str, Union[str, float]]:
    """
    วิเคราะห์ sentiment จากข่าวและบันทึกลงฐานข้อมูลเพื่อติดตามเทรนด์
    
    Args:
        news_text: ข้อความข่าวที่ต้องการวิเคราะห์
        symbol: สัญลักษณ์ของเครื่องมือทางการเงิน (เช่น 'XAUUSD')
        source: แหล่งที่มาของข่าว
    
    Returns:
        ข้อมูล sentiment และสถานะการบันทึก
    """
    # วิเคราะห์ sentiment ด้วย AI
    sentiment = sentiment_analysis(news_text)
    
    # แปลง sentiment เป็นค่าตัวเลข
    sentiment_text = sentiment.lower()
    sentiment_score = 0.0
    
    for keyword, score in SENTIMENT_SCORES.items():
        if keyword in sentiment_text:
            sentiment_score = score
            break
    
    # สร้างระเบียนข้อมูล
    timestamp = datetime.now()
    record = {
        'timestamp': timestamp.isoformat(),
        'symbol': symbol.upper(),
        'sentiment': sentiment,
        'sentiment_score': sentiment_score,
        'source': source,
        'headline': news_text[:100] + '...' if len(news_text) > 100 else news_text
    }
    
    # บันทึกลง DataFrame
    try:
        if os.path.exists(SENTIMENT_DB_PATH):
            df = pd.read_csv(SENTIMENT_DB_PATH)
        else:
            df = pd.DataFrame(columns=['timestamp', 'symbol', 'sentiment', 'sentiment_score', 'source', 'headline'])
        
        # เพิ่มข้อมูลใหม่
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        
        # บันทึกลงไฟล์
        df.to_csv(SENTIMENT_DB_PATH, index=False)
        logger.info(f"Recorded sentiment for {symbol}: {sentiment}")
        
        record['status'] = 'saved'
    except Exception as e:
        logger.error(f"Error saving sentiment record: {e}")
        record['status'] = f"error: {str(e)}"
    
    return record

def get_sentiment_trend(symbol: str, days: int = 7) -> Dict[str, Union[str, float, List]]:
    """
    ดึงข้อมูลเทรนด์ sentiment ของสัญลักษณ์ที่ระบุในช่วงเวลาที่กำหนด
    
    Args:
        symbol: สัญลักษณ์ของเครื่องมือทางการเงิน (เช่น 'XAUUSD')
        days: จำนวนวันย้อนหลังที่ต้องการวิเคราะห์
    
    Returns:
        ข้อมูลเทรนด์ sentiment
    """
    symbol = symbol.upper()
    
    try:
        if not os.path.exists(SENTIMENT_DB_PATH):
            return {
                'symbol': symbol,
                'trend': 'NEUTRAL',
                'trend_score': 0.0,
                'confidence': 0.0,
                'records_count': 0,
                'message': 'No sentiment data available'
            }
        
        # อ่านข้อมูลจากไฟล์
        df = pd.read_csv(SENTIMENT_DB_PATH)
        
        # กรองข้อมูลตามสัญลักษณ์
        df = df[df['symbol'] == symbol]
        
        # แปลงคอลัมน์ timestamp เป็น datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # กรองข้อมูลตามช่วงเวลา
        start_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= start_date]
        
        # ถ้าไม่มีข้อมูล
        if len(df) == 0:
            return {
                'symbol': symbol,
                'trend': 'NEUTRAL',
                'trend_score': 0.0,
                'confidence': 0.0,
                'records_count': 0,
                'message': f'No sentiment data for {symbol} in the last {days} days'
            }
        
        # คำนวณค่าเฉลี่ย sentiment score
        avg_score = df['sentiment_score'].mean()
        
        # คำนวณความเชื่อมั่น (ขึ้นอยู่กับจำนวนข้อมูล)
        confidence = min(len(df) / 10, 1.0)  # 10 ระเบียนขึ้นไป = ความเชื่อมั่น 100%
        
        # กำหนดเทรนด์จากค่าเฉลี่ย
        if avg_score > 0.3:
            trend = 'BULLISH'
        elif avg_score < -0.3:
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        # สร้างข้อมูลเทรนด์แยกตามวัน
        df['date'] = df['timestamp'].dt.date
        daily_trends = df.groupby('date')['sentiment_score'].mean().reset_index()
        daily_trends['date'] = daily_trends['date'].astype(str)
        
        # แปลง DataFrame เป็น list of dict
        daily_data = daily_trends.to_dict('records')
        
        return {
            'symbol': symbol,
            'trend': trend,
            'trend_score': avg_score,
            'confidence': confidence,
            'records_count': len(df),
            'daily_trends': daily_data,
            'days_analyzed': days
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment trend: {e}")
        return {
            'symbol': symbol,
            'trend': 'ERROR',
            'trend_score': 0.0,
            'confidence': 0.0,
            'message': str(e)
        }

def format_sentiment_report(trend_data: Dict[str, Union[str, float, List]]) -> str:
    """
    สร้างรายงานเทรนด์ sentiment ในรูปแบบข้อความ
    
    Args:
        trend_data: ข้อมูลเทรนด์ sentiment จาก get_sentiment_trend
    
    Returns:
        ข้อความรายงานสรุปเทรนด์ sentiment
    """
    if 'message' in trend_data and trend_data.get('records_count', 0) == 0:
        return f"""
🔍 Sentiment Analysis: {trend_data['symbol']}
ℹ️ Status: {trend_data['message']}
"""
    
    # กำหนดอิโมจิตามเทรนด์
    trend_emoji = '📈' if trend_data['trend'] == 'BULLISH' else ('📉' if trend_data['trend'] == 'BEARISH' else '➡️')
    
    # สร้างกราฟแท่งอย่างง่ายสำหรับเทรนด์รายวัน
    daily_chart = ""
    if 'daily_trends' in trend_data and trend_data['daily_trends']:
        for day_data in trend_data['daily_trends']:
            score = day_data['sentiment_score']
            bar = '🟢' if score > 0.3 else ('🔴' if score < -0.3 else '⚪')
            daily_chart += f"   {day_data['date']}: {bar} ({score:.2f})\n"
    
    confidence_percent = int(trend_data['confidence'] * 100)
    
    return f"""
🔍 Sentiment Analysis: {trend_data['symbol']}
{trend_emoji} Overall Trend: {trend_data['trend']} (Score: {trend_data['trend_score']:.2f})
📊 Confidence: {confidence_percent}% (based on {trend_data['records_count']} data points)
📅 Period: Last {trend_data['days_analyzed']} days

📈 Daily Trend:
{daily_chart}
"""

# Example usage
if __name__ == "__main__":
    # Test track_sentiment
    sample_news = "Gold prices rose as investors sought safe-haven assets amid economic uncertainty."
    track_sentiment(sample_news, "XAUUSD")
    
    # Test get_sentiment_trend
    trend = get_sentiment_trend("XAUUSD")
    print(format_sentiment_report(trend))
