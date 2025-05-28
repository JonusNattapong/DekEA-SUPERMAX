import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import requests
import os
import pandas as pd
from dotenv import load_dotenv

# Load .env environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def plot_and_send_chart_tradingview_style(ohlc_df: pd.DataFrame, logo_path: str | None = None, symbol: str = 'XAUUSD') -> None:
    """วาดกราฟแท่งเทียนและส่งไป Telegram"""
    
    if not pd.api.types.is_datetime64_any_dtype(ohlc_df.index):
        raise ValueError("Index ของ ohlc_df ต้องเป็น datetime")

    fig, ax = plt.subplots(figsize=(16, 8))
    width = 0.8
    wick_width = 0.15

    for i, (idx, row) in enumerate(ohlc_df.iterrows()):
        color = '#26a69a' if row['Close'] >= row['Open'] else '#ef5350'
        ax.vlines(i, row['Low'], row['High'], color=color, linewidth=wick_width * 10, zorder=2)
        ax.add_patch(
            patches.Rectangle(
                (i - width / 2, min(row['Open'], row['Close'])),
                width,
                max(abs(row['Close'] - row['Open']), 0.01),
                facecolor=color, alpha=0.95, zorder=3, linewidth=1, edgecolor='black'
            )
        )

    price_min = ohlc_df['Low'].min()
    price_max = ohlc_df['High'].max()
    target_min = price_min + (price_max - price_min) * 0.3
    target_max = price_min + (price_max - price_min) * 0.5
    entry = (target_min + target_max) / 2
    tp = price_max * 0.995
    sl = price_min * 1.005

    ax.axhspan(target_min, target_max, facecolor='#ffe066', alpha=0.6, zorder=1, linewidth=2, edgecolor='black')
    ax.hlines([target_min, target_max], -1, len(ohlc_df) + 2, color='black', linewidth=1, zorder=2)
    ax.text(len(ohlc_df)//2, entry, 'TARGET ZONE', fontsize=20, color='black', ha='center', va='center', weight='bold', zorder=5)

    box_x = len(ohlc_df) - 3
    ax.add_patch(patches.Rectangle((box_x - 0.25, entry), 0.5, tp - entry, facecolor='#43a047', alpha=0.7, edgecolor='black', linewidth=2, zorder=4))
    ax.text(box_x, tp, 'TP', color='white', fontsize=14, ha='center', va='bottom', weight='bold', zorder=5)

    ax.add_patch(patches.Rectangle((box_x - 0.25, sl), 0.5, entry - sl, facecolor='#d32f2f', alpha=0.7, edgecolor='black', linewidth=2, zorder=4))
    ax.text(box_x, sl, 'SL', color='white', fontsize=14, ha='center', va='top', weight='bold', zorder=5)

    # Styling
    fig.patch.set_facecolor('#f4f4f4')
    ax.set_facecolor('#f4f4f4')
    ax.set_title(symbol, fontsize=32, weight='bold', pad=30)
    ax.text(0, price_min - (price_max - price_min) * 0.10, 'Like And Subscribe', fontsize=18, color='gray', weight='bold', ha='left', va='bottom')

    if logo_path and os.path.isfile(logo_path):
        try:
            img = plt.imread(logo_path)
            fig.figimage(img, xo=80, yo=350, alpha=0.7, zorder=10)
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลดโลโก้ได้: {e}")

    ax.set_xlim(-1, len(ohlc_df) + 2)
    ax.set_xticks(range(len(ohlc_df)))
    ax.set_xticklabels([d.strftime('%b %d') for d in ohlc_df.index], rotation=45, fontsize=12)
    ax.set_ylabel('Price', fontsize=16, weight='bold')
    ax.tick_params(axis='y', labelsize=14)
    for spine in ax.spines.values():
        spine.set_linewidth(2)

    plt.tight_layout()

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    # Send to Telegram
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {'photo': buf}
    data = {'chat_id': TELEGRAM_CHAT_ID}
    response = requests.post(url, files=files, data=data, timeout=10)

    if not response.ok:
        raise RuntimeError(f"❌ Telegram API Error: {response.status_code} {response.text}")

    print("✅ ส่งภาพกราฟไปยัง Telegram เรียบร้อยแล้ว")

# ตัวอย่างการรันเมื่อเรียกตรง
if __name__ == "__main__":
    import yfinance as yf
    df = yf.download('XAUUSD=X', period='15d', interval='1d')
    df = df[['Open', 'High', 'Low', 'Close']]
    df.dropna(inplace=True)
    plot_and_send_chart_tradingview_style(df, logo_path=None, symbol='XAUUSD')
