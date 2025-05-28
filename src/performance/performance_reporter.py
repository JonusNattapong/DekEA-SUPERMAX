"""
Performance Reporter - ระบบส่งรายงาน Winrate ผ่าน Telegram อัตโนมัติ
"""

import os
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from src.performance.performance_tracker import PerformanceTracker, PeriodStats
from src.performance.performance_trading_monitor import TradingMonitor
from src.utils.telegram_utils import send_message_to_telegram

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceReporter:
    """ระบบส่งรายงานผลการเทรดผ่าน Telegram"""
    
    def __init__(self, monitor: TradingMonitor, auto_schedule: bool = True):
        """
        Initialize Performance Reporter
        
        Args:
            monitor: TradingMonitor instance
            auto_schedule: เปิดใช้งานการส่งรายงานอัตโนมัติ
        """
        self.monitor = monitor
        self.tracker = monitor.tracker
        
        if auto_schedule:
            self._setup_scheduled_reports()
    
    def send_daily_summary(self) -> None:
        """ส่งสรุปการเทรดรายวัน"""
        summary = self.monitor.get_daily_summary()
        
        # สร้างข้อความ
        message = self._format_daily_summary(summary)
        
        try:
            send_message_to_telegram(message)
            logger.info("✅ ส่งสรุปรายวันผ่าน Telegram สำเร็จ")
        except Exception as e:
            logger.error(f"❌ Error sending daily summary: {e}")
    
    def send_weekly_report(self) -> None:
        """ส่งรายงานรายสัปดาห์"""
        weekly_reports = self.tracker.get_weekly_report(4)  # 4 สัปดาห์ย้อนหลัง
        
        if not weekly_reports:
            logger.info("ไม่มีข้อมูลสำหรับรายงานรายสัปดาห์")
            return
        
        message = self._format_weekly_report(weekly_reports)
        
        try:
            send_message_to_telegram(message)
            logger.info("✅ ส่งรายงานรายสัปดาห์ผ่าน Telegram สำเร็จ")
        except Exception as e:
            logger.error(f"❌ Error sending weekly report: {e}")
    
    def send_monthly_report(self) -> None:
        """ส่งรายงานรายเดือน"""
        monthly_reports = self.tracker.get_monthly_report(3)  # 3 เดือนย้อนหลัง
        
        if not monthly_reports:
            logger.info("ไม่มีข้อมูลสำหรับรายงานรายเดือน")
            return
        
        message = self._format_monthly_report(monthly_reports)
        
        try:
            send_message_to_telegram(message)
            logger.info("✅ ส่งรายงานรายเดือนผ่าน Telegram สำเร็จ")
        except Exception as e:
            logger.error(f"❌ Error sending monthly report: {e}")
    
    def send_trade_alert(self, trade_id: str, action: str, details: Dict) -> None:
        """
        ส่งการแจ้งเตือนการเทรด
        
        Args:
            trade_id: รหัสการเทรด
            action: การกระทำ ('OPEN', 'CLOSE', 'UPDATE')
            details: รายละเอียดการเทรด
        """
        message = self._format_trade_alert(trade_id, action, details)
        
        try:
            send_message_to_telegram(message)
            logger.info(f"✅ ส่งการแจ้งเตือนการเทรด {action} สำเร็จ")
        except Exception as e:
            logger.error(f"❌ Error sending trade alert: {e}")
    
    def _format_daily_summary(self, summary: Dict) -> str:
        """จัดรูปแบบสรุปรายวัน"""
        date = summary['date']
        total_trades = summary['total_trades']
        winrate = summary['winrate']
        total_pnl = summary['total_pnl']
        active_trades = summary['active_trades']
        
        # เลือก emoji ตาม winrate
        if winrate >= 70:
            winrate_emoji = "🔥"
        elif winrate >= 50:
            winrate_emoji = "✅"
        elif winrate > 0:
            winrate_emoji = "⚠️"
        else:
            winrate_emoji = "❌"
        
        # เลือก emoji ตาม PnL
        if total_pnl > 0:
            pnl_emoji = "💰"
        elif total_pnl < 0:
            pnl_emoji = "📉"
        else:
            pnl_emoji = "⚖️"
        
        message = f"""
📊 **สรุปการเทรดประจำวัน**
🗓️ วันที่: {date}

📈 **ผลการเทรดวันนี้**
🔢 การเทรดทั้งหมด: {total_trades}
{winrate_emoji} Winrate: {winrate:.1f}%
{pnl_emoji} PnL รวม: {total_pnl:.2f}
🔓 การเทรดที่เปิดอยู่: {active_trades}
"""
        
        if total_trades > 0:
            winning_trades = summary['winning_trades']
            losing_trades = summary['losing_trades']
            avg_win = summary.get('avg_win', 0)
            avg_loss = summary.get('avg_loss', 0)
            largest_win = summary.get('largest_win', 0)
            largest_loss = summary.get('largest_loss', 0)
            
            message += f"""
🏆 การเทรดที่ชนะ: {winning_trades}
❌ การเทรดที่แพ้: {losing_trades}
📊 กำไรเฉลี่ย: {avg_win:.2f}
📉 ขาดทุนเฉลี่ย: {avg_loss:.2f}
🎯 กำไรสูงสุด: {largest_win:.2f}
⚡ ขาดทุนสูงสุด: {largest_loss:.2f}
"""
        
        message += f"\n⏰ รายงาน ณ เวลา: {datetime.now().strftime('%H:%M:%S')}"
        
        return message.strip()
    
    def _format_weekly_report(self, weekly_reports: List[PeriodStats]) -> str:
        """จัดรูปแบบรายงานรายสัปดาห์"""
        message = f"""
📅 **รายงานผลการเทรดรายสัปดาห์**
🕐 สร้างเมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}

"""
        
        for i, week in enumerate(weekly_reports):
            if i >= 4:  # แสดงเฉพาะ 4 สัปดาห์ล่าสุด
                break
            
            # กำหนด emoji ตาม winrate
            if week.winrate >= 70:
                emoji = "🔥"
            elif week.winrate >= 50:
                emoji = "✅"
            elif week.winrate > 0:
                emoji = "⚠️"
            else:
                emoji = "❌"
            
            # แสดงการเปลี่ยนแปลงจากสัปดาห์ก่อน
            trend = ""
            if i < len(weekly_reports) - 1:
                prev_winrate = weekly_reports[i + 1].winrate
                if week.winrate > prev_winrate:
                    trend = "📈"
                elif week.winrate < prev_winrate:
                    trend = "📉"
                else:
                    trend = "➡️"
            
            message += f"""
{emoji} **สัปดาห์ที่ {i + 1}** {trend}
📊 การเทรด: {week.total_trades} | Winrate: {week.winrate:.1f}%
💰 PnL: {week.total_pnl:.2f} | PF: {week.profit_factor:.2f}
🏆 ชนะ: {week.winning_trades} | ❌ แพ้: {week.losing_trades}

"""
        
        return message.strip()
    
    def _format_monthly_report(self, monthly_reports: List[PeriodStats]) -> str:
        """จัดรูปแบบรายงานรายเดือน"""
        message = f"""
📆 **รายงานผลการเทรดรายเดือน**
🕐 สร้างเมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}

"""
        
        for i, month in enumerate(monthly_reports):
            if i >= 3:  # แสดงเฉพาะ 3 เดือนล่าสุด
                break
            
            # กำหนด emoji ตาม winrate
            if month.winrate >= 70:
                emoji = "🔥"
            elif month.winrate >= 50:
                emoji = "✅"
            elif month.winrate > 0:
                emoji = "⚠️"
            else:
                emoji = "❌"
            
            # แสดงการเปลี่ยนแปลงจากเดือนก่อน
            trend = ""
            if i < len(monthly_reports) - 1:
                prev_winrate = monthly_reports[i + 1].winrate
                if month.winrate > prev_winrate:
                    trend = "📈"
                elif month.winrate < prev_winrate:
                    trend = "📉"
                else:
                    trend = "➡️"
            
            message += f"""
{emoji} **{month.period}** {trend}
📊 การเทรดทั้งหมด: {month.total_trades}
🎯 Winrate: {month.winrate:.1f}%
💰 PnL รวม: {month.total_pnl:.2f}
📈 Profit Factor: {month.profit_factor:.2f}
📉 Max Drawdown: {month.max_drawdown:.2f}
🏆 ชนะ: {month.winning_trades} | ❌ แพ้: {month.losing_trades}
💎 กำไรเฉลี่ย: {month.avg_win:.2f}
⚡ ขาดทุนเฉลี่ย: {month.avg_loss:.2f}
🔥 ชนะติดต่อกันสูงสุด: {month.consecutive_wins}
❄️ แพ้ติดต่อกันสูงสุด: {month.consecutive_losses}

"""
        
        return message.strip()
    
    def _format_trade_alert(self, trade_id: str, action: str, details: Dict) -> str:
        """จัดรูปแบบการแจ้งเตือนการเทรด"""
        if action == "OPEN":
            symbol = details.get('symbol', 'N/A')
            position_type = details.get('position_type', 'N/A')
            entry_price = details.get('entry_price', 0)
            position_size = details.get('position_size', 0)
            strategy = details.get('strategy_name', 'N/A')
            
            emoji = "🟢" if position_type == "LONG" else "🔴"
            
            message = f"""
{emoji} **การเทรดใหม่เปิดแล้ว**

🆔 Trade ID: {trade_id}
💹 Symbol: {symbol}
📍 Position: {position_type}
💰 Entry Price: {entry_price}
📊 Size: {position_size}
🎯 Strategy: {strategy}
⏰ เวลา: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
            
            if details.get('stop_loss'):
                message += f"\n🛑 Stop Loss: {details['stop_loss']}"
            if details.get('take_profit'):
                message += f"\n🎯 Take Profit: {details['take_profit']}"
        
        elif action == "CLOSE":
            exit_price = details.get('exit_price', 0)
            pnl = details.get('pnl', 0)
            pnl_percentage = details.get('pnl_percentage', 0)
            exit_reason = details.get('exit_reason', 'Manual')
            
            emoji = "✅" if pnl > 0 else "❌"
            pnl_emoji = "💰" if pnl > 0 else "📉"
            
            message = f"""
{emoji} **การเทรดปิดแล้ว**

🆔 Trade ID: {trade_id}
💰 Exit Price: {exit_price}
{pnl_emoji} PnL: {pnl:.2f} ({pnl_percentage:.2f}%)
📝 เหตุผล: {exit_reason}
⏰ เวลา: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        
        else:  # UPDATE
            message = f"""
🔄 **อัปเดตการเทรด**

🆔 Trade ID: {trade_id}
📝 การเปลี่ยนแปลง: {details.get('changes', 'N/A')}
⏰ เวลา: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        
        return message.strip()
    
    def _setup_scheduled_reports(self) -> None:
        """ตั้งค่าการส่งรายงานอัตโนมัติ"""
        # สรุปรายวัน - ส่งเวลา 18:00 ทุกวัน
        schedule.every().day.at("18:00").do(self.send_daily_summary)
        
        # รายงานรายสัปดาห์ - ส่งทุกวันอาทิตย์ เวลา 19:00
        schedule.every().sunday.at("19:00").do(self.send_weekly_report)
        
        # รายงานรายเดือน - ส่งวันที่ 1 ของเดือน เวลา 20:00
        schedule.every().month.do(self._check_monthly_report)
        
        logger.info("✅ ตั้งค่าการส่งรายงานอัตโนมัติสำเร็จ")
    
    def _check_monthly_report(self) -> None:
        """ตรวจสอบและส่งรายงานรายเดือนในวันที่ 1"""
        if datetime.now().day == 1:
            self.send_monthly_report()
    
    def run_scheduler(self) -> None:
        """เรียกใช้ scheduler (ใช้ในการทำงานแบบ background)"""
        logger.info("🔄 เริ่มต้น Performance Reporter Scheduler")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # ตรวจสอบทุกนาที

# Enhanced TradingMonitor with automatic reporting
class EnhancedTradingMonitor(TradingMonitor):
    """TradingMonitor ที่มีการส่งรายงานอัตโนมัติ"""
    
    def __init__(self, data_dir: str = "trading_data", enable_reporting: bool = True):
        super().__init__(data_dir)
        
        if enable_reporting:
            self.reporter = PerformanceReporter(self, auto_schedule=False)
        else:
            self.reporter = None
    
    def open_trade(self, *args, **kwargs) -> str:
        """เปิดการเทรดพร้อมส่งการแจ้งเตือน"""
        trade_id = super().open_trade(*args, **kwargs)
        
        if self.reporter and trade_id:
            # ส่งการแจ้งเตือนการเทรดใหม่
            trade = self.active_trades[trade_id]
            details = {
                'symbol': trade.symbol,
                'position_type': trade.position_type,
                'entry_price': trade.entry_price,
                'position_size': trade.position_size,
                'strategy_name': trade.strategy_name,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit
            }
            self.reporter.send_trade_alert(trade_id, "OPEN", details)
        
        return trade_id
    
    def close_trade(self, trade_id: str, exit_price: float, exit_reason: str = "Manual") -> bool:
        """ปิดการเทรดพร้อมส่งการแจ้งเตือน"""
        # เก็บข้อมูลก่อนปิด
        trade = self.active_trades.get(trade_id)
        
        success = super().close_trade(trade_id, exit_price, exit_reason)
        
        if success and self.reporter and trade:
            # คำนวณ PnL
            if trade.position_type == 'LONG':
                pnl = (exit_price - trade.entry_price) * trade.position_size
            else:
                pnl = (trade.entry_price - exit_price) * trade.position_size
            
            pnl_percentage = (pnl / (trade.entry_price * trade.position_size)) * 100
            
            details = {
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'exit_reason': exit_reason
            }
            self.reporter.send_trade_alert(trade_id, "CLOSE", details)
        
        return success
    
    def send_manual_report(self, report_type: str = "daily") -> None:
        """ส่งรายงานแบบ manual"""
        if not self.reporter:
            logger.warning("Reporter ไม่ได้เปิดใช้งาน")
            return
        
        if report_type == "daily":
            self.reporter.send_daily_summary()
        elif report_type == "weekly":
            self.reporter.send_weekly_report()
        elif report_type == "monthly":
            self.reporter.send_monthly_report()
        else:
            logger.warning(f"Report type ไม่รองรับ: {report_type}")

# Helper functions
def create_enhanced_monitor(data_dir: str = "trading_data", 
                          enable_reporting: bool = True) -> EnhancedTradingMonitor:
    """สร้าง Enhanced Trading Monitor"""
    return EnhancedTradingMonitor(data_dir, enable_reporting)

if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    monitor = create_enhanced_monitor()
    
    # ส่งรายงานทดสอบ
    monitor.send_manual_report("daily")
    monitor.send_manual_report("weekly")
