import os
import logging
from datetime import datetime
import time
from dotenv import load_dotenv

from src.gold_analysis import generate_gold_summary, format_gold_report
from src.telegram_utils import send_telegram_alert
from src.news_filter import should_avoid_trading, format_news_report
from src.sentiment_tracker import get_sentiment_trend, format_sentiment_report

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL_MINUTES', '60'))  # Default: 60 minutes
ALERT_ON_CHANGE = os.getenv('ALERT_ON_SENTIMENT_CHANGE', 'True').lower() == 'true'
DAILY_REPORT_HOUR = int(os.getenv('DAILY_REPORT_HOUR', '8'))  # Default: 8:00 AM

def send_gold_report():
    """สร้างและส่งรายงานการวิเคราะห์ทองคำไปยัง Telegram"""
    try:
        logger.info("เริ่มการวิเคราะห์ทองคำ...")
        
        # ดึงข้อมูลวิเคราะห์ทองคำ
        gold_summary = generate_gold_summary()
        gold_report = format_gold_report(gold_summary)
        
        # ตรวจสอบข่าวสำคัญ
        news_status = should_avoid_trading("XAUUSD")
        if news_status['should_avoid']:
            news_report = format_news_report(news_status)
            gold_report += "\n\n" + news_report
        
        # ส่งรายงานไปยัง Telegram
        send_telegram_alert(gold_report)
        logger.info("ส่งรายงานทองคำไปยัง Telegram เรียบร้อยแล้ว")
        
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างหรือส่งรายงานทองคำ: {e}")
        return False

def check_sentiment_change():
    """ตรวจสอบการเปลี่ยนแปลง sentiment และแจ้งเตือนหากมีการเปลี่ยนแปลงสำคัญ"""
    try:
        # ดึงข้อมูล sentiment ล่าสุด
        current_trend = get_sentiment_trend("XAUUSD", days=1)
        previous_trend = get_sentiment_trend("XAUUSD", days=7)
        
        # ตรวจสอบการเปลี่ยนแปลง
        if current_trend.get('trend') != previous_trend.get('trend'):
            alert_msg = f"""
🚨 XAUUSD Sentiment Change Alert 🚨

เทรนด์ Sentiment ล่าสุด: {current_trend.get('trend')}
เทรนด์ Sentiment ก่อนหน้า: {previous_trend.get('trend')}

🔍 รายละเอียดเพิ่มเติม:
{format_sentiment_report(current_trend)}
"""
            send_telegram_alert(alert_msg)
            logger.info(f"แจ้งเตือนการเปลี่ยนแปลง sentiment จาก {previous_trend.get('trend')} เป็น {current_trend.get('trend')}")
            
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบการเปลี่ยนแปลง sentiment: {e}")
        return False

def run_daily_report():
    """ตรวจสอบและส่งรายงานประจำวันตามเวลาที่กำหนด"""
    current_hour = datetime.now().hour
    
    if current_hour == DAILY_REPORT_HOUR:
        logger.info("เริ่มสร้างรายงานประจำวัน...")
        daily_report = """
📅 XAUUSD Daily Report 📅
วันที่: {}

""".format(datetime.now().strftime("%Y-%m-%d"))

        # เพิ่มข้อมูลวิเคราะห์ทองคำ
        gold_summary = generate_gold_summary()
        gold_report = format_gold_report(gold_summary)
        daily_report += gold_report
        
        # เพิ่มข้อมูล sentiment
        sentiment_trend = get_sentiment_trend("XAUUSD", days=14)  # ดูย้อนหลัง 2 สัปดาห์
        sentiment_report = format_sentiment_report(sentiment_trend)
        daily_report += "\n\n" + sentiment_report
        
        # ส่งรายงานไปยัง Telegram
        send_telegram_alert(daily_report)
        logger.info("ส่งรายงานประจำวันเรียบร้อยแล้ว")

def main():
    """ฟังก์ชันหลักสำหรับรันบอทวิเคราะห์ทองคำ"""
    logger.info("เริ่มต้นระบบวิเคราะห์ทองคำ DekTradingSignal Gold Bot")
    
    # ส่งรายงานครั้งแรกเมื่อเริ่มระบบ
    send_gold_report()
    
    last_daily_report_day = datetime.now().day
    
    try:
        while True:
            # ตรวจสอบรายงานประจำวัน
            current_day = datetime.now().day
            if current_day != last_daily_report_day:
                run_daily_report()
                last_daily_report_day = current_day
            
            # ตรวจสอบการเปลี่ยนแปลง sentiment
            if ALERT_ON_CHANGE:
                check_sentiment_change()
            
            # รอจนถึงรอบถัดไป
            logger.info(f"รออัปเดตถัดไปใน {UPDATE_INTERVAL} นาที...")
            time.sleep(UPDATE_INTERVAL * 60)
            
            # ส่งรายงานประจำรอบ
            send_gold_report()
            
    except KeyboardInterrupt:
        logger.info("ผู้ใช้หยุดการทำงานของระบบ")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาด: {e}")
        # ส่งข้อความแจ้งเตือนเมื่อระบบมีปัญหา
        send_telegram_alert(f"⚠️ Gold Bot Error: {e}")

if __name__ == "__main__":
    main()
