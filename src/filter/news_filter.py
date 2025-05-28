import requests
import logging
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INVESTING_API_URL = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
CACHE_FILE = "news_cache.json"
CACHE_DURATION_HOURS = 6  # Cache duration in hours

# Symbols mapping (map forex pairs to related currencies)
SYMBOL_CURRENCY_MAP = {
    "EURUSD": ["EUR", "USD"],
    "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["USD", "JPY"],
    "AUDUSD": ["AUD", "USD"],
    "USDCAD": ["USD", "CAD"],
    "NZDUSD": ["NZD", "USD"],
    "XAUUSD": ["XAU", "USD", "GOLD"],  # Gold is affected by USD and general economic news
}

def get_economic_calendar(days_ahead: int = 1, importance: int = 3) -> List[Dict[str, Any]]:
    """
    ดึงปฏิทินข่าวเศรษฐกิจจาก Investing.com
    
    Args:
        days_ahead: จำนวนวันล่วงหน้าที่ต้องการดึงข้อมูล
        importance: ระดับความสำคัญขั้นต่ำของข่าว (1-3, โดย 3 = สำคัญมาก)
    
    Returns:
        รายการข่าวเศรษฐกิจที่สำคัญ
    """
    cache_path = os.path.join(os.path.dirname(__file__), '..', CACHE_FILE)
    
    # Check if cache exists and is recent enough
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time < timedelta(hours=CACHE_DURATION_HOURS):
                logger.info("Using cached economic calendar data")
                return cache_data['events']
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.warning("Invalid cache file, fetching fresh data")
    
    today = datetime.now()
    end_date = today + timedelta(days=days_ahead)
    
    # Format dates for Investing.com URL
    start_str = today.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.investing.com/economic-calendar/'
    }
    
    data = {
        'dateFrom': start_str,
        'dateTo': end_str,
        'currentTab': 'custom',
        'limit_from': 0
    }
    
    try:
        response = requests.post(INVESTING_API_URL, headers=headers, data=data, timeout=20)
        response.raise_for_status()
        
        # Parse HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        
        for row in soup.select('tr.js-event-item'):
            try:
                # Extract event importance (number of bulls)
                event_importance = len(row.select('td.sentiment span.grayFullBullishIcon'))
                
                if event_importance < importance:
                    continue  # Skip events with low importance
                
                # Extract event time
                time_cell = row.select_one('td.time')
                if not time_cell:
                    continue
                event_time = time_cell.get_text(strip=True)
                
                # Extract event name
                event_name = row.select_one('td.event a')
                if not event_name:
                    continue
                name = event_name.get_text(strip=True)
                
                # Extract country
                country = row.select_one('td.flagCur span')
                if not country:
                    continue
                country_name = country.get('title', '')
                
                # Extract forecast and previous values if available
                forecast = row.select_one('td.forecast')
                forecast_value = forecast.get_text(strip=True) if forecast else 'N/A'
                
                previous = row.select_one('td.previous')
                previous_value = previous.get_text(strip=True) if previous else 'N/A'
                
                # Create event record
                event_record = {
                    'time': event_time,
                    'date': start_str,  # Assuming all events are for today
                    'name': name,
                    'country': country_name,
                    'importance': event_importance,
                    'forecast': forecast_value,
                    'previous': previous_value,
                    # Map country to currencies for filtering
                    'affected_currencies': get_affected_currencies(country_name)
                }
                
                events.append(event_record)
                
            except Exception as e:
                logger.error(f"Error parsing event row: {e}")
                continue
        
        # Cache the results
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'events': events
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error writing cache file: {e}")
        
        return events
        
    except requests.RequestException as e:
        logger.error(f"Error fetching economic calendar: {e}")
        
        # Try to use cached data if available, even if it's old
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)['events']
            except:
                pass
                
        return []

def get_affected_currencies(country: str) -> List[str]:
    """
    Map a country to its currency code(s)
    
    Args:
        country: ชื่อประเทศ
    
    Returns:
        รหัสสกุลเงินที่เกี่ยวข้อง
    """
    country_currency_map = {
        'United States': ['USD'],
        'Euro Zone': ['EUR'],
        'Germany': ['EUR'],
        'France': ['EUR'],
        'Italy': ['EUR'],
        'Spain': ['EUR'],
        'United Kingdom': ['GBP'],
        'Japan': ['JPY'],
        'Canada': ['CAD'],
        'Australia': ['AUD'],
        'New Zealand': ['NZD'],
        'Switzerland': ['CHF'],
        'China': ['CNY'],
    }
    
    return country_currency_map.get(country, [])

def should_avoid_trading(symbol: str, time_buffer_minutes: int = 30) -> Dict[str, Any]:
    """
    ตรวจสอบว่าควรหลีกเลี่ยงการเทรดในช่วงนี้เนื่องจากมีข่าวสำคัญหรือไม่
    
    Args:
        symbol: คู่เงิน หรือ instrument ที่จะเทรด (เช่น 'EURUSD')
        time_buffer_minutes: ระยะเวลาก่อนและหลังข่าว (เป็นนาที) ที่ควรหลีกเลี่ยงการเทรด
    
    Returns:
        ข้อมูลสถานะและข่าวที่กระทบ
    """
    symbol = symbol.upper()
    events = get_economic_calendar(importance=3)  # Get only high importance events
    current_time = datetime.now()
    
    # Get currencies related to this symbol
    related_currencies = SYMBOL_CURRENCY_MAP.get(symbol, [])
    if not related_currencies and '_' in symbol:
        # Try to parse symbol like 'EUR_USD'
        parts = symbol.split('_')
        related_currencies = parts
    elif not related_currencies and len(symbol) == 6:
        # Try to parse symbol like 'EURUSD'
        related_currencies = [symbol[:3], symbol[3:]]
    
    avoid = False
    upcoming_events = []
    
    for event in events:
        # Check if any related currency is affected
        event_affects_symbol = False
        for currency in related_currencies:
            if currency in event['affected_currencies']:
                event_affects_symbol = True
                break
        
        if not event_affects_symbol:
            continue
            
        # Parse event time
        try:
            event_time_str = f"{event['date']} {event['time']}"
            event_time = datetime.strptime(event_time_str, '%Y-%m-%d %H:%M')
            
            # Add timezone info if necessary
            # event_time = event_time.replace(tzinfo=timezone.utc)
            
            buffer_before = event_time - timedelta(minutes=time_buffer_minutes)
            buffer_after = event_time + timedelta(minutes=time_buffer_minutes)
            
            # Check if current time is within buffer period
            if buffer_before <= current_time <= buffer_after:
                avoid = True
                upcoming_events.append(event)
            elif current_time < event_time:
                # Future event, add to upcoming list
                upcoming_events.append(event)
        except ValueError:
            logger.error(f"Invalid date/time format: {event['date']} {event['time']}")
    
    # Sort upcoming events by time
    upcoming_events.sort(key=lambda x: x['time'])
    
    return {
        'should_avoid': avoid,
        'symbol': symbol,
        'current_time': current_time.isoformat(),
        'buffer_minutes': time_buffer_minutes,
        'upcoming_events': upcoming_events[:5],  # Limit to next 5 events
        'trading_status': 'AVOID' if avoid else 'OK'
    }

def format_news_report(news_status: Dict[str, Any]) -> str:
    """
    สร้างรายงานสถานะข่าวในรูปแบบข้อความ
    
    Args:
        news_status: ข้อมูลสถานะข่าวจาก should_avoid_trading
    
    Returns:
        ข้อความรายงานสรุปสถานะข่าวและผลกระทบต่อการเทรด
    """
    status = "⚠️ ควรหลีกเลี่ยงการเทรด ⚠️" if news_status['should_avoid'] else "✅ เทรดได้ตามปกติ"
    
    report = f"""
📰 News Filter Report: {news_status['symbol']}
🚦 สถานะ: {status}
🕒 เวลาปัจจุบัน: {news_status['current_time']}
⏱️ Buffer: {news_status['buffer_minutes']} นาที

📆 ข่าวที่จะเกิดขึ้นเร็วๆ นี้:
"""
    
    if not news_status['upcoming_events']:
        report += "   ไม่มีข่าวสำคัญในช่วงนี้\n"
    else:
        for idx, event in enumerate(news_status['upcoming_events'], 1):
            report += f"   {idx}. [{event['time']}] {event['country']}: {event['name']} (ความสำคัญ: {'🔴' * event['importance']})\n"
    
    return report

# Example usage
if __name__ == "__main__":
    # Test the functions
    symbol = "XAUUSD"
    news_status = should_avoid_trading(symbol)
    print(format_news_report(news_status))
