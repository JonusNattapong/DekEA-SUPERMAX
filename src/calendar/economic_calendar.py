import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from typing import Optional, Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

class EconomicCalendar:
    def __init__(self):
        """
        Initialize EconomicCalendar for web scraping Investing.com
        with DeepSeek sentiment analysis and local fallbacks.
        """
        self.base_url = "https://www.investing.com/economic-calendar/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Telegram bot configuration
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # DeepSeek API configuration
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        
        # Initialize DeepSeek client
        self.deepseek_client = None
        self._init_deepseek_client()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Initialize fallback sentiment analyzer
        self.fallback_sentiment = self._init_fallback_sentiment()

    def _init_deepseek_client(self):
        """Initialize DeepSeek API client."""
        try:
            if self.deepseek_api_key:
                from openai import OpenAI
                self.deepseek_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                logger.info("✅ DeepSeek client initialized")
        except ImportError:
            logger.warning("⚠️ OpenAI SDK not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"❌ Failed to initialize DeepSeek client: {e}")

    def _init_fallback_sentiment(self):
        """Initialize fallback sentiment analysis using TextBlob or VADER."""
        try:
            from textblob import TextBlob
            logger.info("✅ TextBlob initialized for fallback sentiment analysis")
            return "textblob"
        except ImportError:
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                logger.info("✅ VADER initialized for fallback sentiment analysis")
                return "vader"
            except ImportError:
                logger.warning("⚠️ No fallback sentiment analysis available. Install textblob or vaderSentiment.")
                return None

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Implement exponential backoff retry logic."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"❌ Final attempt failed: {e}")
                    raise e
                
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def _get_sentiment_deepseek(self, text: str) -> Dict[str, Any]:
        """Get sentiment using DeepSeek API with OpenAI SDK."""
        if not self.deepseek_client:
            raise ValueError("DeepSeek client not initialized")
        
        try:
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial sentiment analyzer. Analyze the sentiment of economic news and return only a JSON object with 'sentiment' (positive/negative/neutral) and 'score' (float between -1 and 1)."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze sentiment: {text}"
                    }
                ],
                max_tokens=100,
                temperature=0.1,
                stream=False
            )
            
            content = response.choices[0].message.content
            sentiment_data = json.loads(content)
            return sentiment_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse DeepSeek response: {e}")
            return {"sentiment": "neutral", "score": 0.0}
        except Exception as e:
            logger.error(f"❌ DeepSeek API error: {e}")
            raise e

    def _get_sentiment_fallback(self, text: str) -> Dict[str, Any]:
        """Get sentiment using fallback methods."""
        if self.fallback_sentiment == "textblob":
            from textblob import TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
                
            return {"sentiment": sentiment, "score": round(polarity, 2)}
            
        elif self.fallback_sentiment == "vader":
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            analyzer = SentimentIntensityAnalyzer()
            scores = analyzer.polarity_scores(text)
            compound = scores['compound']
            
            if compound > 0.05:
                sentiment = "positive"
            elif compound < -0.05:
                sentiment = "negative"
            else:
                sentiment = "neutral"
                
            return {"sentiment": sentiment, "score": round(compound, 2)}
        
        return {"sentiment": "neutral", "score": 0.0}

    def get_event_sentiment(self, event_text: str) -> Dict[str, Any]:
        """
        Get sentiment for economic event using DeepSeek API with local fallbacks.
        """
        if not event_text or event_text.strip() == "":
            return {"sentiment": "neutral", "score": 0.0}
        
        # Try DeepSeek API first
        if self.deepseek_client:
            try:
                result = self._retry_with_backoff(self._get_sentiment_deepseek, event_text)
                logger.debug(f"✅ DeepSeek sentiment for '{event_text}': {result}")
                return result
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek API failed: {e}. Using local fallback...")
        
        # Use fallback sentiment analysis
        try:
            result = self._get_sentiment_fallback(event_text)
            logger.debug(f"✅ Fallback sentiment for '{event_text}': {result}")
            return result
        except Exception as e:
            logger.error(f"❌ All sentiment analysis methods failed: {e}")
            return {"sentiment": "neutral", "score": 0.0}

    def get_economic_events(self, start_date=None, end_date=None):
        """
        Scrape economic events from Investing.com and analyze sentiment.
        """
        try:
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            
            target_date = datetime.strptime(start_date, '%Y-%m-%d')
            url = f"{self.base_url}?day={target_date.strftime('%b%d.%Y')}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            # Try different possible selectors for event rows
            table_rows = soup.find_all('tr', class_='js-event-item') or soup.find_all('tr', {'data-event-id': True})
            
            for row in table_rows:
                try:
                    # Extract time
                    time_cell = row.find('td', class_='time') or row.find('time')
                    event_time = time_cell.text.strip() if time_cell else 'N/A'
                    
                    # Extract country
                    country_cell = row.find('td', class_='flagCur') or row.find('span', class_='ceFlags')
                    if country_cell:
                        country_span = country_cell.find('span', {'title': True})
                        country = country_span['title'] if country_span else country_cell.text.strip()
                    else:
                        country = 'N/A'
                    
                    # Extract impact (look for bull icons or impact indicators)
                    impact_cell = row.find('td', class_='sentiment') or row.find('td', class_='impact')
                    if impact_cell:
                        # Count bull icons or look for impact class
                        bulls = impact_cell.find_all('i', class_=['grayFullBullishIcon', 'bull-icon']) 
                        impact_divs = impact_cell.find_all('div', class_=['high', 'medium', 'low'])
                        
                        if impact_divs:
                            impact = impact_divs[0]['class'][0].capitalize()
                        elif len(bulls) >= 3:
                            impact = 'High'
                        elif len(bulls) >= 2:
                            impact = 'Medium'
                        else:
                            impact = 'Low'
                    else:
                        impact = 'Low'
                    
                    # Extract event name
                    event_cell = row.find('td', class_='event') or row.find('a', class_='eventTitle')
                    if event_cell:
                        event_link = event_cell.find('a')
                        event_name = event_link.text.strip() if event_link else event_cell.text.strip()
                    else:
                        event_name = 'N/A'
                    
                    # Extract actual, forecast, previous values
                    actual_cell = row.find('td', class_='act') or row.find('td', class_='actual')
                    actual = actual_cell.text.strip() if actual_cell else 'N/A'
                    
                    forecast_cell = row.find('td', class_='fore') or row.find('td', class_='forecast')
                    forecast = forecast_cell.text.strip() if forecast_cell else 'N/A'
                    
                    previous_cell = row.find('td', class_='prev') or row.find('td', class_='previous')
                    previous = previous_cell.text.strip() if previous_cell else 'N/A'
                    
                    # Sentiment analysis with error handling
                    sentiment_result = self.get_event_sentiment(event_name)
                    
                    formatted_event = {
                        'date': start_date,
                        'time': event_time,
                        'country': country,
                        'event': event_name,
                        'impact': impact,
                        'actual': actual,
                        'forecast': forecast,
                        'previous': previous,
                        'change': 'N/A',
                        'sentiment': sentiment_result.get('sentiment', 'neutral'),
                        'sentiment_score': sentiment_result.get('score', 0.0)
                    }
                    events.append(formatted_event)
                    
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Error scraping economic events: {e}")
            return []

    def get_high_impact_events(self, start_date=None, end_date=None):
        """Fetch only high impact economic events."""
        events = self.get_economic_events(start_date, end_date)
        return [event for event in events if str(event.get('impact', '')).lower() == 'high']

    def get_events_by_country(self, country_code, start_date=None, end_date=None):
        """Fetch economic events for a specific country."""
        events = self.get_economic_events(start_date, end_date)
        # Map common country codes to full names
        country_map = {
            'USD': 'United States',
            'US': 'United States',
            'EUR': 'Euro Zone',
            'GBP': 'United Kingdom',
            'JPY': 'Japan',
            'CAD': 'Canada',
            'AUD': 'Australia',
            'NZD': 'New Zealand'
        }
        
        search_country = country_map.get(country_code.upper(), country_code)
        return [event for event in events if search_country.upper() in event['country'].upper()]

    def format_events_as_dataframe(self, events):
        """Convert list of economic events to pandas DataFrame."""
        if not events:
            return pd.DataFrame()

        columns = ['date', 'time', 'country', 'event', 'actual', 'forecast', 'previous', 'change', 'impact', 'sentiment', 'sentiment_score']
        df = pd.DataFrame(events)
        # Ensure all columns exist, fill with N/A if not
        for col in columns:
            if col not in df.columns:
                df[col] = 'N/A'
        df = df[columns] # Reorder and select
        df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce').fillna(0.0).round(2)
        df = df.sort_values(['date', 'time', 'country'])
        return df

    def send_to_telegram(self, message):
        """
        Send message to Telegram chat
        """
        if not self.telegram_token or not self.telegram_chat_id:
            print("❌ Telegram bot token หรือ chat ID ไม่ได้ตั้งค่าไว้")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=payload)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False

    def format_telegram_message(self, events, title="📊 Economic Calendar"):
        """
        Format events data for Telegram message, including sentiment.
        """
        if not events:
            return f"{title}\n\n⚠️ ไม่มีอีเวนต์เศรษฐกิจในช่วงนี้"
        
        message = f"<b>{title}</b>\n\n"
        
        for event in events[:20]:  # Limit to 20 events
            impact_emoji = "🔴" if event['impact'] == 'High' else "🟡" if event['impact'] == 'Medium' else "🟢"
            
            message += f"{impact_emoji} <b>{event['time']}</b> | {event['country']}\n"
            message += f"📈 {event['event']}\n"

            # Add sentiment display
            sentiment = event.get('sentiment', 'neutral')
            sentiment_score = event.get('sentiment_score', 0.0)
            
            if sentiment == 'positive':
                sentiment_emoji = "😊"
            elif sentiment == 'negative':
                sentiment_emoji = "😰"
            else:
                sentiment_emoji = "😐"
            
            message += f"{sentiment_emoji} Sentiment: {sentiment.title()} ({sentiment_score})\n"
            
            details = []
            if event['actual'] != 'N/A' and event['actual'] != '':
                details.append(f"Actual: {event['actual']}")
            if event['forecast'] != 'N/A' and event['forecast'] != '':
                details.append(f"Forecast: {event['forecast']}")
            if event['previous'] != 'N/A' and event['previous'] != '':
                details.append(f"Previous: {event['previous']}")
            
            if details:
                message += f"💡 {' | '.join(details)}"
            
            message += "\n\n"
        
        if len(events) > 20:
            message += f"... และอีก {len(events) - 20} เหตุการณ์"
            
        return message

    def send_daily_summary_to_telegram(self, date=None):
        """
        Send daily economic calendar summary to Telegram, including sentiment counts.
        """
        logger.info(f"🔍 Debug: Telegram Token exists: {'✅' if self.telegram_token else '❌'}")
        logger.info(f"🔍 Debug: Chat ID exists: {'✅' if self.telegram_chat_id else '❌'}")
        logger.info(f"🔍 Debug: DeepSeek API: {'✅' if self.deepseek_client else '❌'}")
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get all events
        all_events = self.get_economic_events(date)
        high_impact_events = self.get_high_impact_events(date)
        
        success = True
        
        # Send high impact events first
        if high_impact_events:
            logger.info(f"📤 Sending {len(high_impact_events)} high impact events...")
            high_impact_msg = self.format_telegram_message(
                high_impact_events, 
                f"🚨 High Impact Events - {date}"
            )
            if not self.send_to_telegram(high_impact_msg):
                success = False
            time.sleep(1)  # Avoid rate limiting
        
        # Send summary of all events
        logger.info(f"📤 Sending summary of {len(all_events)} total events...")
        summary_msg = f"📊 <b>Economic Calendar Summary - {date}</b>\n\n"
        summary_msg += f"📈 Total Events: {len(all_events)}\n"
        summary_msg += f"🔴 High Impact: {len(high_impact_events)}\n"
        summary_msg += f"🟡 Medium Impact: {len([e for e in all_events if e['impact'] == 'Medium'])}\n"
        summary_msg += f"🟢 Low Impact: {len([e for e in all_events if e['impact'] == 'Low'])}\n"

        # Add sentiment counts
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for event in all_events:
            sentiment = event.get('sentiment', 'neutral')
            sentiment_counts[sentiment] += 1
        
        summary_msg += f"😊 Positive Sentiment: {sentiment_counts['positive']}\n"
        summary_msg += f"😰 Negative Sentiment: {sentiment_counts['negative']}\n"
        summary_msg += f"😐 Neutral Sentiment: {sentiment_counts['neutral']}\n\n"
        
        # Add API status - only DeepSeek or fallback
        if self.deepseek_client:
            api_status = "DeepSeek API"
        elif self.fallback_sentiment:
            api_status = f"Local ({self.fallback_sentiment.title()})"
        else:
            api_status = "None"
        
        summary_msg += f"🤖 Sentiment Analysis: {api_status}\n\n"
        
        # Add top 5 events, prioritized by impact then time
        if all_events:
            summary_msg += "<b>Top Events (Prioritized):</b>\n"
            impact_order = {'High': 0, 'Medium': 1, 'Low': 2, 'N/A': 3}
            sorted_top_events = sorted(
                all_events, 
                key=lambda x: (impact_order.get(x['impact'], 3), x['time'])
            )
            
            for i, event in enumerate(sorted_top_events[:5], 1):
                impact_emoji = "🔴" if event['impact'] == 'High' else "🟡" if event['impact'] == 'Medium' else "🟢"
                sentiment = event.get('sentiment', 'neutral')
                sentiment_emoji = "😊" if sentiment == 'positive' else "😰" if sentiment == 'negative' else "😐"
                summary_msg += f"{i}. {impact_emoji} {sentiment_emoji} {event['time']} | {event['country']} - {event['event']}\n"
        
        if not self.send_to_telegram(summary_msg):
            success = False
            
        return success

if __name__ == '__main__':
    calendar = EconomicCalendar()

    # Get today's events
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("🔄 กำลัง scrape ข้อมูลจาก Investing.com...")
    events = calendar.get_economic_events(today)
    df = calendar.format_events_as_dataframe(events)

    if not df.empty:
        print("📊 เหตุการณ์เศรษฐกิจทั้งหมด:")
        print(df.to_string(index=False))
        
        # Send to Telegram
        print("\n📤 กำลังส่งข้อมูลไปยัง Telegram...")
        calendar.send_daily_summary_to_telegram(today)
        print("✅ ส่งข้อมูลไปยัง Telegram เรียบร้อยแล้ว")
    else:
        print("⚠️ ไม่มีอีเวนต์เศรษฐกิจในวันนี้")
