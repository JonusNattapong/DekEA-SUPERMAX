import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from bs4 import BeautifulSoup
import time

# Load environment variables from .env
load_dotenv()

class EconomicCalendar:
    def __init__(self):
        """
        Initialize EconomicCalendar for web scraping Investing.com
        """
        self.base_url = "https://www.investing.com/economic-calendar/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Telegram bot configuration
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    def get_economic_events(self, start_date=None, end_date=None):
        """
        Scrape economic events from Investing.com
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
                    
                    formatted_event = {
                        'date': start_date,
                        'time': event_time,
                        'country': country,
                        'event': event_name,
                        'impact': impact,
                        'actual': actual,
                        'forecast': forecast,
                        'previous': previous,
                        'change': 'N/A'
                    }
                    events.append(formatted_event)
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            return events
            
        except Exception as e:
            print(f"Error scraping economic events: {e}")
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

        columns = ['date', 'time', 'country', 'event', 'actual', 'forecast', 'previous', 'change', 'impact']
        df = pd.DataFrame(events)
        df = df[columns]
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
        Format events data for Telegram message
        """
        if not events:
            return f"{title}\n\n⚠️ ไม่มีอีเวนต์เศรษฐกิจในช่วงนี้"
        
        message = f"<b>{title}</b>\n\n"
        
        for event in events[:20]:  # Limit to 20 events to avoid message length limits
            impact_emoji = "🔴" if event['impact'] == 'High' else "🟡" if event['impact'] == 'Medium' else "🟢"
            
            message += f"{impact_emoji} <b>{event['time']}</b> | {event['country']}\n"
            message += f"📈 {event['event']}\n"
            
            if event['actual'] != 'N/A':
                message += f"💡 Actual: {event['actual']}"
            if event['forecast'] != 'N/A':
                message += f" | Forecast: {event['forecast']}"
            if event['previous'] != 'N/A':
                message += f" | Previous: {event['previous']}"
            
            message += "\n\n"
        
        if len(events) > 20:
            message += f"... และอีก {len(events) - 20} เหตุการณ์"
            
        return message

    def send_daily_summary_to_telegram(self, date=None):
        """
        Send daily economic calendar summary to Telegram
        """
        print(f"🔍 Debug: Telegram Token exists: {'✅' if self.telegram_token else '❌'}")
        print(f"🔍 Debug: Chat ID exists: {'✅' if self.telegram_chat_id else '❌'}")
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get all events
        all_events = self.get_economic_events(date)
        high_impact_events = self.get_high_impact_events(date)
        
        success = True
        
        # Send high impact events first
        if high_impact_events:
            print(f"📤 Sending {len(high_impact_events)} high impact events...")
            high_impact_msg = self.format_telegram_message(
                high_impact_events, 
                f"🚨 High Impact Events - {date}"
            )
            if not self.send_to_telegram(high_impact_msg):
                success = False
            time.sleep(1)  # Avoid rate limiting
        
        # Send summary of all events
        print(f"📤 Sending summary of {len(all_events)} total events...")
        summary_msg = f"📊 <b>Economic Calendar Summary - {date}</b>\n\n"
        summary_msg += f"📈 Total Events: {len(all_events)}\n"
        summary_msg += f"🔴 High Impact: {len(high_impact_events)}\n"
        summary_msg += f"🟡 Medium Impact: {len([e for e in all_events if e['impact'] == 'Medium'])}\n"
        summary_msg += f"🟢 Low Impact: {len([e for e in all_events if e['impact'] == 'Low'])}\n\n"
        
        # Add top 5 events, prioritized by impact then time
        if all_events:
            summary_msg += "<b>Top Events (Prioritized):</b>\n"
            # Define impact order for sorting
            impact_order = {'High': 0, 'Medium': 1, 'Low': 2, 'N/A': 3}
            
            # Sort events: by impact (High first), then by time
            sorted_top_events = sorted(
                all_events, 
                key=lambda x: (impact_order.get(x['impact'], 3), x['time'])
            )
            
            for i, event in enumerate(sorted_top_events[:5], 1):
                impact_emoji = "🔴" if event['impact'] == 'High' else "🟡" if event['impact'] == 'Medium' else "🟢"
                summary_msg += f"{i}. {impact_emoji} {event['time']} | {event['country']} - {event['event']}\n"
        
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
