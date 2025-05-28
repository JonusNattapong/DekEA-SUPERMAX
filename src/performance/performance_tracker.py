"""
Performance Tracker - ระบบติดตามและรายงาน Winrate
สำหรับการวิเคราะห์ผลการเทรดในแต่ละสัปดาห์และเดือน
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """โครงสร้างข้อมูลการเทรดแต่ละครั้ง"""
    trade_id: str
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position_type: str  # 'LONG' or 'SHORT'
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    pnl: Optional[float]
    pnl_percentage: Optional[float]
    status: str  # 'OPEN', 'CLOSED', 'PARTIAL'
    strategy_name: str
    notes: Optional[str] = None

@dataclass
class PeriodStats:
    """สถิติการเทรดในช่วงเวลาหนึ่ง"""
    period: str
    start_date: datetime
    end_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    winrate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int

class PerformanceTracker:
    """ระบบติดตามและวิเคราะห์ผลการเทรด"""
    
    def __init__(self, data_dir: str = "trading_data"):
        """
        Initialize Performance Tracker
        
        Args:
            data_dir: โฟลเดอร์สำหรับเก็บข้อมูลการเทรด
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.trades_file = self.data_dir / "trades.json"
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        self.trades: List[TradeRecord] = []
        self.load_trades()
    
    def add_trade(self, trade: TradeRecord) -> None:
        """เพิ่มรายการเทรดใหม่"""
        self.trades.append(trade)
        self.save_trades()
        logger.info(f"เพิ่มการเทรดใหม่: {trade.trade_id}")
    
    def update_trade(self, trade_id: str, **updates) -> bool:
        """อัปเดตข้อมูลการเทรด"""
        for i, trade in enumerate(self.trades):
            if trade.trade_id == trade_id:
                for key, value in updates.items():
                    if hasattr(trade, key):
                        setattr(trade, key, value)
                
                # คำนวณ PnL หากปิดออเดอร์แล้ว
                if trade.exit_price and trade.exit_time:
                    trade = self._calculate_pnl(trade)
                    trade.status = 'CLOSED'
                
                self.trades[i] = trade
                self.save_trades()
                logger.info(f"อัปเดตการเทรด: {trade_id}")
                return True
        return False
    
    def close_trade(self, trade_id: str, exit_price: float, exit_time: datetime = None) -> bool:
        """ปิดการเทรด"""
        if exit_time is None:
            exit_time = datetime.now()
        
        return self.update_trade(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_time=exit_time,
            status='CLOSED'
        )
    
    def _calculate_pnl(self, trade: TradeRecord) -> TradeRecord:
        """คำนวณ PnL สำหรับการเทรด"""
        if trade.exit_price is None:
            return trade
        
        if trade.position_type == 'LONG':
            pnl = (trade.exit_price - trade.entry_price) * trade.position_size
        else:  # SHORT
            pnl = (trade.entry_price - trade.exit_price) * trade.position_size
        
        trade.pnl = pnl
        trade.pnl_percentage = (pnl / (trade.entry_price * trade.position_size)) * 100
        
        return trade
    
    def get_trades_by_period(self, start_date: datetime, end_date: datetime) -> List[TradeRecord]:
        """ดึงการเทรดในช่วงเวลาที่กำหนด"""
        return [
            trade for trade in self.trades
            if trade.entry_time >= start_date and trade.entry_time <= end_date
            and trade.status == 'CLOSED'
        ]
    
    def calculate_period_stats(self, trades: List[TradeRecord], period_name: str, 
                             start_date: datetime, end_date: datetime) -> PeriodStats:
        """คำนวณสถิติสำหรับช่วงเวลาหนึ่ง"""
        if not trades:
            return PeriodStats(
                period=period_name,
                start_date=start_date,
                end_date=end_date,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                winrate=0.0,
                total_pnl=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                consecutive_wins=0,
                consecutive_losses=0
            )
        
        # คำนวณสถิติพื้นฐาน
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        winrate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        
        # PnL สถิติ
        total_pnl = sum(t.pnl for t in trades)
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        total_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Max Drawdown
        cumulative_pnl = np.cumsum([t.pnl for t in trades])
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = running_max - cumulative_pnl
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # ผลกำไร/ขาดทุนที่ใหญ่ที่สุด
        largest_win = max([t.pnl for t in trades]) if trades else 0
        largest_loss = min([t.pnl for t in trades]) if trades else 0
        
        # คำนวณ Consecutive Wins/Losses
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(trades)
        
        return PeriodStats(
            period=period_name,
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            winrate=winrate,
            total_pnl=total_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            largest_win=largest_win,
            largest_loss=largest_loss,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses
        )
    
    def _calculate_consecutive_trades(self, trades: List[TradeRecord]) -> Tuple[int, int]:
        """คำนวณการเทรดติดต่อกันที่ชนะ/แพ้"""
        if not trades:
            return 0, 0
        
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif trade.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return max_consecutive_wins, max_consecutive_losses
    
    def get_weekly_report(self, weeks_back: int = 4) -> List[PeriodStats]:
        """สร้างรายงานรายสัปดาห์"""
        reports = []
        
        # หาวันจันทร์ของสัปดาห์ปัจจุบัน
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        
        for i in range(weeks_back):
            week_start = current_monday - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            week_trades = self.get_trades_by_period(week_start, week_end)
            week_name = f"สัปดาห์ที่ {week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}"
            
            stats = self.calculate_period_stats(week_trades, week_name, week_start, week_end)
            reports.append(stats)
        
        return reports
    
    def get_monthly_report(self, months_back: int = 6) -> List[PeriodStats]:
        """สร้างรายงานรายเดือน"""
        reports = []
        
        today = datetime.now()
        
        for i in range(months_back):
            # หาวันแรกของเดือน
            if i == 0:
                month_start = datetime(today.year, today.month, 1)
            else:
                target_month = today.month - i
                target_year = today.year
                
                while target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = datetime(target_year, target_month, 1)
            
            # หาวันสุดท้ายของเดือน
            if month_start.month == 12:
                month_end = datetime(month_start.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(seconds=1)
            
            month_trades = self.get_trades_by_period(month_start, month_end)
            month_name = f"{month_start.strftime('%B %Y')}"
            
            stats = self.calculate_period_stats(month_trades, month_name, month_start, month_end)
            reports.append(stats)
        
        return reports
    
    def generate_report(self, report_type: str = "both", save_to_file: bool = True) -> Dict:
        """สร้างรายงานสรุปผลการเทรด"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "report_type": report_type
        }
        
        if report_type in ["weekly", "both"]:
            weekly_reports = self.get_weekly_report()
            report_data["weekly_reports"] = [asdict(report) for report in weekly_reports]
        
        if report_type in ["monthly", "both"]:
            monthly_reports = self.get_monthly_report()
            report_data["monthly_reports"] = [asdict(report) for report in monthly_reports]
        
        # สร้างสรุปภาพรวม
        all_trades = [t for t in self.trades if t.status == 'CLOSED']
        if all_trades:
            overall_stats = self.calculate_period_stats(
                all_trades, 
                "สรุปรวม", 
                min(t.entry_time for t in all_trades),
                max(t.entry_time for t in all_trades)
            )
            report_data["overall_stats"] = asdict(overall_stats)
        
        if save_to_file:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"บันทึกรายงานที่: {filepath}")
        
        return report_data
    
    def create_performance_chart(self, save_path: Optional[str] = None) -> None:
        """สร้างกราฟแสดงผลการเทรด"""
        plt.style.use('seaborn-v0_8')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Weekly Winrate Chart
        weekly_reports = self.get_weekly_report(8)  # 8 สัปดาห์ย้อนหลัง
        
        if weekly_reports:
            weeks = [report.period.split(' ')[1] for report in weekly_reports[::-1]]
            winrates = [report.winrate for report in weekly_reports[::-1]]
            
            ax1.bar(range(len(weeks)), winrates, color='lightblue', alpha=0.7)
            ax1.set_title('Weekly Winrate (%)', fontweight='bold')
            ax1.set_ylabel('Winrate (%)')
            ax1.set_xticks(range(len(weeks)))
            ax1.set_xticklabels(weeks, rotation=45)
            ax1.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='Break-even')
            ax1.legend()
            ax1.grid(axis='y', alpha=0.3)
        
        # 2. Monthly Winrate Chart
        monthly_reports = self.get_monthly_report(6)  # 6 เดือนย้อนหลัง
        
        if monthly_reports:
            months = [report.period for report in monthly_reports[::-1]]
            monthly_winrates = [report.winrate for report in monthly_reports[::-1]]
            
            ax2.plot(range(len(months)), monthly_winrates, marker='o', linewidth=2, markersize=6)
            ax2.set_title('Monthly Winrate Trend', fontweight='bold')
            ax2.set_ylabel('Winrate (%)')
            ax2.set_xticks(range(len(months)))
            ax2.set_xticklabels(months, rotation=45)
            ax2.axhline(y=50, color='red', linestyle='--', alpha=0.7)
            ax2.grid(alpha=0.3)
        
        # 3. PnL Distribution
        closed_trades = [t for t in self.trades if t.status == 'CLOSED' and t.pnl is not None]
        if closed_trades:
            pnls = [trade.pnl for trade in closed_trades]
            ax3.hist(pnls, bins=20, alpha=0.7, edgecolor='black')
            ax3.set_title('PnL Distribution', fontweight='bold')
            ax3.set_xlabel('PnL')
            ax3.set_ylabel('Frequency')
            ax3.axvline(x=0, color='red', linestyle='--', alpha=0.7)
            ax3.grid(alpha=0.3)
        
        # 4. Cumulative PnL
        if closed_trades:
            sorted_trades = sorted(closed_trades, key=lambda x: x.entry_time)
            cumulative_pnl = np.cumsum([t.pnl for t in sorted_trades])
            dates = [t.entry_time for t in sorted_trades]
            
            ax4.plot(dates, cumulative_pnl, linewidth=2)
            ax4.set_title('Cumulative PnL', fontweight='bold')
            ax4.set_ylabel('Cumulative PnL')
            ax4.grid(alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.reports_dir / f"performance_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        logger.info(f"บันทึกกราฟที่: {save_path}")
    
    def print_formatted_report(self, report_type: str = "both") -> None:
        """แสดงรายงานในรูปแบบที่อ่านง่าย"""
        report = self.generate_report(report_type, save_to_file=False)
        
        print("\n" + "="*70)
        print("📊 TRADING PERFORMANCE REPORT 📊")
        print("="*70)
        print(f"🕐 Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Overall Stats
        if "overall_stats" in report:
            stats = report["overall_stats"]
            print(f"\n🌟 OVERALL PERFORMANCE")
            print("-" * 50)
            print(f"📈 Total Trades: {stats['total_trades']}")
            print(f"🏆 Winrate: {stats['winrate']:.2f}%")
            print(f"💰 Total PnL: {stats['total_pnl']:.2f}")
            print(f"📊 Profit Factor: {stats['profit_factor']:.2f}")
            print(f"📉 Max Drawdown: {stats['max_drawdown']:.2f}")
        
        # Weekly Reports
        if "weekly_reports" in report:
            print(f"\n📅 WEEKLY REPORTS")
            print("-" * 50)
            for week_data in report["weekly_reports"]:
                print(f"\n📊 {week_data['period']}")
                print(f"   🔢 Trades: {week_data['total_trades']}")
                print(f"   🎯 Winrate: {week_data['winrate']:.2f}%")
                print(f"   💰 PnL: {week_data['total_pnl']:.2f}")
                print(f"   🏆 Wins: {week_data['winning_trades']} | ❌ Losses: {week_data['losing_trades']}")
        
        # Monthly Reports
        if "monthly_reports" in report:
            print(f"\n📆 MONTHLY REPORTS")
            print("-" * 50)
            for month_data in report["monthly_reports"]:
                print(f"\n📊 {month_data['period']}")
                print(f"   🔢 Trades: {month_data['total_trades']}")
                print(f"   🎯 Winrate: {month_data['winrate']:.2f}%")
                print(f"   💰 PnL: {month_data['total_pnl']:.2f}")
                print(f"   🏆 Wins: {month_data['winning_trades']} | ❌ Losses: {month_data['losing_trades']}")
                print(f"   📈 Avg Win: {month_data['avg_win']:.2f} | 📉 Avg Loss: {month_data['avg_loss']:.2f}")
        
        print("\n" + "="*70)
    
    def save_trades(self) -> None:
        """บันทึกข้อมูลการเทรดลงไฟล์"""
        trades_data = []
        for trade in self.trades:
            trade_dict = asdict(trade)
            # แปลง datetime เป็น string สำหรับ JSON
            if trade_dict['entry_time']:
                trade_dict['entry_time'] = trade_dict['entry_time'].isoformat()
            if trade_dict['exit_time']:
                trade_dict['exit_time'] = trade_dict['exit_time'].isoformat()
            trades_data.append(trade_dict)
        
        with open(self.trades_file, 'w', encoding='utf-8') as f:
            json.dump(trades_data, f, ensure_ascii=False, indent=2)
    
    def load_trades(self) -> None:
        """โหลดข้อมูลการเทรดจากไฟล์"""
        if not self.trades_file.exists():
            return
        
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                trades_data = json.load(f)
            
            self.trades = []
            for trade_dict in trades_data:
                # แปลง string กลับเป็น datetime
                if trade_dict['entry_time']:
                    trade_dict['entry_time'] = datetime.fromisoformat(trade_dict['entry_time'])
                if trade_dict['exit_time']:
                    trade_dict['exit_time'] = datetime.fromisoformat(trade_dict['exit_time'])
                
                trade = TradeRecord(**trade_dict)
                self.trades.append(trade)
            
            logger.info(f"โหลดข้อมูล {len(self.trades)} การเทรดสำเร็จ")
        
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            self.trades = []

# Helper functions สำหรับใช้งานง่าย
def create_tracker(data_dir: str = "trading_data") -> PerformanceTracker:
    """สร้าง Performance Tracker instance"""
    return PerformanceTracker(data_dir)

def add_sample_trades(tracker: PerformanceTracker) -> None:
    """เพิ่มข้อมูลตัวอย่างสำหรับทดสอบ"""
    import random
    
    base_date = datetime.now() - timedelta(days=60)
    
    for i in range(50):
        trade_date = base_date + timedelta(days=random.randint(0, 60))
        exit_date = trade_date + timedelta(hours=random.randint(1, 24))
        
        entry_price = 2000 + random.uniform(-50, 50)
        win_probability = 0.6  # 60% โอกาสชนะ
        
        if random.random() < win_probability:
            # การเทรดที่ชนะ
            exit_price = entry_price + random.uniform(5, 30)
        else:
            # การเทรดที่แพ้
            exit_price = entry_price - random.uniform(5, 20)
        
        trade = TradeRecord(
            trade_id=f"TRADE_{i+1:03d}",
            symbol="XAUUSD",
            entry_time=trade_date,
            exit_time=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            position_type=random.choice(['LONG', 'SHORT']),
            position_size=0.1,
            stop_loss=entry_price - 15 if random.choice(['LONG', 'SHORT']) == 'LONG' else entry_price + 15,
            take_profit=entry_price + 30 if random.choice(['LONG', 'SHORT']) == 'LONG' else entry_price - 30,
            pnl=None,  # จะคำนวณอัตโนมัติ
            pnl_percentage=None,  # จะคำนวณอัตโนมัติ
            status='CLOSED',
            strategy_name=random.choice(['MA_Crossover', 'RSI_Strategy', 'MACD_Strategy'])
        )
        
        # คำนวณ PnL
        if trade.position_type == 'LONG':
            pnl = (exit_price - entry_price) * trade.position_size
        else:
            pnl = (entry_price - exit_price) * trade.position_size
        
        trade.pnl = pnl
        trade.pnl_percentage = (pnl / (entry_price * trade.position_size)) * 100
        
        tracker.add_trade(trade)

if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    tracker = create_tracker()
    
    # เพิ่มข้อมูลตัวอย่าง (ใช้เฉพาะการทดสอบ)
    # add_sample_trades(tracker)
    
    # สร้างรายงาน
    tracker.print_formatted_report()
    
    # สร้างกราฟ
    # tracker.create_performance_chart()
