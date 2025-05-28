"""
Performance System Integration - การผสานรวมระบบ Performance Tracking กับระบบเทรดหลัก
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# เพิ่ม path เพื่อ import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ระบบเทรดหลัก
from src.algorithms.trading_algorithms import AlgorithmManager, execute_algorithm_trading
from src.utils.price_utils import fetch_gold_price_data
from src.utils.risk_utils import calculate_risk_metrics

# Import ระบบ Performance Tracking
from src.performance.performance_tracker import PerformanceTracker, TradeRecord
from src.performance.performance_trading_monitor import TradingMonitor, integrate_with_algorithm_manager
from src.performance.performance_reporter import EnhancedTradingMonitor, create_enhanced_monitor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DekTradingSystem:
    """ระบบเทรดหลักที่รวม Performance Tracking เข้าไป"""
    
    def __init__(self, 
                 data_dir: str = "trading_data",
                 enable_reporting: bool = True,
                 account_balance: float = 10000,
                 risk_percent: float = 1.0):
        """
        Initialize Dek Trading System
        
        Args:
            data_dir: โฟลเดอร์สำหรับเก็บข้อมูลการเทรด
            enable_reporting: เปิดใช้งานการส่งรายงานผ่าน Telegram
            account_balance: ยอดเงินในบัญชี
            risk_percent: เปอร์เซ็นต์ความเสี่ยงต่อการเทรด
        """
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        
        # สร้างระบบติดตามการเทรด
        self.monitor = create_enhanced_monitor(data_dir, enable_reporting)
        
        # สร้าง Algorithm Manager
        self.algorithm_manager = AlgorithmManager()
        self._setup_algorithms()
        
        logger.info("🚀 เริ่มต้นระบบ Dek Trading System สำเร็จ")
    
    def _setup_algorithms(self) -> None:
        """ตั้งค่า trading algorithms"""
        from src.algorithms.trading_algorithms import (
            MACrossover, RSIStrategy, BollingerBandsStrategy, MACDStrategy
        )
        
        # เพิ่ม algorithms พร้อม weights
        self.algorithm_manager.add_algorithm(MACrossover(short_window=10, long_window=50), weight=1.0)
        self.algorithm_manager.add_algorithm(RSIStrategy(period=14, overbought=70, oversold=30), weight=1.2)
        self.algorithm_manager.add_algorithm(BollingerBandsStrategy(window=20, num_std=2.0), weight=1.0)
        self.algorithm_manager.add_algorithm(MACDStrategy(fast_period=12, slow_period=26, signal_period=9), weight=1.5)
        
        logger.info("✅ ตั้งค่า Trading Algorithms สำเร็จ")
    
    def run_trading_analysis(self, 
                           symbol: str = "XAUUSD",
                           timeframe: str = "1d",
                           lookback_days: int = 60) -> Dict[str, Any]:
        """
        วิเคราะห์และสร้างสัญญาณการเทรด
        
        Args:
            symbol: สัญลักษณ์ของเครื่องมือการเทรด
            timeframe: กรอบเวลา
            lookback_days: จำนวนวันย้อนหลังสำหรับวิเคราะห์
        
        Returns:
            คำแนะนำการเทรดพร้อมข้อมูล risk management
        """
        try:
            # ดึงข้อมูลราคา
            price_data = fetch_gold_price_data(timeframe=timeframe, days=lookback_days)
            
            if price_data.empty:
                logger.error("ไม่สามารถดึงข้อมูลราคาได้")
                return {"error": "ไม่สามารถดึงข้อมูลราคาได้"}
            
            # สร้างสัญญาณจาก algorithms
            recommendation = self.algorithm_manager.get_combined_signal(price_data, method="weighted_vote")
            
            # เพิ่มข้อมูลราคาปัจจุบัน
            current_price = price_data.iloc[-1]['Close']
            recommendation['current_price'] = current_price
            recommendation['symbol'] = symbol
            recommendation['analysis_time'] = datetime.now().isoformat()
            
            # คำนวณ risk management
            if recommendation['signal'] in ['BUY', 'SELL']:
                trade_direction = "LONG" if recommendation['signal'] == 'BUY' else "SHORT"
                
                risk_metrics = calculate_risk_metrics(
                    entry_price=current_price,
                    account_balance=self.account_balance,
                    risk_percent=self.risk_percent,
                    trade_direction=trade_direction
                )
                
                recommendation['risk_metrics'] = risk_metrics
            
            logger.info(f"📊 วิเคราะห์สำเร็จ: {symbol} | Signal: {recommendation['signal']}")
            return recommendation
        
        except Exception as e:
            logger.error(f"❌ Error in trading analysis: {e}")
            return {"error": str(e)}
    
    def execute_trade(self, 
                     recommendation: Dict[str, Any],
                     position_size: Optional[float] = None) -> Optional[str]:
        """
        ดำเนินการเทรดตามคำแนะนำ
        
        Args:
            recommendation: คำแนะนำจากการวิเคราะห์
            position_size: ขนาด position (ถ้าไม่ระบุจะใช้จาก risk management)
        
        Returns:
            trade_id หากเปิดการเทรดสำเร็จ
        """
        signal = recommendation.get('signal')
        
        if signal not in ['BUY', 'SELL']:
            logger.info(f"ไม่มีสัญญาณการเทรด: {signal}")
            return None
        
        # คำนวณขนาด position
        if position_size is None:
            risk_metrics = recommendation.get('risk_metrics', {})
            position_size = risk_metrics.get('position_size', 0.1)
        
        # ใช้ integration function เพื่อเปิดการเทรด
        trade_id = integrate_with_algorithm_manager(
            monitor=self.monitor,
            recommendation=recommendation,
            symbol=recommendation.get('symbol', 'XAUUSD'),
            position_size=position_size
        )
        
        if trade_id:
            logger.info(f"🎯 เปิดการเทรดสำเร็จ: {trade_id}")
        else:
            logger.warning("❌ ไม่สามารถเปิดการเทรดได้")
        
        return trade_id
    
    def close_trade_by_id(self, trade_id: str, exit_price: float, reason: str = "Manual") -> bool:
        """ปิดการเทรดตาม ID"""
        return self.monitor.close_trade(trade_id, exit_price, reason)
    
    def close_all_trades(self, current_prices: Dict[str, float], reason: str = "Close All") -> List[str]:
        """ปิดการเทรดทั้งหมด"""
        closed_trades = []
        
        for trade_id, trade in self.monitor.get_active_trades().items():
            current_price = current_prices.get(trade.symbol)
            
            if current_price and self.monitor.close_trade(trade_id, current_price, reason):
                closed_trades.append(trade_id)
        
        logger.info(f"🔒 ปิดการเทรดทั้งหมด: {len(closed_trades)} รายการ")
        return closed_trades
    
    def check_stop_loss_take_profit(self, current_prices: Dict[str, float]) -> List[str]:
        """ตรวจสอบและปิดการเทรดที่ถึง SL/TP"""
        return self.monitor.check_trade_levels(current_prices)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """ดึงสรุปผลการเทรด"""
        daily_summary = self.monitor.get_daily_summary()
        active_trades = self.monitor.get_active_trades()
        
        # เพิ่มข้อมูลการเทรดที่เปิดอยู่
        active_trades_info = []
        for trade_id, trade in active_trades.items():
            active_trades_info.append({
                'trade_id': trade_id,
                'symbol': trade.symbol,
                'position_type': trade.position_type,
                'entry_price': trade.entry_price,
                'entry_time': trade.entry_time.isoformat(),
                'strategy': trade.strategy_name
            })
        
        return {
            'daily_summary': daily_summary,
            'active_trades': active_trades_info,
            'total_active_trades': len(active_trades)
        }
    
    def send_performance_report(self, report_type: str = "daily") -> None:
        """ส่งรายงานผลการเทรด"""
        self.monitor.send_manual_report(report_type)
    
    def create_performance_chart(self, save_path: Optional[str] = None) -> None:
        """สร้างกราฟแสดงผลการเทรด"""
        self.monitor.create_performance_chart(save_path)

def run_automated_trading_session(system: DekTradingSystem, 
                                 duration_hours: int = 24,
                                 check_interval_minutes: int = 15) -> None:
    """
    รันการเทรดอัตโนมัติ
    
    Args:
        system: DekTradingSystem instance
        duration_hours: ระยะเวลาการทำงาน (ชั่วโมง)
        check_interval_minutes: ช่วงเวลาตรวจสอบ (นาที)
    """
    import time
    
    logger.info(f"🤖 เริ่มต้นการเทรดอัตโนมัติ: {duration_hours} ชั่วโมง")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=duration_hours)
    
    while datetime.now() < end_time:
        try:
            # วิเคราะห์สัญญาณ
            recommendation = system.run_trading_analysis()
            
            if 'error' not in recommendation:
                # ตรวจสอบสัญญาณ
                signal = recommendation.get('signal')
                current_price = recommendation.get('current_price')
                
                if signal in ['BUY', 'SELL']:
                    logger.info(f"🎯 ได้สัญญาณ {signal} ที่ราคา {current_price}")
                    
                    # เปิดการเทรดใหม่
                    trade_id = system.execute_trade(recommendation)
                    
                    if trade_id:
                        logger.info(f"✅ เปิดการเทรดสำเร็จ: {trade_id}")
                
                # ตรวจสอบ SL/TP
                if current_price:
                    closed_trades = system.check_stop_loss_take_profit({
                        recommendation.get('symbol', 'XAUUSD'): current_price
                    })
                    
                    if closed_trades:
                        logger.info(f"🔒 ปิดการเทรดอัตโนมัติ: {len(closed_trades)} รายการ")
            
            # รอช่วงเวลาที่กำหนด
            time.sleep(check_interval_minutes * 60)
            
        except Exception as e:
            logger.error(f"❌ Error in automated trading: {e}")
            time.sleep(60)  # รอ 1 นาทีก่อนลองใหม่
    
    logger.info("🏁 จบการเทรดอัตโนมัติ")

# ตัวอย่างการใช้งาน
def example_usage():
    """ตัวอย่างการใช้งานระบบ"""
    
    # สร้างระบบเทรด
    system = DekTradingSystem(
        data_dir="trading_data",
        enable_reporting=True,
        account_balance=10000,
        risk_percent=1.5
    )
    
    print("🚀 ระบบ Dek Trading พร้อมใช้งาน!")
    
    # วิเคราะห์สัญญาณ
    print("\n📊 กำลังวิเคราะห์สัญญาณ...")
    recommendation = system.run_trading_analysis()
    
    if 'error' in recommendation:
        print(f"❌ เกิดข้อผิดพลาด: {recommendation['error']}")
        return
    
    print(f"🎯 สัญญาณ: {recommendation['signal']}")
    print(f"💰 ราคาปัจจุบัน: {recommendation['current_price']}")
    
    # ถ้ามีสัญญาณ BUY/SELL ให้เปิดการเทรด
    if recommendation['signal'] in ['BUY', 'SELL']:
        print(f"\n🔄 กำลังเปิดการเทรด...")
        trade_id = system.execute_trade(recommendation)
        
        if trade_id:
            print(f"✅ เปิดการเทรดสำเร็จ: {trade_id}")
        else:
            print("❌ ไม่สามารถเปิดการเทรดได้")
    
    # แสดงสรุปผลการเทรด
    print("\n📈 สรุปผลการเทรด:")
    summary = system.get_performance_summary()
    daily = summary['daily_summary']
    
    print(f"   📊 การเทรดวันนี้: {daily['total_trades']}")
    print(f"   🎯 Winrate: {daily['winrate']:.1f}%")
    print(f"   💰 PnL: {daily['total_pnl']:.2f}")
    print(f"   🔓 การเทรดที่เปิดอยู่: {daily['active_trades']}")
    
    # ส่งรายงาน
    print("\n📤 ส่งรายงานประจำวัน...")
    system.send_performance_report("daily")

if __name__ == "__main__":
    example_usage()
