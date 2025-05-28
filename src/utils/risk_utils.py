import os
import logging
from dotenv import load_dotenv
from typing import Dict, Tuple, Optional, Union

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default risk parameters (can be overridden in .env)
DEFAULT_RISK_PERCENT = float(os.getenv('DEFAULT_RISK_PERCENT', '1.0'))  # 1% risk per trade by default
DEFAULT_RISK_REWARD_RATIO = float(os.getenv('DEFAULT_RISK_REWARD_RATIO', '2.0'))  # 1:2 risk:reward ratio
MAX_RISK_PERCENT = float(os.getenv('MAX_RISK_PERCENT', '2.0'))  # Max 2% risk per trade

def calculate_stop_loss(entry_price: float, risk_percent: float, is_long: bool) -> float:
    """
    คำนวณจุด Stop Loss จากราคาเข้า และเปอร์เซ็นต์ความเสี่ยงที่ยอมรับได้
    
    Args:
        entry_price: ราคาที่เข้าซื้อ/ขาย
        risk_percent: เปอร์เซ็นต์ความเสี่ยงที่ยอมรับได้ (เช่น 1.0 = 1%)
        is_long: True ถ้าเป็นการซื้อ (Long), False ถ้าเป็นการขาย (Short)
    
    Returns:
        ราคา Stop Loss ที่เหมาะสม
    """
    if risk_percent > MAX_RISK_PERCENT:
        logger.warning(f"Risk percent {risk_percent}% exceeds maximum allowed {MAX_RISK_PERCENT}%. Using maximum.")
        risk_percent = MAX_RISK_PERCENT
    
    if is_long:
        # สำหรับ Long position, Stop Loss อยู่ต่ำกว่าราคาเข้า
        return entry_price * (1 - risk_percent / 100)
    else:
        # สำหรับ Short position, Stop Loss อยู่สูงกว่าราคาเข้า
        return entry_price * (1 + risk_percent / 100)

def calculate_take_profit(entry_price: float, risk_reward_ratio: float, stop_loss: float, is_long: bool) -> float:
    """
    คำนวณจุด Take Profit จาก Risk:Reward Ratio
    
    Args:
        entry_price: ราคาที่เข้าซื้อ/ขาย
        risk_reward_ratio: อัตราส่วนความเสี่ยงต่อผลตอบแทน (เช่น 2.0 = 1:2)
        stop_loss: ราคา Stop Loss
        is_long: True ถ้าเป็นการซื้อ (Long), False ถ้าเป็นการขาย (Short)
    
    Returns:
        ราคา Take Profit ที่เหมาะสม
    """
    risk = abs(entry_price - stop_loss)
    reward = risk * risk_reward_ratio
    
    if is_long:
        # สำหรับ Long position, Take Profit อยู่สูงกว่าราคาเข้า
        return entry_price + reward
    else:
        # สำหรับ Short position, Take Profit อยู่ต่ำกว่าราคาเข้า
        return entry_price - reward

def calculate_position_size(account_balance: float, risk_amount: float, 
                           entry_price: float, stop_loss: float, pip_value: float = 0.1) -> float:
    """
    คำนวณขนาด position ที่เหมาะสมตามหลัก risk management
    
    Args:
        account_balance: ยอดเงินในบัญชี
        risk_amount: จำนวนเงินที่ยอมเสี่ยงต่อการเทรด (หรือเปอร์เซ็นต์ของบัญชี)
        entry_price: ราคาที่เข้าซื้อ/ขาย
        stop_loss: ราคา Stop Loss
        pip_value: มูลค่าต่อ pip (default 0.1 สำหรับ forex standard lot)
    
    Returns:
        ขนาด lot ที่เหมาะสม
    """
    # ถ้า risk_amount เป็นเปอร์เซ็นต์ (น้อยกว่า 100)
    if risk_amount < 100:
        risk_amount = account_balance * (risk_amount / 100)
    
    # จำนวน pips เสี่ยง
    pips_at_risk = abs(entry_price - stop_loss) / pip_value
    
    # คำนวณขนาด lot
    if pips_at_risk > 0:
        lot_size = risk_amount / pips_at_risk
        return round(lot_size, 2)  # ปัดเศษให้เป็น 2 ตำแหน่ง
    return 0.0

def calculate_risk_metrics(entry_price: float, account_balance: float, 
                          risk_percent: float = DEFAULT_RISK_PERCENT,
                          risk_reward_ratio: float = DEFAULT_RISK_REWARD_RATIO,
                          is_long: bool = True,
                          pip_value: float = 0.1) -> Dict[str, Union[float, str]]:
    """
    คำนวณ metrics ทั้งหมดเกี่ยวกับการจัดการความเสี่ยง
    
    Args:
        entry_price: ราคาที่เข้าซื้อ/ขาย
        account_balance: ยอดเงินในบัญชี
        risk_percent: เปอร์เซ็นต์ความเสี่ยงที่ยอมรับได้ (default: 1%)
        risk_reward_ratio: อัตราส่วนความเสี่ยงต่อผลตอบแทน (default: 2.0 = 1:2)
        is_long: True ถ้าเป็นการซื้อ (Long), False ถ้าเป็นการขาย (Short)
        pip_value: มูลค่าต่อ pip
    
    Returns:
        Dictionary ที่มีข้อมูลทั้งหมดเกี่ยวกับการจัดการความเสี่ยง
    """
    # คำนวณ Stop Loss
    stop_loss = calculate_stop_loss(entry_price, risk_percent, is_long)
    
    # คำนวณ Take Profit
    take_profit = calculate_take_profit(entry_price, risk_reward_ratio, stop_loss, is_long)
    
    # คำนวณจำนวนเงินที่เสี่ยง
    risk_amount = account_balance * (risk_percent / 100)
    
    # คำนวณขนาด position
    position_size = calculate_position_size(account_balance, risk_amount, entry_price, stop_loss, pip_value)
    
    # จำนวน pips เสี่ยง
    pips_at_risk = abs(entry_price - stop_loss) / pip_value
    
    # จำนวน pips เป้าหมาย
    target_pips = abs(entry_price - take_profit) / pip_value
    
    return {
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'position_type': 'LONG' if is_long else 'SHORT',
        'risk_percent': risk_percent,
        'risk_amount': risk_amount,
        'risk_reward_ratio': risk_reward_ratio,
        'position_size': position_size,
        'pips_at_risk': pips_at_risk,
        'target_pips': target_pips,
        'potential_profit': risk_amount * risk_reward_ratio,
        'account_balance': account_balance
    }

def format_risk_report(risk_metrics: Dict[str, Union[float, str]]) -> str:
    """
    สร้างรายงานการจัดการความเสี่ยงในรูปแบบข้อความ
    
    Args:
        risk_metrics: Dictionary ที่มีข้อมูลการจัดการความเสี่ยง (จาก calculate_risk_metrics)
    
    Returns:
        ข้อความรายงานสรุปการจัดการความเสี่ยง
    """
    return f"""
📊 Risk Management Report:
🔹 Position: {risk_metrics['position_type']}
🔹 Entry Price: {risk_metrics['entry_price']:.5f}
🛑 Stop Loss: {risk_metrics['stop_loss']:.5f}
🎯 Take Profit: {risk_metrics['take_profit']:.5f}
📈 Risk/Reward: 1:{risk_metrics['risk_reward_ratio']}

💰 Account: ${risk_metrics['account_balance']:.2f}
⚠️ Risk: {risk_metrics['risk_percent']:.2f}% (${risk_metrics['risk_amount']:.2f})
💵 Position Size: {risk_metrics['position_size']:.2f} lots
📏 Pips at Risk: {risk_metrics['pips_at_risk']:.1f}
📏 Target Pips: {risk_metrics['target_pips']:.1f}
💸 Potential Profit: ${risk_metrics['potential_profit']:.2f}
"""

# Example usage
if __name__ == "__main__":
    # Test the functions
    entry_price = 1.10000  # Example entry price for EUR/USD
    account_balance = 10000  # Example account balance
    
    # Calculate risk metrics for a LONG position
    long_metrics = calculate_risk_metrics(
        entry_price=entry_price,
        account_balance=account_balance,
        risk_percent=1.0,
        risk_reward_ratio=2.0,
        is_long=True
    )
    
    # Print the risk report
    print(format_risk_report(long_metrics))
