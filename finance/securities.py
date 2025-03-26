import logging
import re
import requests
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_corporate_events(scriptcode: str, start_date: str, end_date: str, event_type: str = None, debug: bool = False) -> List[Dict[str, Any]]:

    """
    Fetch corporate events from BSE India for a given script code and event type using BSE India's internal API.

    parameters:
        scriptcode (str): The security script code.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
        event_type (str): The type of event to fetch ('bonus', 'dividend', 'split', default: None: meaning fetch all events).
        debug (bool): Flag to enable debug logging (default: False).

    returns:
        List[Dict[str, Any]]: A list of dictionaries containing the corporate events.
    """
    
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled.")

    logger.info(f"Fetching corporate events for scriptcode: {scriptcode}")
    # Convert dates to required format (YYYYMMDD)
    try:
        formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
        formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
        logger.debug(f"Formatted dates start: {formatted_start_date}, end: {formatted_end_date}")
    except ValueError as e:
        logger.error(f"Date conversion error: {e}")
        return []

    # Construct the URL
    url = (
        f"https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w?"
        f"Fdate={formatted_start_date}&TDate={formatted_end_date}&Purposecode="
        f"&ddlcategorys=E&ddlindustrys=&scripcode={scriptcode}&segment=0&strSearch=S"
    )

    logger.info(f"Constructed URL: {url}")

    # Define headers to mimic a browser request
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.bseindia.com',
        'Referer': 'https://www.bseindia.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
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

    # Extract and filter relevant data
    events = []
    logger.info("Processing received events")
    for item in data:
        purpose = item.get("Purpose", "").lower()
        ex_date = item.get("Ex_date", "").strip()
        amount, ratio = None, None

        # Determine event type and extract relevant values
        if "dividend" in purpose:
            event_type_detected = "dividend"
            match = re.search(r"rs\. - ([\d.]+)", purpose)
            amount = float(match.group(1)) if match else None

        elif "bonus issue" in purpose:
            event_type_detected = "bonus"
            match = re.search(r"(\d+):(\d+)", purpose)
            if match:
                x, y = map(int, match.groups())
                ratio = (x + y) / y  # Bonus issue ratio calculation

        elif "split" in purpose:
            event_type_detected = "split"
            match = re.search(r"rs\.(\d+)/- to rs\.(\d+)/-", purpose)
            if match:
                old_value, new_value = map(float, match.groups())
                ratio = old_value / new_value if new_value != 0 else None

        else:
            event_type_detected = "other"

        # Apply event type filter
        if event_type and event_type_detected != event_type:
            continue

        # Build event dictionary
        event_data = {
            "type": event_type_detected,
            "ex_date": ex_date,
            "details": purpose,
        }
        
        logger.debug(f"Processed event: {event_data}")
        if event_type_detected == "dividend":
            event_data["amount"] = amount
        elif event_type_detected in ["split", "bonus"]:
            event_data["ratio"] = ratio

        events.append(event_data)

    logger.info(f"Total events fetched: {len(events)}")
    return events

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
        debug (bool): Flag to enable debug logging (default: False).

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
        logger.debug(f"Timestamps start: {start_timestamp}, end: {end_timestamp}")
    except ValueError as e:
        logger.error(f"Date conversion error: {e}")
        return []

    # Construct the URL
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?"
        f"period1={start_timestamp}&period2={end_timestamp}&interval={frequency}&events=history"
    )

    logger.info(f"Constructed URL: {url}")

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

def get_script_codes(tickers: List[str], segment: str = "Equity T+1", status: str = None, debug: bool = False) -> Dict[str, Optional[str]]:

    """
    Fetch the BSE script codes given a list of ticker symbols, with optional filtering by segment and status.

    Parameters:
        tickers (List[str]): The list of ticker symbols.
        segment (str): The segment to filter by ('Equity T+1', 'Equity T+0', 'Derivatives', 'Exchange Traded Funds',
                                                'Debt or Others', 'Currency Derivatives', 'Commodity', 'Electronic Gold Receipts',
                                                'Hybrid Security', 'Municipal Bonds', 'Preference Shares', 'Debentures and Bonds',
                                                'Equity - Institutional Series', 'Commercial Papers', 'Social Stock Exchange', default: 'Equity').
        status (str): The status to filter by ('Active', 'Suspended', 'Delisted', default: None, meaning no filter).
        debug (bool): Flag to enable debug logging (default: False).

    Returns:
        Dict[str, Optional[str]]: A dictionary with tickers as keys and script codes as values.
    """

    VALID_SEGMENTS = {
        "Equity T+1": "Equity",
        "Equity T+0": "EQT0",
        "Derivatives": "DER",
        "Exchange Traded Funds": "MF",
        "Debt or Others": "DB",
        "Currency Derivatives": "CR",
        "Commodity": "CO",
        "Electronic Gold Receipts": "EGR",
        "Hybrid Security": "HS",
        "Municipal Bonds": "MB",
        "Preference Shares": "Preference Shares",
        "Debentures and Bonds": "Debentures and Bonds",
        "Equity - Institutional Series": "Equity - Institutional Series",
        "Commercial Papers": "Commercial Papers",
        "Social Stock Exchange": "SSE"}

    VALID_STATUSES = {"Active": "Active", "Suspended": "Suspended", "Delisted": "Delisted", None: None}

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled.")

    # Validate segment
    if segment not in VALID_SEGMENTS:
        logger.warning(f"Invalid segment '{segment}', using 'Equity T+1' as default segment filter.")
        segment = VALID_SEGMENTS.get(segment, "Equity")

    # Validate status
    if status not in VALID_STATUSES:
        logger.warning(f"Invalid status '{status}', ignoring status filter.")
        status = VALID_STATUSES.get(status, None)

    # API endpoint
    url = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w"

    # Headers
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.bseindia.com',
        'Referer': 'https://www.bseindia.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    # Query params
    params = {
        'Group': '',
        'Scripcode': '',
        'industry': '',
        'segment': segment,
        'status': status if status else '',  # Don't send status if None
    }

    logger.info(f"Parameters: {params}")

    # Fetch data
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        securities = response.json()
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {ticker: None for ticker in tickers}
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        return {ticker: None for ticker in tickers}

    logger.info(f"Fetched {len(securities)} securities.")

    # Search for the tickers
    script_codes = {}
    for ticker in tickers:
        found = False
        for security in securities:
            if security.get("scrip_id", "").upper() == ticker.upper():
                script_codes[ticker] = security.get("SCRIP_CD")
                found = True
                break
        if not found:
            logger.warning(f"Ticker '{ticker}' not found.")
            script_codes[ticker] = None

    logger.debug(f"Script codes: {script_codes}")
    return script_codes
