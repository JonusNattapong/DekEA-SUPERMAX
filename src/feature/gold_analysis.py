import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Union, Optional, Tuple

from src.price_utils import get_xauusd_price_smart
from src.news_utils import sentiment_analysis, get_latest_news
from src.sentiment_tracker import get_sentiment_trend
from src.news_filter import should_avoid_trading
from src.risk_utils import calculate_risk_metrics, format_risk_report

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gold-specific constants
GOLD_PIP_VALUE = 0.1  # 1 pip = $0.10 for standard lot (100oz)
GOLD_MIN_TICK = 0.01  # Minimum price movement in USD
GOLD_STANDARD_LOT = 100  # 100 troy ounces

# Important support/resistance zones (to be updated regularly)
GOLD_KEY_LEVELS = {
    'major_support': [1800, 1765, 1680],
    'major_resistance': [2000, 2050, 2075],
    'recent_support': [],  # To be filled dynamically
    'recent_resistance': []  # To be filled dynamically
}

# Gold market trading hours (when liquidity is highest)
GOLD_OPTIMAL_TRADING_HOURS = [
    # Format: (start_hour, end_hour) in UTC
    (8, 16),  # London session
    (13, 21),  # New York session
]

def is_gold_market_active() -> bool:
    """
    ตรวจสอบว่าตลาดทองมีสภาพคล่องสูงในขณะนี้หรือไม่
    
    Returns:
        bool: True ถ้าอยู่ในช่วงเวลาที่เหมาะสมสำหรับการเทรดทอง
    """
    current_time = datetime.utcnow()
    current_hour = current_time.hour
    current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday
    
    # ตลาดปิดในวันเสาร์และวันอาทิตย์
    if current_weekday >= 5:  # Saturday and Sunday
        return False
        
    # ตรวจสอบว่าอยู่ในช่วงเวลาที่มีสภาพคล่องสูงหรือไม่
    for start_hour, end_hour in GOLD_OPTIMAL_TRADING_HOURS:
        if start_hour <= current_hour < end_hour:
            return True
            
    return False

def update_key_levels(historical_data: pd.DataFrame) -> None:
    """
    อัปเดตระดับ support/resistance ล่าสุดจากข้อมูลย้อนหลัง
    
    Args:
        historical_data: DataFrame ของข้อมูลราคาย้อนหลัง
    """
    # ตรวจหา swing highs และ swing lows
    if len(historical_data) < 10:
        logger.warning("Insufficient data to identify key levels")
        return
        
    # ใช้อัลกอริทึมอย่างง่ายเพื่อหา local maxima/minima
    window = 5  # พิจารณา 5 แท่งก่อนและหลัง
    
    highs = []
    lows = []
    
    for i in range(window, len(historical_data) - window):
        # ตรวจหา swing high
        if all(historical_data['high'][i] > historical_data['high'][i-j] for j in range(1, window+1)) and \
           all(historical_data['high'][i] > historical_data['high'][i+j] for j in range(1, window+1)):
            highs.append(historical_data['high'][i])
            
        # ตรวจหา swing low
        if all(historical_data['low'][i] < historical_data['low'][i-j] for j in range(1, window+1)) and \
           all(historical_data['low'][i] < historical_data['low'][i+j] for j in range(1, window+1)):
            lows.append(historical_data['low'][i])
    
    # อัปเดต key levels
    GOLD_KEY_LEVELS['recent_support'] = sorted(lows[-5:]) if lows else []
    GOLD_KEY_LEVELS['recent_resistance'] = sorted(highs[-5:]) if highs else []
    
    logger.info(f"Updated recent support levels: {GOLD_KEY_LEVELS['recent_support']}")
    logger.info(f"Updated recent resistance levels: {GOLD_KEY_LEVELS['recent_resistance']}")

def analyze_gold_correlations() -> Dict[str, float]:
    """
    วิเคราะห์ความสัมพันธ์ของทองกับสินทรัพย์อื่นๆ เช่น USD, Bond Yields
    
    Returns:
        ข้อมูลความสัมพันธ์กับสินทรัพย์หลักที่ส่งผลต่อราคาทอง
    """
    # ในระบบจริงควรดึงข้อมูลจริงจาก API
    # เช่น US Dollar Index, 10Y Treasury Yield, S&P500
    
    # ตัวอย่างข้อมูลสมมติ
    correlations = {
        'USD_Index': -0.82,  # ทองมักเคลื่อนไหวตรงข้ามกับดอลลาร์
        'US_10Y_Yield': -0.65,  # ทองมักเคลื่อนไหวตรงข้ามกับ bond yields
        'SP500': 0.25,  # ความสัมพันธ์กับตลาดหุ้นไม่แน่นอน
        'Inflation_Expectation': 0.70,  # ทองเป็นเครื่องป้องกันเงินเฟ้อ
        'VIX': 0.55  # ทองมักได้ประโยชน์เมื่อความผันผวนสูง
    }
    
    return correlations

def check_gold_specific_events() -> List[Dict[str, str]]:
    """
    ตรวจสอบเหตุการณ์เฉพาะที่กระทบกับราคาทอง
    
    Returns:
        รายการเหตุการณ์ที่อาจส่งผลต่อราคาทอง
    """
    # ในระบบจริงควรดึงข้อมูลจาก economic calendar API หรือแหล่งข่าวเฉพาะทาง
    
    # ตัวอย่างเหตุการณ์ที่ส่งผลต่อทอง
    gold_events = [
        {
            'event': 'FOMC Interest Rate Decision',
            'impact': 'high',
            'date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'description': 'การเปลี่ยนแปลงอัตราดอกเบี้ยของ Fed ส่งผลอย่างมากต่อราคาทอง'
        },
        {
            'event': 'US CPI Data',
            'impact': 'high',
            'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'description': 'ข้อมูลเงินเฟ้อส่งผลต่อการคาดการณ์ทิศทางดอกเบี้ยและราคาทอง'
        },
        {
            'event': 'Central Bank Gold Reserves Report',
            'impact': 'medium',
            'date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'description': 'การเปลี่ยนแปลงทุนสำรองทองคำของธนาคารกลางส่งผลต่อความต้องการทองในระยะยาว'
        }
    ]
    
    return gold_events

def calculate_gold_position_size(account_balance: float, risk_percent: float, 
                               entry_price: float, stop_loss: float) -> float:
    """
    คำนวณขนาด position สำหรับการเทรดทองคำโดยเฉพาะ
    
    Args:
        account_balance: ยอดเงินในบัญชี (USD)
        risk_percent: เปอร์เซ็นต์ความเสี่ยงที่ยอมรับได้ (%)
        entry_price: ราคาเข้าซื้อ/ขาย
        stop_loss: ราคา Stop Loss
        
    Returns:
        ขนาด position ในหน่วย lot (1 lot = 100 oz)
    """
    # จำนวนเงินที่ยอมรับความเสี่ยงได้
    risk_amount = account_balance * (risk_percent / 100)
    
    # คำนวณความเสี่ยงต่อ oz
    risk_per_oz = abs(entry_price - stop_loss)
    
    # จำนวน oz ที่เหมาะสม
    if risk_per_oz > 0:
        oz_quantity = risk_amount / risk_per_oz
        lot_size = oz_quantity / GOLD_STANDARD_LOT  # แปลงเป็น lot
        return round(lot_size, 2)  # ปัดเศษให้เป็น 2 ตำแหน่ง
    return 0.01  # ค่าขั้นต่ำ

def generate_gold_summary() -> Dict[str, any]:
    """
    สร้างรายงานสรุปข้อมูลทั้งหมดที่เกี่ยวข้องกับทองคำ
    
    Returns:
        รายงานสรุปและคำแนะนำการเทรดทองคำ
    """
    # 1. ดึงราคาปัจจุบัน
    current_price, price_source = get_xauusd_price_smart()
    if not current_price:
        return {"error": "ไม่สามารถดึงราคาทองคำได้"}
    
    # 2. วิเคราะห์ sentiment จากข่าว
    news = get_latest_news()
    news_sentiment = sentiment_analysis(news) if news else "Neutral"
    
    # 3. ตรวจสอบเทรนด์ sentiment ระยะยาว
    sentiment_trend = get_sentiment_trend("XAUUSD", days=7)
    
    # 4. ตรวจสอบข่าวสำคัญ
    news_status = should_avoid_trading("XAUUSD")
    
    # 5. วิเคราะห์ความสัมพันธ์กับสินทรัพย์อื่น
    correlations = analyze_gold_correlations()
    
    # 6. ตรวจสอบเหตุการณ์เฉพาะทอง
    gold_events = check_gold_specific_events()
    
    # 7. ตรวจสอบช่วงเวลาการเทรด
    market_active = is_gold_market_active()
    
    # 8. คำนวณ position size สำหรับการเทรดทอง (ตัวอย่าง)
    account_balance = 10000  # ตัวอย่างเงินในบัญชี
    risk_percent = 1.0
    # สมมติระยะห่าง SL 20 เหรียญ
    suggested_sl = current_price - 20 if news_sentiment.lower() == "bullish" else current_price + 20
    position_size = calculate_gold_position_size(account_balance, risk_percent, current_price, suggested_sl)
    
    # 9. สร้างคำแนะนำการเทรด
    if news_status['should_avoid']:
        trading_recommendation = "WAIT - มีข่าวสำคัญที่อาจทำให้ตลาดผันผวน"
    elif not market_active:
        trading_recommendation = "WAIT - อยู่นอกช่วงเวลาที่ตลาดมีสภาพคล่องสูง"
    else:
        # ตัดสินใจจาก sentiment และตัวแปรอื่นๆ
        if news_sentiment.lower() == "bullish" and sentiment_trend.get('trend') == "BULLISH":
            trading_recommendation = "BUY - sentiment เป็นบวกทั้งระยะสั้นและระยะยาว"
        elif news_sentiment.lower() == "bearish" and sentiment_trend.get('trend') == "BEARISH":
            trading_recommendation = "SELL - sentiment เป็นลบทั้งระยะสั้นและระยะยาว"
        else:
            trading_recommendation = "NEUTRAL - รอสัญญาณที่ชัดเจนกว่านี้"
    
    # สร้างรายงานสรุป
    summary = {
        "current_price": current_price,
        "price_source": price_source,
        "datetime": datetime.now().isoformat(),
        "news_sentiment": news_sentiment,
        "sentiment_trend": sentiment_trend.get('trend', "NEUTRAL"),
        "sentiment_confidence": sentiment_trend.get('confidence', 0),
        "should_avoid_trading": news_status['should_avoid'],
        "market_active": market_active,
        "trading_recommendation": trading_recommendation,
        "suggested_position_size": position_size,
        "correlations": correlations,
        "upcoming_gold_events": gold_events,
        "key_levels": GOLD_KEY_LEVELS
    }
    
    return summary

def format_gold_report(summary: Dict[str, any]) -> str:
    """
    จัดรูปแบบรายงานการวิเคราะห์ทองคำให้อ่านง่าย
    
    Args:
        summary: ข้อมูลสรุปจาก generate_gold_summary()
        
    Returns:
        รายงานในรูปแบบข้อความที่อ่านง่าย
    """
    if "error" in summary:
        return f"⚠️ เกิดข้อผิดพลาด: {summary['error']}"
    
    # สร้างอิโมจิตามคำแนะนำ
    recommendation_emoji = "🟢" if "BUY" in summary["trading_recommendation"] else \
                         ("🔴" if "SELL" in summary["trading_recommendation"] else "⚪")
    
    # สร้างกราฟอย่างง่ายแสดงความสัมพันธ์
    correlation_chart = ""
    for asset, corr in summary["correlations"].items():
        bar = "📈" if corr > 0 else "📉"
        correlation_chart += f"   {asset}: {bar} ({corr:+.2f})\n"
    
    # สร้างข้อความรายงาน
    report = f"""
🔆 XAUUSD (ทองคำ) - รายงานการวิเคราะห์ 🔆
⏰ เวลา: {summary["datetime"]}

💰 ราคาปัจจุบัน: ${summary["current_price"]:.2f} (จาก {summary["price_source"]})
{'✅ ตลาดมีสภาพคล่องสูง' if summary["market_active"] else '⚠️ อยู่นอกช่วงเวลาการเทรดที่เหมาะสม'}
{'⚠️ ควรหลีกเลี่ยงการเทรดเนื่องจากมีข่าวสำคัญ' if summary["should_avoid_trading"] else '✅ ไม่มีข่าวสำคัญที่ควรหลีกเลี่ยง'}

🧠 การวิเคราะห์ Sentiment:
   ข่าวล่าสุด: {summary["news_sentiment"]}
   เทรนด์ (7 วัน): {summary["sentiment_trend"]} (ความเชื่อมั่น: {int(summary["sentiment_confidence"]*100)}%)

{recommendation_emoji} คำแนะนำ: {summary["trading_recommendation"]}
💼 ขนาด Position แนะนำ: {summary["suggested_position_size"]} lot

📊 ความสัมพันธ์กับสินทรัพย์อื่น:
{correlation_chart}

📍 ระดับสำคัญ:
   แนวรับสำคัญ: {', '.join([f'${level:.2f}' for level in summary["key_levels"]["major_support"]])}
   แนวต้านสำคัญ: {', '.join([f'${level:.2f}' for level in summary["key_levels"]["major_resistance"]])}

📅 เหตุการณ์สำคัญที่กำลังจะเกิดขึ้น:
"""
    
    # เพิ่มข้อมูลเหตุการณ์
    if summary["upcoming_gold_events"]:
        for i, event in enumerate(summary["upcoming_gold_events"], 1):
            impact_marker = "🔴" if event["impact"] == "high" else ("🟠" if event["impact"] == "medium" else "🟡")
            report += f"   {i}. {event['date']} - {impact_marker} {event['event']}\n"
    else:
        report += "   ไม่มีเหตุการณ์สำคัญในเร็วๆ นี้\n"
    
    return report

# Example usage
if __name__ == "__main__":
    # Test the module
    gold_summary = generate_gold_summary()
    gold_report = format_gold_report(gold_summary)
    print(gold_report)
