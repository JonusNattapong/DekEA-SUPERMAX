"""
Performance System Demo - ตัวอย่างการใช้งานระบบ Report Winrate
"""

import sys
import os
from datetime import datetime, timedelta
import random

# เพิ่ม path เพื่อ import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.performance_tracker import PerformanceTracker, TradeRecord, create_tracker, add_sample_trades
from src.utils.trading_monitor import TradingMonitor, create_monitoring_system
from src.utils.performance_reporter import EnhancedTradingMonitor, create_enhanced_monitor

def demo_basic_performance_tracking():
    """Demo การใช้งาน Performance Tracker พื้นฐาน"""
    print("=" * 60)
    print("🎯 DEMO: Basic Performance Tracking")
    print("=" * 60)
    
    # สร้าง tracker
    tracker = create_tracker("demo_data")
    
    # เพิ่มข้อมูลตัวอย่าง
    print("📊 กำลังเพิ่มข้อมูลการเทรดตัวอย่าง...")
    add_sample_trades(tracker)
    
    # แสดงรายงาน
    print("\n📈 รายงานผลการเทรด:")
    tracker.print_formatted_report("both")
    
    # สร้างกราฟ
    print("\n📊 กำลังสร้างกราฟ...")
    try:
        tracker.create_performance_chart("demo_data/demo_chart.png")
        print("✅ สร้างกราฟสำเร็จ: demo_data/demo_chart.png")
    except Exception as e:
        print(f"❌ ไม่สามารถสร้างกราฟได้: {e}")

def demo_trading_monitor():
    """Demo การใช้งาน Trading Monitor"""
    print("\n" + "=" * 60)
    print("🔍 DEMO: Trading Monitor")
    print("=" * 60)
    
    # สร้าง monitor
    monitor = create_monitoring_system("demo_data")
    
    # เปิดการเทรดทดสอบ
    print("🔓 เปิดการเทรดทดสอบ...")
    
    trade_id1 = monitor.open_trade(
        symbol="XAUUSD",
        entry_price=2050.0,
        position_type="LONG",
        position_size=0.1,
        strategy_name="Demo_Strategy",
        stop_loss=2030.0,
        take_profit=2080.0,
        notes="การเทรดทดสอบ 1"
    )
    
    trade_id2 = monitor.open_trade(
        symbol="XAUUSD",
        entry_price=2055.0,
        position_type="SHORT",
        position_size=0.05,
        strategy_name="Demo_Strategy",
        stop_loss=2070.0,
        take_profit=2040.0,
        notes="การเทรดทดสอบ 2"
    )
    
    print(f"✅ เปิดการเทรด: {trade_id1}")
    print(f"✅ เปิดการเทรด: {trade_id2}")
    
    # แสดงการเทรดที่เปิดอยู่
    active_trades = monitor.get_active_trades()
    print(f"\n🔓 การเทรดที่เปิดอยู่: {len(active_trades)} รายการ")
    
    # ปิดการเทรดบางรายการ
    print("\n🔒 ปิดการเทรดทดสอบ...")
    
    # ปิดการเทรดที่ 1 ด้วยกำไร
    monitor.close_trade(trade_id1, 2075.0, "Take Profit Test")
    
    # ปิดการเทรดที่ 2 ด้วยขาดทุน
    monitor.close_trade(trade_id2, 2065.0, "Stop Loss Test")
    
    # แสดงสรุปรายวัน
    print("\n📊 สรุปการเทรดวันนี้:")
    daily_summary = monitor.get_daily_summary()
    
    for key, value in daily_summary.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")

def demo_enhanced_monitor_with_reporting():
    """Demo การใช้งาน Enhanced Monitor พร้อมการส่งรายงาน"""
    print("\n" + "=" * 60)
    print("📤 DEMO: Enhanced Monitor with Telegram Reporting")
    print("=" * 60)
    
    # สร้าง enhanced monitor (ปิดการส่งรายงานอัตโนมัติสำหรับ demo)
    monitor = create_enhanced_monitor("demo_data", enable_reporting=False)
    
    # เพิ่มข้อมูลการเทรดตัวอย่างเพิ่มเติม
    print("📊 เพิ่มข้อมูลการเทรดเพิ่มเติม...")
    
    # สร้างการเทรดตัวอย่างในช่วงสัปดาห์ที่ผ่านมา
    base_date = datetime.now() - timedelta(days=7)
    
    for i in range(10):
        trade_date = base_date + timedelta(days=random.randint(0, 7))
        
        # เปิดการเทรด
        trade_id = monitor.open_trade(
            symbol="XAUUSD",
            entry_price=2000 + random.uniform(-30, 30),
            position_type=random.choice(["LONG", "SHORT"]),
            position_size=0.1,
            strategy_name=f"Demo_Strategy_{i%3 + 1}",
            notes=f"การเทรดตัวอย่าง {i+1}"
        )
        
        # ปิดการเทรดทันที (สำหรับ demo)
        exit_price = 2000 + random.uniform(-40, 40)
        monitor.close_trade(trade_id, exit_price, "Demo Close")
    
    print("✅ เพิ่มข้อมูลการเทรดสำเร็จ")
    
    # ทดสอบการส่งรายงาน (จะแสดงข้อความแทนการส่งจริง)
    print("\n📤 ทดสอบรายงานต่าง ๆ:")
    
    # ลองสร้างรายงานรายวัน
    try:
        print("   📅 รายงานรายวัน...")
        if hasattr(monitor, 'reporter') and monitor.reporter:
            # แสดงเฉพาะ format ของรายงาน
            summary = monitor.get_daily_summary()
            formatted_msg = monitor.reporter._format_daily_summary(summary)
            print("   ✅ สร้างรายงานรายวันสำเร็จ")
            print("   📝 ตัวอย่างข้อความ:")
            print("   " + "\n   ".join(formatted_msg.split("\n")[:10]))  # แสดงแค่ 10 บรรทัดแรก
        else:
            print("   ⚠️ Reporter ไม่พร้อมใช้งาน")
    except Exception as e:
        print(f"   ❌ Error creating daily report: {e}")
    
    # ลองสร้างรายงานรายสัปดาห์
    try:
        print("\n   📊 รายงานรายสัปดาห์...")
        weekly_reports = monitor.tracker.get_weekly_report(2)
        if weekly_reports:
            print(f"   ✅ ได้รายงาน {len(weekly_reports)} สัปดาห์")
            for report in weekly_reports:
                print(f"      📈 {report.period}: Winrate {report.winrate:.1f}%, PnL {report.total_pnl:.2f}")
        else:
            print("   ⚠️ ไม่มีข้อมูลสำหรับรายงานรายสัปดาห์")
    except Exception as e:
        print(f"   ❌ Error creating weekly report: {e}")

def demo_integration_with_algorithm_manager():
    """Demo การผสานรวมกับ Algorithm Manager"""
    print("\n" + "=" * 60)
    print("🤖 DEMO: Integration with Algorithm Manager")
    print("=" * 60)
    
    try:
        from src.utils.trading_monitor import integrate_with_algorithm_manager
        
        # สร้าง monitor
        monitor = create_monitoring_system("demo_data")
        
        # สร้างข้อมูลจำลองจาก Algorithm Manager
        mock_recommendation = {
            'signal': 'BUY',
            'current_price': 2055.5,
            'confidence': 0.75,
            'individual_signals': {
                'MA_Crossover': 'BUY',
                'RSI_Strategy': 'HOLD', 
                'MACD_Strategy': 'BUY'
            },
            'risk_metrics': {
                'stop_loss': 2035.0,
                'take_profit': 2085.0,
                'position_size': 0.1
            }
        }
        
        print("📊 ข้อมูลจำลองจาก Algorithm Manager:")
        print(f"   🎯 Signal: {mock_recommendation['signal']}")
        print(f"   💰 Price: {mock_recommendation['current_price']}")
        print(f"   📈 Confidence: {mock_recommendation['confidence']}")
        
        # ใช้ integration function
        print("\n🔄 เชื่อมต่อกับ Algorithm Manager...")
        trade_id = integrate_with_algorithm_manager(
            monitor=monitor,
            recommendation=mock_recommendation,
            symbol="XAUUSD",
            position_size=0.1
        )
        
        if trade_id:
            print(f"✅ เปิดการเทรดสำเร็จ: {trade_id}")
            
            # ปิดการเทรดทันที (สำหรับ demo)
            monitor.close_trade(trade_id, 2070.0, "Demo Integration")
            print(f"🔒 ปิดการเทรดสำเร็จ")
        else:
            print("❌ ไม่สามารถเปิดการเทรดได้")
    
    except ImportError as e:
        print(f"❌ ไม่สามารถ import Algorithm Manager: {e}")
    except Exception as e:
        print(f"❌ Error in integration demo: {e}")

def show_file_structure():
    """แสดงโครงสร้างไฟล์ที่สร้างขึ้น"""
    print("\n" + "=" * 60)
    print("📁 ไฟล์ที่สร้างขึ้นใหม่")
    print("=" * 60)
    
    files_created = [
        "src/utils/performance_tracker.py - ระบบติดตามและวิเคราะห์ผลการเทรด",
        "src/utils/trading_monitor.py - ระบบติดตามการเทรดแบบ real-time",
        "src/utils/performance_reporter.py - ระบบส่งรายงานผ่าน Telegram",
        "src/performance_system.py - ระบบหลักที่รวมทุกอย่างเข้าด้วยกัน",
        "demo_performance_system.py - ไฟล์ demo นี้"
    ]
    
    for file_info in files_created:
        print(f"✅ {file_info}")
    
    print(f"\n📂 ข้อมูลจะถูกเก็บใน: demo_data/")
    print(f"📊 รายงานจะถูกเก็บใน: demo_data/reports/")

def main():
    """เรียกใช้ demo ทั้งหมด"""
    print("🎯 Dek Trading Signal - Performance System Demo")
    print("=" * 60)
    
    try:
        # Demo 1: Basic Performance Tracking
        demo_basic_performance_tracking()
        
        # Demo 2: Trading Monitor
        demo_trading_monitor()
        
        # Demo 3: Enhanced Monitor with Reporting
        demo_enhanced_monitor_with_reporting()
        
        # Demo 4: Integration with Algorithm Manager
        demo_integration_with_algorithm_manager()
        
        # แสดงโครงสร้างไฟล์
        show_file_structure()
        
        print("\n" + "=" * 60)
        print("🎉 Demo สำเร็จทั้งหมด!")
        print("=" * 60)
        print("\n📚 วิธีการใช้งาน:")
        print("1. import ระบบ: from src.performance_system import DekTradingSystem")
        print("2. สร้างระบบ: system = DekTradingSystem()")
        print("3. วิเคราะห์: recommendation = system.run_trading_analysis()")
        print("4. เทรด: trade_id = system.execute_trade(recommendation)")
        print("5. รายงาน: system.send_performance_report('daily')")
        
        print("\n🔔 หมายเหตุ:")
        print("- ตั้งค่า TELEGRAM_BOT_TOKEN และ TELEGRAM_CHAT_ID ใน .env")
        print("- ระบบจะส่งรายงานอัตโนมัติทุกวันเวลา 18:00")
        print("- รายงานรายสัปดาห์จะส่งทุกวันอาทิตย์เวลา 19:00")
        print("- รายงานรายเดือนจะส่งวันที่ 1 ของเดือนเวลา 20:00")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดใน demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
