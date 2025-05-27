def is_good_buy_entry(ohlc_df, price) -> tuple[bool, str]:
    """
    วิเคราะห์จุดเข้าซื้อ: ราคาปัจจุบันต่ำกว่า SMA20 และแท่งล่าสุดเป็นแท่งเขียว (Close > Open)
    สามารถปรับ logic ตามกลยุทธ์จริงได้
    """
    if ohlc_df is None or len(ohlc_df) < 20:
        return False, 'ข้อมูลไม่พอสำหรับวิเคราะห์ SMA20'
    sma20 = ohlc_df['Close'].rolling(window=20).mean()
    last_close = ohlc_df['Close'].iloc[-1]
    last_open = ohlc_df['Open'].iloc[-1]
    if price < sma20.iloc[-1] and last_close > last_open:
        return True, f'ราคาปัจจุบัน ({price}) ต่ำกว่า SMA20 ({sma20.iloc[-1]:.2f}) และแท่งล่าสุดเป็นแท่งเขียว'
    return False, f'ราคาปัจจุบัน ({price}) ไม่เข้าเงื่อนไขเข้าซื้อ (SMA20: {sma20.iloc[-1]:.2f})'
