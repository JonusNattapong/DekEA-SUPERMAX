# DekEA-SUPERMAX

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI-Powered](https://img.shields.io/badge/AI-Powered-green.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📝 รายละเอียดโปรเจค

DekEA-SUPERMAX เป็นระบบอัจฉริยะสำหรับการเทรดและวิเคราะห์ตลาดการเงินที่ขับเคลื่อนด้วย AI โดยใช้ข้อมูลจากหลายแหล่ง (ราคา, ข่าว, sentiment) มาประมวลผลและให้คำแนะนำในการเทรด ระบบประกอบด้วยหลายโมดูลที่ทำงานร่วมกัน ตั้งแต่การดึงข้อมูลราคาและข่าวสาร ไปจนถึงการวิเคราะห์และส่งแจ้งเตือนผ่าน Telegram

### 💡 คุณสมบัติหลัก

- **ดึงข้อมูลราคาจากหลายแหล่ง**: GoldAPI, Alpha Vantage, FreeForexAPI
- **วิเคราะห์ข่าวเศรษฐกิจอัตโนมัติ**: ดึงข่าวล่าสุด, แปลและสรุปด้วย AI
- **การวิเคราะห์ sentiment**: ประเมินความเป็น Bullish/Bearish ของตลาดจากข่าว
- **บริหารความเสี่ยง**: คำนวณ Stop Loss, Take Profit และขนาด Position ที่เหมาะสม
- **กรองข่าวสำคัญ**: หลีกเลี่ยงการเทรดในช่วงข่าวสำคัญที่อาจทำให้ตลาดผันผวน
- **ติดตาม sentiment**: บันทึกและวิเคราะห์เทรนด์ sentiment ต่อเนื่อง
- **แจ้งเตือนผ่าน Telegram**: ส่งข้อมูลวิเคราะห์และแจ้งเตือนผ่าน Telegram Bot

### 🧠 เทคโนโลยี AI ที่ใช้

- **DeepSeek Chat & Reasoner API**: สำหรับการวิเคราะห์ข่าวและสร้างกลยุทธ์การลงทุน
- **Mistral API**: เป็นระบบสำรองในกรณีที่ DeepSeek ไม่ตอบสนอง
- **การประมวลผลภาษาธรรมชาติ (NLP)**: แปลและวิเคราะห์ข่าวเศรษฐกิจ
- **การวิเคราะห์ sentiment**: ตรวจจับความเป็น Bullish/Bearish ของข่าว

## 🚀 การติดตั้ง

1. Clone repository นี้:
```bash
git clone https://github.com/yourusername/DekEA-SUPERMAX.git
cd DekEA-SUPERMAX
```

2. สร้าง virtual environment และติดตั้ง dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # สำหรับ Linux/Mac
# หรือ
.venv\Scripts\activate  # สำหรับ Windows

pip install -r requirements.txt
```

3. สร้างไฟล์ `.env` และกำหนดค่า API keys ที่จำเป็น:
```
# API Keys
GOLDAPI_KEY=your_goldapi_key
ALPHA_VANTAGE_KEY=your_alphavantage_key
FINNHUB_API_KEY=your_finnhub_key
DEEPSEEK_API_KEY=your_deepseek_key
MISTRAL_API_KEY=your_mistral_key

# Telegram Settings
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Risk Management Settings (optional)
DEFAULT_RISK_PERCENT=1.0
DEFAULT_RISK_REWARD_RATIO=2.0
MAX_RISK_PERCENT=2.0
```

## 📊 โครงสร้างโปรเจค

```
DekEA-SUPERMAX/
├── main.py                  # จุดเริ่มต้นรันระบบ/บอทเทรด
├── requirements.txt         # รายการ dependencies
├── .env                     # เก็บ API keys (สร้างเอง)
├── README.md                # คู่มือและรายละเอียดโปรเจกต์
├── sentiment_history.csv    # ไฟล์เก็บประวัติ sentiment (สร้างอัตโนมัติ)
└── src/
    ├── __init__.py
    ├── utils/               # ฟังก์ชัน/ยูทิลิตี้พื้นฐาน
    │   ├── __init__.py
    │   ├── price_utils.py       # ดึงราคาทอง/Forex จากหลาย API (GoldAPI, AlphaVantage ฯลฯ)
    │   ├── news_utils.py        # วิเคราะห์ข่าวด้วย AI (DeepSeek, Mistral, OpenAI)
    │   ├── telegram_utils.py    # ส่งข้อความแจ้งเตือนผ่าน Telegram
    │   ├── risk_utils.py        # คำนวณ SL/TP, จัดการความเสี่ยง
    │   ├── ohlc_utils.py        # เครื่องมือจัดการข้อมูลราคา OHLC
    │   └── chart_utils.py       # ฟังก์ชัน plot/chart
    ├── feature/             # ฟีเจอร์ขั้นสูง/AI
    │   ├── __init__.py
    │   └── sentiment_tracker.py # วิเคราะห์ sentiment และเทรนด์ข่าว
    ├── filter/              # ฟิลเตอร์/กรองข่าวหรือช่วงเวลาที่ควรหลีกเลี่ยง
    │   ├── __init__.py
    │   └── news_filter.py       # ฟังก์ชันกรองข่าวสำคัญและ format รายงานข่าว
    ├── algorithms/          # กลยุทธ์เทรดและ ML/AI
    │   ├── __init__.py
    │   └── trading_algorithms.py # รวมอัลกอริทึมเทรด, ML, Deep Learning
    ├── backtest/            # ระบบ backtesting
    │   ├── __init__.py
    │   └── backtester.py        # ทดสอบกลยุทธ์ย้อนหลัง/วิเคราะห์ performance
    ├── bot/                 # (option) โค้ดสำหรับ integration กับบอทหรือ automation อื่นๆ
    │   ├── __init__.py
    │   └── gold_bot.py          # ตัวอย่าง Telegram/Gold bot
    ├── entry_logic.py        # Logic การเข้าออเดอร์ (Entry/Exit)
    ├── gold_analysis.py      # วิเคราะห์ข่าวทอง, event, ฟีเจอร์พิเศษ
    ├── ml_utils.py           # ฟังก์ชัน ML/Deep Learning/Auto-tuning
```

- ทุกโฟลเดอร์ย่อยใน `src/` มีไฟล์ `__init__.py` เพื่อรองรับการ import แบบ package
- สามารถขยาย/เพิ่มโมดูลใหม่ได้ง่าย รองรับโค้ดแบบ modular
- ตัวอย่างการ import: `from src.utils.price_utils import get_xauusd_price_alpha`

## 🎮 การใช้งาน

### ดึงข้อมูลราคาและวิเคราะห์ข่าวล่าสุด

รันไฟล์ `main.py` เพื่อเริ่มต้นการทำงานของระบบ:

```bash
python main.py
```

ระบบจะดึงข้อมูลราคาทองและข่าวล่าสุด วิเคราะห์ด้วย AI และส่งข้อมูลไปยัง Telegram

### การจัดการความเสี่ยง

```python
from src.risk_utils import calculate_risk_metrics, format_risk_report

# คำนวณ SL/TP และขนาด Position ที่เหมาะสม
risk_data = calculate_risk_metrics(
    entry_price=1900.50,
    account_balance=10000,
    risk_percent=1.0,
    risk_reward_ratio=2.0,
    is_long=True
)

# สร้างรายงานสรุปการจัดการความเสี่ยง
risk_report = format_risk_report(risk_data)
print(risk_report)
```

### กรองช่วงเวลาข่าวสำคัญ

```python
from src.news_filter import should_avoid_trading, format_news_report

# ตรวจสอบว่าควรหลีกเลี่ยงการเทรดในขณะนี้หรือไม่
news_status = should_avoid_trading("XAUUSD")
if news_status['should_avoid']:
    print("ควรหลีกเลี่ยงการเทรดในขณะนี้เนื่องจากมีข่าวสำคัญ")

# สร้างรายงานข่าวสำคัญที่กำลังจะเกิดขึ้น
news_report = format_news_report(news_status)
print(news_report)
```

### ติดตาม Sentiment

```python
from src.sentiment_tracker import track_sentiment, get_sentiment_trend, format_sentiment_report

# บันทึก sentiment จากข่าวล่าสุด
news_text = "Gold prices rose as investors sought safe-haven assets amid economic uncertainty."
track_sentiment(news_text, "XAUUSD")

# วิเคราะห์เทรนด์ sentiment ในช่วง 7 วันที่ผ่านมา
trend = get_sentiment_trend("XAUUSD", days=7)
trend_report = format_sentiment_report(trend)
print(trend_report)
```

## 📚 APIs ที่ใช้

- [GoldAPI](https://www.goldapi.io/) - ข้อมูลราคาทอง
- [Alpha Vantage](https://www.alphavantage.co/) - ข้อมูลราคา forex และสินทรัพย์อื่นๆ
- [Finnhub](https://finnhub.io/) - ข่าวเศรษฐกิจล่าสุด
- [DeepSeek API](https://deepseek.com/) - วิเคราะห์ข่าวและ sentiment ด้วย AI
- [Mistral API](https://mistral.ai/) - ระบบ AI สำรอง
- [Telegram Bot API](https://core.telegram.org/bots/api) - ส่งการแจ้งเตือน

## ข้อจำกัดความรับผิดชอบ

ซอฟต์แวร์นี้มีไว้เพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น อย่าเสี่ยงกับเงินที่คุณกลัวที่จะสูญเสีย ใช้ซอฟต์แวร์นี้ด้วยความเสี่ยงของคุณเอง ผู้เขียนและ บริษัท ในเครือทั้งหมดจะไม่รับผิดชอบต่อผลการซื้อขายของคุณ

เริ่มต้นจากการเรียกใช้บอทซื้อขายในการทดสอบก่อน และอย่าใช้เงินจริงจนกว่าคุณจะเข้าใจวิธีการทำงานและผลกำไร / ขาดทุนที่คุณควรคาดหวัง

เราขอแนะนำอย่างยิ่งให้คุณมีทักษะการเขียนโค้ดขั้นพื้นฐานและความรู้เกี่ยวกับ Python อย่าลังเลที่จะอ่านซอร์สโค้ดและทำความเข้าใจกลไกของบอทนี้ อัลกอริธึม และเทคนิคที่ใช้ในการทำงาน

## DISCLAIMER

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

Always start by running a trading bot in Dry-run and do not engage money before you understand how it works and what profit/loss you should expect.

We strongly recommend you to have basic coding skills and Python knowledge. Do not hesitate to read the source code and understand the mechanisms of this bot, algorithms and techniques implemented in it.

## 📄 License

MIT License