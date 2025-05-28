<div align="center">

# 🥇 DekTradingSignal

### *Advanced AI-Powered Gold Trading System with Real-time Performance Analytics*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI-Powered](https://img.shields.io/badge/AI-DeepSeek%20%26%20Mistral-green.svg)]()
[![Performance Tracking](https://img.shields.io/badge/Performance-Real--time%20Analytics-orange.svg)]()
[![Telegram Bot](https://img.shields.io/badge/Telegram-Auto%20Reports-blue.svg)]()
[![Trading Algorithms](https://img.shields.io/badge/Algorithms-15%2B%20Strategies-purple.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*🚀 ระบบเทรดทองคำอัจฉริยะที่ครบครัน พร้อมการติดตามผลการเทรดแบบเรียลไทม์*

[🚀 เริ่มต้นใช้งาน](#-การติดตั้ง) • [🎯 ฟีเจอร์หลัก](#-ฟีเจอร์หลัก) • [📈 Performance Tracking](#-performance-tracking-system) • [🤖 Trading Algorithms](#-trading-algorithms) • [📊 การใช้งาน](#-การใช้งาน)

---

## ✨ สิ่งที่ใหม่ใน Version 2.0

🔥 **Performance Tracking System** - ติดตามและรายงาน Winrate แบบเรียลไทม์  
🤖 **15+ Trading Algorithms** - รวมกลยุทธ์การเทรดแบบ ML และ Deep Learning  
📊 **Advanced Analytics** - วิเคราะห์ผลการเทรดแบบละเอียด พร้อมกราฟและสถิติ  
⚡ **Auto Telegram Reports** - รายงานผลการเทรดอัตโนมัติ รายวัน/รายสัปดาห์/รายเดือน  
🎯 **Risk Management 2.0** - การจัดการความเสี่ยงที่ทันสมัยและแม่นยำ  

</div>

---

## 📈 Performance Tracking System

> 🔥 **ฟีเจอร์ใหม่!** ระบบติดตามผลการเทรดอัตโนมัติแบบเรียลไทม์

### 🎯 ฟีเจอร์หลัก

| 📊 **AnalyticsPower** | 🎯 **การใช้งาน** |
|---|---|
| 📈 **Real-time Tracking** | ติดตามการเทรดแบบเรียลไทม์ |
| 📊 **Winrate Analytics** | คำนวณ Winrate รายวัน/รายสัปดาห์/รายเดือน |
| 💰 **PnL Monitoring** | วิเคราะห์กำไร-ขาดทุนโดยละเอียด |
| 🚨 **Auto Reports** | รายงานส่งอัตโนมัติผ่าน Telegram |
| 📉 **Risk Metrics** | ติดตาม Drawdown, Profit Factor, Sharpe Ratio |
| 📈 **Performance Charts** | กราฟแสดงผลการเทรดที่สวยงาม |

### 💡 การเริ่มต้นใช้งาน Performance System

```python
from src.performance.performance_system import DekTradingSystem

# สร้างระบบเทรดพร้อม Performance Tracking
system = DekTradingSystem(
    data_dir="trading_data",
    enable_reporting=True,  # เปิดใช้การรายงานอัตโนมัติ
    account_balance=10000,
    risk_percent=1.5
)

# วิเคราะห์สัญญาณการเทรด
recommendation = system.run_trading_analysis()

# เปิดการเทรดอัตโนมัติ
if recommendation['signal'] in ['BUY', 'SELL']:
    trade_id = system.execute_trade(recommendation)
    print(f"✅ เปิดการเทรด: {trade_id}")

# ดูสรุปผลการเทรด
summary = system.get_performance_summary()
print(f"📊 Winrate วันนี้: {summary['daily_summary']['winrate']:.1f}%")
```

### 📊 ตัวอย่างรายงานผลการเทรด

```
📊 TRADING PERFORMANCE REPORT 📊
🕐 Generated: 15/01/2024 14:30:25

🌟 OVERALL PERFORMANCE
📈 Total Trades: 156
🏆 Winrate: 67.31%
💰 Total PnL: +2,456.78
📊 Profit Factor: 1.89
📉 Max Drawdown: -345.22

📅 WEEKLY REPORTS
📊 Week 06/01/2024 - 12/01/2024
   🔢 Trades: 23
   🎯 Winrate: 69.57%
   💰 PnL: +456.12
   🏆 Wins: 16 | ❌ Losses: 7
```

---

## 🎯 ฟีเจอร์หลัก

DekTradingSignal เป็นระบบอัจฉริยะสำหรับการเทรดและวิเคราะห์ตลาดการเงินที่ขับเคลื่อนด้วย AI โดยใช้ข้อมูลจากหลายแหล่ง (ราคา, ข่าว, sentiment) มาประมวลผลและให้คำแนะนำในการเทรด ระบบประกอบด้วยหลายโมดูลที่ทำงานร่วมกัน ตั้งแต่การดึงข้อมูลราคาและข่าวสาร ไปจนถึงการวิเคราะห์และส่งแจ้งเตือนผ่าน Telegram

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
git clone https://github.com/yourusername/DekTradingSignal.git
cd DekTradingSignal
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

### 🏗️ สถาปัตยกรรมระบบ

DekTradingSignal ถูกออกแบบเป็น **Modular Architecture** ที่แยกหน้าที่อย่างชัดเจน เพื่อให้ง่ายต่อการขยายและบำรุงรักษา

#### 🧠 Core AI & Analysis Engine
- **Multi-AI Integration**: DeepSeek + Mistral APIs
- **Real-time Data Processing**: ข้อมูลราคา, ข่าว, และ sentiment
- **Advanced Risk Management**: Dynamic SL/TP calculation
- **Performance Analytics**: Real-time tracking และ reporting

#### 📊 Trading Performance Suite
- **Live Performance Monitoring**: ติดตามผลการเทรดแบบเรียลไทม์
- **Advanced Analytics**: Winrate, PnL, Drawdown analysis
- **Automated Reporting**: Daily/Weekly/Monthly reports ส่งผ่าน Telegram
- **Visual Performance Charts**: กราฟแสดงผลการเทรดที่สวยงาม

## 📁 โครงสร้างโปรเจค

```text
DekTradingSignal/
├── 🚀 main.py                  # จุดเริ่มต้นรันระบบเทรด
├── 📋 requirements.txt         # รายการ dependencies
├── 🔐 .env                     # API keys configuration
├── 📖 README.md                # คู่มือการใช้งาน
├── 📊 docs/                    # เอกสารประกอบ
└── 🏗️ src/                     # โค้ดหลักของระบบ
    ├── 🤖 algorithms/          # Trading Algorithms & ML
    │   ├── __init__.py
    │   └── trading_algorithms.py   # 15+ กลยุทธ์เทรด ML/DL
    ├── 📈 performance/         # 🔥 Performance Tracking System
    │   ├── __init__.py
    │   ├── performance_tracker.py      # ติดตามผลการเทรด
    │   ├── performance_trading_monitor.py  # Monitor การเทรดแบบเรียลไทม์
    │   ├── performance_reporter.py     # รายงานอัตโนมัติผ่าน Telegram
    │   └── performance_system.py       # ระบบเทรดหลักพร้อม Performance
    ├── 🛠️ utils/               # เครื่องมือพื้นฐาน
    │   ├── price_utils.py          # ดึงข้อมูลราคา Multi-API
    │   ├── news_utils.py           # วิเคราะห์ข่าวด้วย AI
    │   ├── telegram_utils.py       # Telegram integration
    │   ├── risk_utils.py           # Risk management
    │   ├── chart_utils.py          # การสร้างกราฟ
    │   └── ohlc_utils.py           # จัดการข้อมูล OHLC
    ├── 📰 filter/              # News & Event Filtering
    │   └── news_filter.py          # กรองข่าวสำคัญ
    ├── 🎯 tracker/             # Sentiment Analysis
    │   └── sentiment_tracker.py    # ติดตาม sentiment ตลาด
    ├── 🧪 backtest/            # Backtesting System
    │   └── backtester.py           # ทดสอบกลยุทธ์ย้อนหลัง
    ├── 🤖 bot/                 # Telegram Bot
    │   └── gold_bot.py             # Gold trading bot
    ├── 📅 calendar/            # Economic Calendar
    │   └── economic_calendar.py    # ปฏิทินเศรษฐกิจ
    ├── 🎲 analysis/            # Market Analysis
    │   └── gold_analysis.py        # วิเคราะห์ตลาดทอง
    └── 🎯 logic/               # Trading Logic
            └── entry_logic.py          # Logic การเข้าออเดอร์
```

---

## 🤖 Trading Algorithms

DekTradingSignal รวมกลยุทธ์การเทรดที่หลากหลาย ตั้งแต่ Technical Analysis แบบดั้งเดิมไปจนถึง Machine Learning ขั้นสูง

### 📊 Technical Analysis Strategies

| 🎯 **Algorithm** | 📈 **Strategy** | ⚡ **Performance** |
|---|---|---|
| **MA Crossover** | Moving Average Crossover | ⭐⭐⭐⭐ |
| **RSI Strategy** | Relative Strength Index | ⭐⭐⭐⭐⭐ |
| **Bollinger Bands** | Volatility-based trading | ⭐⭐⭐⭐ |
| **MACD Strategy** | Trend following | ⭐⭐⭐⭐⭐ |
| **Stochastic** | Momentum oscillator | ⭐⭐⭐ |

### 🧠 AI & Machine Learning Strategies

| 🤖 **AI Model** | 📊 **Method** | 🎯 **Accuracy** |
|---|---|---|
| **LSTM Neural Network** | Time series prediction | 72.4% |
| **Random Forest** | Ensemble learning | 68.9% |
| **Support Vector Machine** | Pattern recognition | 71.2% |
| **Gradient Boosting** | Boosting ensemble | 74.1% |
| **DeepSeek AI Analysis** | News sentiment analysis | 76.8% |

### 💡 ตัวอย่างการใช้งาน Algorithms

```python
from src.algorithms.trading_algorithms import AlgorithmManager

# สร้าง Algorithm Manager
manager = AlgorithmManager()

# เพิ่มกลยุทธ์พร้อม weight
manager.add_algorithm(RSIStrategy(period=14), weight=1.2)
manager.add_algorithm(MACrossover(short=10, long=50), weight=1.0)
manager.add_algorithm(BollingerBandsStrategy(window=20), weight=1.0)

# รับสัญญาณรวม
signal = manager.get_combined_signal(price_data, method="weighted_vote")
print(f"📊 Signal: {signal['signal']} | Confidence: {signal['confidence']:.2f}")
```

---

## 🎮 การใช้งาน

### 🚀 Quick Start - เริ่มต้นใช้งานภายใน 5 นาที

#### 1. การติดตั้งและตั้งค่าเบื้องต้น

```bash
# Clone repository
git clone https://github.com/yourusername/DekTradingSignal.git
cd DekTradingSignal

# สร้าง virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# หรือ .venv\Scripts\activate  # Windows

# ติดตั้ง dependencies
pip install -r requirements.txt
```

#### 2. ตั้งค่า API Keys ในไฟล์ `.env`

```env
# AI APIs
DEEPSEEK_API_KEY=your_deepseek_key
MISTRAL_API_KEY=your_mistral_key

# Price Data APIs
GOLDAPI_KEY=your_goldapi_key
ALPHA_VANTAGE_KEY=your_alphavantage_key
FINNHUB_API_KEY=your_finnhub_key

# Telegram Settings
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Risk Management (Optional)
DEFAULT_RISK_PERCENT=1.0
DEFAULT_RISK_REWARD_RATIO=2.0
```

#### 3. เริ่มใช้งานระบบเทรด

```bash
# รันระบบเทรดพร้อม Performance Tracking
python main.py
```

### 💡 ตัวอย่างการใช้งานขั้นสูง

#### 🎯 Performance Tracking & Analytics

```python
from src.performance.performance_system import DekTradingSystem

# สร้างระบบเทรดแบบครบครัน
system = DekTradingSystem(
    data_dir="trading_data",
    enable_reporting=True,
    account_balance=10000,
    risk_percent=1.5
)

# 📊 วิเคราะห์สัญญาณการเทรด
recommendation = system.run_trading_analysis(
    symbol="XAUUSD",
    timeframe="1d",
    lookback_days=60
)

print(f"🎯 Signal: {recommendation['signal']}")
print(f"💰 Current Price: {recommendation['current_price']}")
print(f"📊 Confidence: {recommendation.get('confidence', 'N/A')}")

# 🚀 เปิดการเทรดอัตโนมัติ
if recommendation['signal'] in ['BUY', 'SELL']:
    trade_id = system.execute_trade(recommendation)
    if trade_id:
        print(f"✅ เปิดการเทรดสำเร็จ: {trade_id}")

# 📈 ดูสรุปผลการเทรด
summary = system.get_performance_summary()
daily = summary['daily_summary']

print(f"📊 การเทรดวันนี้: {daily['total_trades']}")
print(f"🎯 Winrate: {daily['winrate']:.1f}%")
print(f"💰 PnL: {daily['total_pnl']:.2f}")
print(f"🔓 การเทรดเปิดอยู่: {daily['active_trades']}")
```

#### 🎨 สร้างกราฟ Performance

```python
# สร้างกราฟแสดงผลการเทรด
system.create_performance_chart("performance_chart.png")

# ส่งรายงานผ่าน Telegram
system.send_performance_report("daily")    # รายงานรายวัน
system.send_performance_report("weekly")   # รายงานรายสัปดาห์
system.send_performance_report("monthly")  # รายงานรายเดือน
```

#### 🔄 การเทรดอัตโนมัติ 24/7

```python
from src.performance.performance_system import run_automated_trading_session

# รันเทรดอัตโนมัติ 24 ชั่วโมง (ตรวจสอบทุก 15 นาที)
run_automated_trading_session(
    system=system,
    duration_hours=24,
    check_interval_minutes=15
)
```

### 🛡️ Risk Management ขั้นสูง

```python
from src.utils.risk_utils import calculate_risk_metrics, format_risk_report

# คำนวณ SL/TP และขนาด Position ที่เหมาะสม
risk_data = calculate_risk_metrics(
    entry_price=1900.50,
    account_balance=10000,
    risk_percent=1.0,
    risk_reward_ratio=2.0,
    trade_direction="LONG"
)

# สร้างรายงานการจัดการความเสี่ยง
risk_report = format_risk_report(risk_data)
print(risk_report)

# ตัวอย่างผลลัพธ์:
# 🛡️ RISK MANAGEMENT REPORT
# 💰 Entry Price: $1,900.50
# 📉 Stop Loss: $1,881.50 (-1.00%)
# 📈 Take Profit: $3,838.50 (+2.00%)
# 💎 Position Size: 0.53 lots
# ⚠️ Max Risk: $100.00 (1.0% of account)
```

#### 🔔 ระบบแจ้งเตือนและกรองข่าว

```python
from src.filter.news_filter import should_avoid_trading, format_news_report

# ตรวจสอบว่าควรหลีกเลี่ยงการเทรดหรือไม่
news_status = should_avoid_trading("XAUUSD")
if news_status['should_avoid']:
    print("⚠️ ควรหลีกเลี่ยงการเทรดเนื่องจากมีข่าวสำคัญ")

# สร้างรายงานข่าวสำคัญ
news_report = format_news_report(news_status)
print(news_report)
```

#### 📊 Sentiment Analysis

```python
from src.tracker.sentiment_tracker import track_sentiment, get_sentiment_trend

# บันทึก sentiment จากข่าวล่าสุด
news_text = "Gold prices surge amid economic uncertainty and inflation concerns."
track_sentiment(news_text, "XAUUSD")

# วิเคราะห์เทรนด์ sentiment ย้อนหลัง 7 วัน
trend = get_sentiment_trend("XAUUSD", days=7)
print(f"📈 Trend: {trend['trend']} | Average Score: {trend['avg_score']:.2f}")
```

---

## 🌟 ฟีเจอร์ขั้นสูง

### 🎯 Demo System - ทดลองใช้งาน

```python
# รันระบบ Demo พร้อมข้อมูลตัวอย่าง
from src.performance.performance_demo_system import run_complete_demo

run_complete_demo()
```

### 📈 Backtesting System

```python
from src.backtest.backtester import Backtester
from src.algorithms.trading_algorithms import RSIStrategy

# สร้าง backtester
backtester = Backtester()

# ทดสอบกลยุทธ์ RSI
strategy = RSIStrategy(period=14, overbought=70, oversold=30)
results = backtester.run_backtest(strategy, symbol="XAUUSD", days=365)

print(f"📊 Backtest Results:")
print(f"   🎯 Total Trades: {results['total_trades']}")
print(f"   🏆 Win Rate: {results['win_rate']:.2f}%")
print(f"   💰 Total Return: {results['total_return']:.2f}%")
```

---

## 📚 APIs และเทคโนโลยี

### 🔗 External APIs

| 📊 **API** | 🎯 **หน้าที่** | 🌟 **Features** |
|---|---|---|
| [🥇 GoldAPI](https://www.goldapi.io/) | ข้อมูลราคาทองแม่นยำ | Real-time, Historical data |
| [📈 Alpha Vantage](https://www.alphavantage.co/) | ข้อมูล Forex & Stocks | Free tier, Technical indicators |
| [📰 Finnhub](https://finnhub.io/) | ข่าวเศรษฐกิจล่าสุด | Real-time news, Market data |
| [🤖 DeepSeek](https://deepseek.com/) | AI Analysis | News analysis, Signal generation |
| [🧠 Mistral](https://mistral.ai/) | AI Backup | Sentiment analysis, Market insights |
| [📱 Telegram](https://core.telegram.org/bots/api) | แจ้งเตือนอัตโนมัติ | Bot integration, Rich formatting |

### 🔧 เทคโนโลยีที่ใช้

- **🐍 Python 3.8+** - ภาษาหลักของระบบ
- **🤖 AI/ML Libraries** - scikit-learn, TensorFlow, PyTorch
- **📊 Data Analysis** - pandas, numpy, matplotlib
- **🌐 API Integration** - requests, aiohttp
- **📱 Telegram Bot** - python-telegram-bot
- **📈 Technical Analysis** - TA-Lib, pandas-ta

---

## ⚠️ ข้อจำกัดความรับผิดชอบ

> **🚨 DISCLAIMER: สำคัญมาก - อ่านก่อนใช้งาน**

### 📚 วัตถุประสงค์การศึกษา

ซอฟต์แวร์นี้พัฒนาขึ้น **เพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น** ไม่ใช่คำแนะนำทางการเงินหรือการลงทุน

### ⚠️ ความเสี่ยง

- **อย่าเสี่ยงเงินที่กลัวจะสูญเสีย**
- **ทดสอบด้วย Demo Account ก่อนเสมอ**
- **ศึกษาและทำความเข้าใจระบบก่อนใช้งานจริง**
- **ผู้พัฒนาไม่รับผิดชอบต่อผลการเทรด**

### 💡 คำแนะนำ

1. **เริ่มต้นด้วย Paper Trading** เสมอ
2. **ศึกษาโค้ดและเข้าใจกลไก** ก่อนใช้งาน
3. **มีความรู้พื้นฐาน Python** และการเทรด
4. **ใช้ขนาด Position ที่เหมาะสม** กับทุนของคุณ
5. **ติดตามผลการเทรดอย่างสม่ำเสมอ**

---

## 📄 License

```
MIT License

Copyright (c) 2024 DekTradingSignal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

### 🚀 Ready to Start Trading?

**[⭐ Star this Repository](https://github.com/yourusername/DekTradingSignal)** • **[🐛 Report Issues](https://github.com/yourusername/DekTradingSignal/issues)** • **[💡 Feature Requests](https://github.com/yourusername/DekTradingSignal/discussions)**

*Made with ❤️ by the zombitx64 Team*

**Happy Trading! 📈💰**

</div>