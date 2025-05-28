from enum import Enum
import pandas as pd

class TradingStrategy(Enum):
    SCALPING = "Scalping"
    DAY_TRADING = "Day Trading"
    SWING_TRADING = "Swing Trading"
    POSITION_TRADING = "Position Trading"

def get_strategy_description(strategy: TradingStrategy) -> str:
    if strategy == TradingStrategy.SCALPING:
        return "เทรดเร็วภายในไม่กี่นาที มือไว / ข่าวแรง"
    elif strategy == TradingStrategy.DAY_TRADING:
        return "เปิด–ปิดออเดอร์ในวันเดียว คนดูหน้าจอได้ทั้งวัน"
    elif strategy == TradingStrategy.SWING_TRADING:
        return "ถือข้ามวัน–สัปดาห์ เน้นจังหวะราคากลับตัว คนมีเวลาบ้างแต่ไม่เต็มวัน"
    elif strategy == TradingStrategy.POSITION_TRADING:
        return "ถือยาวเป็นเดือน/ปี นักลงทุนระยะยาว"
    return "ไม่พบกลยุทธ์"

def is_good_buy_entry(ohlc_df, price, strategy: TradingStrategy) -> tuple[bool, str]:
    """
    วิเคราะห์จุดเข้าซื้อตามกลยุทธ์ที่เลือก
    """
    if ohlc_df is None or len(ohlc_df) < 20: # Ensure enough data for SMA20
        return False, 'ข้อมูลไม่พอสำหรับวิเคราะห์'

    description = get_strategy_description(strategy)
    entry_message = f"กลยุทธ์: {strategy.value} ({description})\n"

    # Default logic (can be customized per strategy)
    sma20 = ohlc_df['Close'].rolling(window=20).mean()
    last_close = ohlc_df['Close'].iloc[-1]
    last_open = ohlc_df['Open'].iloc[-1]
    current_sma20 = sma20.iloc[-1]

    if strategy == TradingStrategy.SCALPING:
        # Scalping: อาจจะเน้น momentum หรือ breakout ระยะสั้นมากๆ
        # ตัวอย่าง: ราคาปัจจุบันทะลุ high ของแท่งก่อนหน้า และ volume สูง (สมมติว่ามีข้อมูล volume)
        # หรือ RSI < 30 (oversold) ใน timeframe เล็กมากๆ
        # ในที่นี้จะใช้ logic คล้ายเดิมแต่ปรับเงื่อนไข
        if price > last_open and price > current_sma20: # สมมติว่าต้องการเข้าเมื่อราคามีแนวโน้มขึ้นเร็ว
            return True, entry_message + f"ราคาปัจจุบัน ({price}) สูงกว่าราคาเปิด ({last_open}) และ SMA20 ({current_sma20:.2f})"
        return False, entry_message + f"ราคาปัจจุบัน ({price}) ไม่เข้าเงื่อนไข Scalping (SMA20: {current_sma20:.2f})"

    elif strategy == TradingStrategy.DAY_TRADING:
        # Day Trading: คล้ายๆ Scalping แต่อาจจะถือยาวกว่าหน่อยภายในวัน
        # อาจจะใช้ SMA ตัดกัน หรือดูแนวรับแนวต้านของวัน
        if price < current_sma20 and last_close > last_open:
            return True, entry_message + f"ราคาปัจจุบัน ({price}) ต่ำกว่า SMA20 ({current_sma20:.2f}) และแท่งล่าสุดเป็นแท่งเขียว"
        return False, entry_message + f"ราคาปัจจุบัน ({price}) ไม่เข้าเงื่อนไข Day Trading (SMA20: {current_sma20:.2f})"

    elif strategy == TradingStrategy.SWING_TRADING:
        # Swing Trading: เน้นการกลับตัว อาจจะดู RSI divergence, MACD crossover, หรือแนวรับแนวต้านสำคัญใน TF day/week
        # ตัวอย่าง: ราคาแตะ SMA50 หรือ SMA200 แล้วมีสัญญาณกลับตัว
        sma50 = ohlc_df['Close'].rolling(window=50).mean()
        current_sma50 = sma50.iloc[-1] if len(sma50) > 0 and not pd.isna(sma50.iloc[-1]) else price # fallback
        if price < current_sma50 and last_close > last_open and price > current_sma20 : # รอราคาย่อมาใกล้ SMA50 แต่ยังอยู่เหนือ SMA20
            return True, entry_message + f"ราคาปัจจุบัน ({price}) ใกล้ SMA50 ({current_sma50:.2f}) และเกิดแท่งเขียวเหนือ SMA20 ({current_sma20:.2f})"
        return False, entry_message + f"ราคาปัจจุบัน ({price}) ไม่เข้าเงื่อนไข Swing Trading (SMA20: {current_sma20:.2f}, SMA50: {current_sma50:.2f})"

    elif strategy == TradingStrategy.POSITION_TRADING:
        # Position Trading: ดูภาพรวมระยะยาว อาจจะใช้ Fundamental ประกอบ หรือ MA เส้นยาวๆ เช่น SMA200
        # ตัวอย่าง: ราคาอยู่เหนือ SMA200 และมีการย่อตัวลงมาทดสอบ SMA200 แล้วเด้งขึ้น
        sma200 = ohlc_df['Close'].rolling(window=200).mean()
        current_sma200 = sma200.iloc[-1] if len(sma200) > 0 and not pd.isna(sma200.iloc[-1]) else price # fallback
        if price > current_sma200 and price < current_sma50 and last_close > last_open: # ราคาย่อมาที่โซนระหว่าง SMA200 กับ SMA50
            return True, entry_message + f"ราคาปัจจุบัน ({price}) อยู่เหนือ SMA200 ({current_sma200:.2f}) และย่อตัวใกล้ SMA50 ({current_sma50:.2f}) พร้อมแท่งเขียว"
        return False, entry_message + f"ราคาปัจจุบัน ({price}) ไม่เข้าเงื่อนไข Position Trading (SMA50: {current_sma50:.2f}, SMA200: {current_sma200:.2f})"

    return False, entry_message + "ไม่พบ Logic สำหรับกลยุทธ์นี้"
