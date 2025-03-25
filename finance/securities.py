import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_historical_data(ticker: str, start_date: str, end_date: str, frequency: str, quote_type: str,
                         debug: bool = False) -> List[Dict[str, Any]]:
    
    """
    Fetch historical data from Yahoo Finance for a given ticker using Yahoo Finance's internal API.

    parameters:
        ticker (str): The stock ticker symbol.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        frequency (str): The frequency of the data  ('1d', '5d', '1wk', '1mo', '3mo').
        quote_type (str): The type of quote ('open', 'close', 'high', 'low', 'adjclose').
        debug (bool): Flag to enable debug logging.

    returns:
        List[Dict[str, Any]]: A list of dictionaries containing the historical data.
    """

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled.")

    # Convert dates to Unix timestamps
    try:
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
    except ValueError as e:
        logger.error(f"Date conversion error: {e}")
        return []

    # Construct the URL
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?"
        f"period1={start_timestamp}&period2={end_timestamp}&interval={frequency}&events=history"
    )

    # Define headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://finance.yahoo.com/",
        "Connection": "keep-alive"
    }

    # Make the request
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return []

    # Parse the JSON response
    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        return []

    if debug:
        logger.debug(f"JSON response: {data}")

    # Extract the relevant quote data
    try:
        quotes = data['chart']['result'][0]['indicators']['quote'][0]
        timestamps = data['chart']['result'][0]['timestamp']
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        return []

    # Map quote type to the correct key in the response
    quote_key = {
        'open': 'open',
        'close': 'close',
        'high': 'high',
        'low': 'low'
    }.get(quote_type, 'close')

    # Prepare the result
    result = []
    for timestamp, quote in zip(timestamps, quotes[quote_key]):
        result.append({
            'timestamp': datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'quote': quote
        })

    logger.info(f"Fetched {len(result)} records for {ticker}.")
    return result

def get_corporate_events(ticker: str, start_date: str, end_date: str, event_type: str = None, debug: bool = False) -> List[Dict[str, Any]]:

    """
    Fetch corporate events from Yahoo Finance for a given ticker and event type using Yahoo Finance's internal API.

    parameters:
        ticker (str): The stock ticker symbol.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        event_type (str): The type of event to fetch ('dividends', 'splits'). If None, fetch all events.
        debug (bool): Flag to enable debug logging.

    returns:
        List[Dict[str, Any]]: A list of flattened dictionaries containing the corporate events of the specified type.
    """
    
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled.")

    try:
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
    except ValueError as e:
        logger.error(f"Date conversion error: {e}")
        return []

    # Construct the URL
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?"
        f"period1={start_timestamp}&period2={end_timestamp}&interval=1d&events=div|split|earn"
    )

    # Define headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://finance.yahoo.com/",
        "Connection": "keep-alive"
    }

    # Make the request
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return []

    # Parse the JSON response
    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        return []

    if debug:
        logger.debug(f"JSON response: {data}")

    # Extract the relevant events data
    events = []
    chart = data.get("chart", {})
    result = chart.get("result", [{}])[0]
    events_data = result.get("events", {})

    if event_type:
        event_keys = [event_type]
    else:
        event_keys = ["dividends", "splits"]

    for key in event_keys:
        event_items = events_data.get(key, {})
        for timestamp, details in event_items.items():
            event_info = {"timestamp": int(timestamp), "type": key}
            event_info.update(details)
            event_info["date"] = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime('%Y-%m-%d')
            events.append(event_info)

    return events
