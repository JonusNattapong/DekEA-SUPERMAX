"""
Trading Performance Monitor - เชื่อมต่อกับระบบเทรดหลักเพื่อบันทึกผลการเทรดอัตโนมัติ
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from src.utils.performance_tracker import PerformanceTracker, TradeRecord

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingMonitor:
    """ระบบติดตามการเทรดที่เชื่อมต่อกับ Algorithm Manager"""
    
    def __init__(self, data_dir: str = "trading_data"):
        """
        Initialize Trading Monitor
        
        Args:
            data_dir: โฟลเดอร์สำหรับเก็บข้อมูลการเทรด
        """
        self.tracker = PerformanceTracker(data_dir)
        self.active_trades: Dict[str, TradeRecord] = {}
        
        # โหลดการเทรดที่ยังเปิดอยู่
        self._load_active_trades()
    
    def open_trade(self, 
                   symbol: str,
                   entry_price: float,
                   position_type: str,
                   position_size: float,
                   strategy_name: str,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None,
                   notes: Optional[str] = None) -> str:
        """
        เปิดการเทรดใหม่
        
        Args:
            symbol: สัญลักษณ์ของเครื่องมือการเทรด (เช่น XAUUSD)
            entry_price: ราคาที่เข้าซื้อ/ขาย
            position_type: ประเภทของ position ('LONG' หรือ 'SHORT')
            position_size: ขนาดของ position
            strategy_name: ชื่อกลยุทธ์ที่ใช้
            stop_loss: ราคา Stop Loss
            take_profit: ราคา Take Profit
            notes: หมายเหตุเพิ่มเติม
        
        Returns:
            trade_id: รหัสการเทรดที่สร้างขึ้น
        """
        trade_id = self._generate_trade_id()
        
        trade = TradeRecord(
            trade_id=trade_id,
            symbol=symbol,
            entry_time=datetime.now(),
            exit_time=None,
            entry_price=entry_price,
            exit_price=None,
            position_type=position_type,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            pnl=None,
            pnl_percentage=None,
            status='OPEN',
            strategy_name=strategy_name,
            notes=notes
        )
        
        # เก็บในการเทรดที่ยังเปิดอยู่
        self.active_trades[trade_id] = trade
        
        # บันทึกลง tracker
        self.tracker.add_trade(trade)
        
        logger.info(f"🔓 เปิดการเทรดใหม่: {trade_id} | {symbol} | {position_type} | {entry_price}")
        
        return trade_id
    
    def close_trade(self, 
                    trade_id: str, 
                    exit_price: float, 
                    exit_reason: str = "Manual") -> bool:
        """
        ปิดการเทรด
        
        Args:
            trade_id: รหัสการเทรด
            exit_price: ราคาที่ปิด
            exit_reason: เหตุผลในการปิด
        
        Returns:
            bool: สำเร็จหรือไม่
        """
        if trade_id not in self.active_trades:
            logger.warning(f"ไม่พบการเทรด: {trade_id}")
            return False
        
        # อัปเดตการเทรดใน tracker
        success = self.tracker.close_trade(trade_id, exit_price, datetime.now())
        
        if success:
            # ลบออกจากการเทรดที่เปิดอยู่
            trade = self.active_trades.pop(trade_id)
            
            # คำนวณ PnL สำหรับ log
            if trade.position_type == 'LONG':
                pnl = (exit_price - trade.entry_price) * trade.position_size
            else:
                pnl = (trade.entry_price - exit_price) * trade.position_size
            
            pnl_percentage = (pnl / (trade.entry_price * trade.position_size)) * 100
            
            # อัปเดต notes
            updated_notes = f"{trade.notes or ''} | Exit Reason: {exit_reason}".strip(" |")
            self.tracker.update_trade(trade_id, notes=updated_notes)
            
            status_emoji = "✅" if pnl > 0 else "❌"
            logger.info(f"{status_emoji} ปิดการเทรด: {trade_id} | PnL: {pnl:.2f} ({pnl_percentage:.2f}%) | Reason: {exit_reason}")
            
            return True
        
        return False
    
    def update_trade_levels(self, 
                           trade_id: str,
                           stop_loss: Optional[float] = None,
                           take_profit: Optional[float] = None) -> bool:
        """
        อัปเดตระดับ Stop Loss และ Take Profit
        
        Args:
            trade_id: รหัสการเทรด
            stop_loss: ราคา Stop Loss ใหม่
            take_profit: ราคา Take Profit ใหม่
        
        Returns:
            bool: สำเร็จหรือไม่
        """
        if trade_id not in self.active_trades:
            logger.warning(f"ไม่พบการเทรด: {trade_id}")
            return False
        
        updates = {}
        if stop_loss is not None:
            updates['stop_loss'] = stop_loss
        if take_profit is not None:
            updates['take_profit'] = take_profit
        
        if updates:
            success = self.tracker.update_trade(trade_id, **updates)
            if success:
                # อัปเดตในการเทรดที่เปิดอยู่ด้วย
                for key, value in updates.items():
                    setattr(self.active_trades[trade_id], key, value)
                
                logger.info(f"🔄 อัปเดตระดับการเทรด: {trade_id} | SL: {stop_loss} | TP: {take_profit}")
                return True
        
        return False
    
    def get_active_trades(self) -> Dict[str, TradeRecord]:
        """ดึงการเทรดที่ยังเปิดอยู่ทั้งหมด"""
        return self.active_trades.copy()
    
    def check_trade_levels(self, current_prices: Dict[str, float]) -> List[str]:
        """
        ตรวจสอบว่าการเทรดใดถึงระดับ SL หรือ TP
        
        Args:
            current_prices: ราคาปัจจุบันของแต่ละสัญลักษณ์
        
        Returns:
            List[str]: รายการการเทรดที่ควรปิด
        """
        trades_to_close = []
        
        for trade_id, trade in self.active_trades.items():
            current_price = current_prices.get(trade.symbol)
            
            if current_price is None:
                continue
            
            should_close = False
            close_reason = ""
            
            if trade.position_type == 'LONG':
                # Long position
                if trade.stop_loss and current_price <= trade.stop_loss:
                    should_close = True
                    close_reason = "Stop Loss Hit"
                elif trade.take_profit and current_price >= trade.take_profit:
                    should_close = True
                    close_reason = "Take Profit Hit"
            
            else:  # SHORT position
                if trade.stop_loss and current_price >= trade.stop_loss:
                    should_close = True
                    close_reason = "Stop Loss Hit"
                elif trade.take_profit and current_price <= trade.take_profit:
                    should_close = True
                    close_reason = "Take Profit Hit"
            
            if should_close:
                # ปิดการเทรดอัตโนมัติ
                if self.close_trade(trade_id, current_price, close_reason):
                    trades_to_close.append(trade_id)
        
        return trades_to_close
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """สร้างสรุปการเทรดรายวัน"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(hour=23, minute=59, second=59)
        
        today_trades = self.tracker.get_trades_by_period(today, tomorrow)
        
        if not today_trades:
            return {
                "date": today.strftime("%d/%m/%Y"),
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "winrate": 0.0,
                "total_pnl": 0.0,
                "active_trades": len(self.active_trades)
            }
        
        stats = self.tracker.calculate_period_stats(
            today_trades, 
            f"วันที่ {today.strftime('%d/%m/%Y')}", 
            today, 
            tomorrow
        )
        
        return {
            "date": today.strftime("%d/%m/%Y"),
            "total_trades": stats.total_trades,
            "winning_trades": stats.winning_trades,
            "losing_trades": stats.losing_trades,
            "winrate": stats.winrate,
            "total_pnl": stats.total_pnl,
            "avg_win": stats.avg_win,
            "avg_loss": stats.avg_loss,
            "largest_win": stats.largest_win,
            "largest_loss": stats.largest_loss,
            "active_trades": len(self.active_trades)
        }
    
    def generate_performance_report(self, report_type: str = "both") -> None:
        """สร้างและแสดงรายงานผลการเทรด"""
        self.tracker.print_formatted_report(report_type)
    
    def create_performance_chart(self, save_path: Optional[str] = None) -> None:
        """สร้างกราฟแสดงผลการเทรด"""
        self.tracker.create_performance_chart(save_path)
    
    def _generate_trade_id(self) -> str:
        """สร้าง ID การเทรดที่ไม่ซ้ำ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"TRADE_{timestamp}_{unique_id}"
    
    def _load_active_trades(self) -> None:
        """โหลดการเทรดที่ยังเปิดอยู่"""
        for trade in self.tracker.trades:
            if trade.status == 'OPEN':
                self.active_trades[trade.trade_id] = trade
        
        logger.info(f"โหลดการเทรดที่เปิดอยู่: {len(self.active_trades)} รายการ")

# Integration functions สำหรับใช้กับระบบเทรดหลัก
def integrate_with_algorithm_manager(monitor: TradingMonitor, 
                                   recommendation: Dict[str, Any],
                                   symbol: str = "XAUUSD",
                                   position_size: float = 0.1) -> Optional[str]:
    """
    เชื่อมต่อกับ Algorithm Manager เพื่อเปิดการเทรดใหม่
    
    Args:
        monitor: TradingMonitor instance
        recommendation: ผลการแนะนำจาก Algorithm Manager
        symbol: สัญลักษณ์ของเครื่องมือการเทรด
        position_size: ขนาดของ position
    
    Returns:
        trade_id หากเปิดการเทรดสำเร็จ, None หากไม่เปิด
    """
    signal = recommendation.get('signal')
    
    if signal not in ['BUY', 'SELL']:
        return None
    
    current_price = recommendation.get('current_price')
    if not current_price:
        logger.warning("ไม่มีข้อมูลราคาปัจจุบัน")
        return None
    
    # กำหนด position type
    position_type = 'LONG' if signal == 'BUY' else 'SHORT'
    
    # ดึงข้อมูล risk management
    risk_metrics = recommendation.get('risk_metrics', {})
    stop_loss = risk_metrics.get('stop_loss')
    take_profit = risk_metrics.get('take_profit')
    
    # สร้างหมายเหตุ
    algorithm_details = recommendation.get('individual_signals', {})
    notes = f"Algorithms: {', '.join(algorithm_details.keys())} | Confidence: {recommendation.get('confidence', 'N/A')}"
    
    # เปิดการเทรด
    trade_id = monitor.open_trade(
        symbol=symbol,
        entry_price=current_price,
        position_type=position_type,
        position_size=position_size,
        strategy_name="Algorithm_Manager",
        stop_loss=stop_loss,
        take_profit=take_profit,
        notes=notes
    )
    
    return trade_id

def create_monitoring_system(data_dir: str = "trading_data") -> TradingMonitor:
    """สร้างระบบติดตามการเทรด"""
    return TradingMonitor(data_dir)

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # สร้างระบบติดตาม
    monitor = create_monitoring_system()
    
    # แสดงสรุปรายวัน
    daily_summary = monitor.get_daily_summary()
    print("📊 สรุปการเทรดวันนี้:")
    print(f"   🔢 การเทรดทั้งหมด: {daily_summary['total_trades']}")
    print(f"   🎯 Winrate: {daily_summary['winrate']:.2f}%")
    print(f"   💰 PnL รวม: {daily_summary['total_pnl']:.2f}")
    print(f"   🔓 การเทรดที่เปิดอยู่: {daily_summary['active_trades']}")
    
    # แสดงรายงานผลการเทรด
    monitor.generate_performance_report("weekly")
