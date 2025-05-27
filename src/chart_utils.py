import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import requests
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def plot_and_send_chart_tradingview_style(ohlc_df: pd.DataFrame, logo_path: str | None = None, symbol: str = 'XAUUSD') -> None:
    """วาดกราฟแท่งเทียนสไตล์ TradingView และส่งภาพไป Telegram"""
    fig, ax = plt.subplots(figsize=(16, 8))
    width = 0.8
    wick_width = 0.15
    for i, (idx, row) in enumerate(ohlc_df.iterrows()):
        color = '#008000' if row['Close'] >= row['Open'] else '#d32f2f'
        ax.vlines(i, row['Low'], row['High'], color=color, linewidth=wick_width*10, zorder=2)
        ax.add_patch(
            patches.Rectangle(
                (i-width/2, min(row['Open'], row['Close'])),
                width,
                max(abs(row['Close']-row['Open']), 0.01),
                facecolor=color, alpha=0.95, zorder=3, linewidth=1, edgecolor='black'
            )
        )
    target_min = ohlc_df['Low'].min() + (ohlc_df['High'].max()-ohlc_df['Low'].min())*0.3
    target_max = ohlc_df['Low'].min() + (ohlc_df['High'].max()-ohlc_df['Low'].min())*0.5
    ax.axhspan(target_min, target_max, facecolor='#ffe066', alpha=0.7, zorder=1, linewidth=2, edgecolor='black')
    ax.hlines([target_min, target_max], -1, len(ohlc_df)+2, color='black', linewidth=1, zorder=2)
    ax.text(len(ohlc_df)//2, (target_min+target_max)/2, 'TARGET LEVEL', fontsize=22, color='black', weight='bold', ha='center', va='center', zorder=10)
    tp = ohlc_df['High'].max() * 0.995
    sl = ohlc_df['Low'].min() * 1.005
    entry = (target_min+target_max)/2
    box_x = len(ohlc_df)-3
    ax.add_patch(patches.Rectangle((box_x-0.25, entry), 0.5, tp-entry, facecolor='#43a047', alpha=0.7, zorder=4, edgecolor='black', linewidth=2))
    ax.text(box_x, tp, 'TP', color='white', fontsize=14, ha='center', va='bottom', weight='bold', zorder=5)
    ax.add_patch(patches.Rectangle((box_x-0.25, sl), 0.5, entry-sl, facecolor='#d32f2f', alpha=0.7, zorder=4, edgecolor='black', linewidth=2))
    ax.text(box_x, sl, 'SL', color='white', fontsize=14, ha='center', va='top', weight='bold', zorder=5)
    fig.patch.set_facecolor('#aaffcc')
    ax.set_facecolor('#aaffcc')
    ax.text(0, ohlc_df['Low'].min()-((ohlc_df['High'].max()-ohlc_df['Low'].min())*0.10), 'Like And Subscribe', fontsize=22, color='black', weight='bold', ha='left', va='bottom', zorder=10)
    ax.set_title(symbol, fontsize=36, weight='bold', pad=30)
    if logo_path:
        img = plt.imread(logo_path)
        fig.figimage(img, xo=80, yo=350, alpha=0.8, zorder=10)
    ax.set_xlim(-1, len(ohlc_df)+2)
    ax.set_xticks(range(len(ohlc_df)))
    ax.set_xticklabels([d.strftime('%b %d') for d in ohlc_df.index], rotation=45, fontsize=12)
    ax.set_ylabel('Price', fontsize=20, weight='bold')
    ax.tick_params(axis='y', labelsize=14)
    for spine in ax.spines.values():
        spine.set_linewidth(2)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError('Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment variables')
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'
    files = {'photo': buf}
    data = {'chat_id': TELEGRAM_CHAT_ID}
    requests.post(url, files=files, data=data, timeout=10)
