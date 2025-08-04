# data/loader.py
import yfinance as yf
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from config import ASSETS_FILE, CURRENCIES_FILE
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Database configuration
DB_PATH = "data/market_data.db"
MAX_HOURLY_DAYS = 30  # Yahoo Finance limit for hourly data

def ensure_db_exists():
    """Create database and tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        # Daily data table
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS daily_data (
                                                               ticker TEXT,
                                                               date DATE,
                                                               open REAL,
                                                               high REAL,
                                                               low REAL,
                                                               close REAL,
                                                               volume INTEGER,
                                                               PRIMARY KEY (ticker, date)
                         )
                     """)

        # Hourly data table
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS hourly_data (
                                                                ticker TEXT,
                                                                datetime DATETIME,
                                                                open REAL,
                                                                high REAL,
                                                                low REAL,
                                                                close REAL,
                                                                volume INTEGER,
                                                                PRIMARY KEY (ticker, datetime)
                         )
                     """)

        # Metadata table to track last update times
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS update_metadata (
                                                                    ticker TEXT PRIMARY KEY,
                                                                    last_daily_update DATE,
                                                                    last_hourly_update DATETIME
                     )
                     """)

        # NEW: Asset names cache table
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS asset_names (
                                                                ticker TEXT PRIMARY KEY,
                                                                long_name TEXT,
                                                                short_name TEXT,
                                                                last_updated DATE
                     )
                     """)

def get_asset_name_from_cache(ticker):
    """Get asset name from local cache."""
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute(
            "SELECT long_name, short_name FROM asset_names WHERE ticker = ?",
            (ticker,)
        ).fetchone()

    if result:
        long_name, short_name = result
        return long_name or short_name or ticker
    return None

def fetch_single_asset_name(ticker):
    """Fetch name for a single asset with error handling."""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        long_name = info.get('longName', '')
        short_name = info.get('shortName', '')

        # Clean up names - remove extra whitespace and handle None values
        long_name = long_name.strip() if long_name else ''
        short_name = short_name.strip() if short_name else ''

        return {
            'ticker': ticker,
            'long_name': long_name,
            'short_name': short_name,
            'success': True
        }
    except Exception as e:
        print(f"Warning: Could not fetch name for {ticker}: {e}")
        return {
            'ticker': ticker,
            'long_name': '',
            'short_name': '',
            'success': False
        }

def batch_update_asset_names(tickers, max_workers=5, delay_between_requests=0.1):
    """
    Efficiently fetch and cache asset names for multiple tickers.

    Args:
        tickers: List of ticker symbols
        max_workers: Number of concurrent threads (keep low to avoid rate limiting)
        delay_between_requests: Delay between requests to avoid rate limiting
    """
    ensure_db_exists()

    # Filter out tickers that are already cached and recent (less than 30 days old)
    tickers_to_fetch = []
    cached_count = 0

    with sqlite3.connect(DB_PATH) as conn:
        for ticker in tickers:
            result = conn.execute(
                """SELECT last_updated FROM asset_names
                   WHERE ticker = ? AND last_updated > date('now', '-30 days')""",
                (ticker,)
            ).fetchone()

            if not result:
                tickers_to_fetch.append(ticker)
            else:
                cached_count += 1

    if cached_count > 0:
        print(f"Using cached names for {cached_count} tickers")

    if not tickers_to_fetch:
        print("All ticker names are already cached")
        return

    print(f"Fetching names for {len(tickers_to_fetch)} tickers...")

    # Fetch names with controlled concurrency
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        future_to_ticker = {
            executor.submit(fetch_single_asset_name, ticker): ticker
            for ticker in tickers_to_fetch
        }

        # Process results as they complete
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                result = future.result()
                results.append(result)

                # Small delay to be respectful to the API
                time.sleep(delay_between_requests)

            except Exception as e:
                print(f"Error fetching name for {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'long_name': '',
                    'short_name': '',
                    'success': False
                })

    # Save results to database
    today = datetime.now().date()
    with sqlite3.connect(DB_PATH) as conn:
        for result in results:
            conn.execute("""
                INSERT OR REPLACE INTO asset_names 
                (ticker, long_name, short_name, last_updated)
                VALUES (?, ?, ?, ?)
            """, (result['ticker'], result['long_name'], result['short_name'], today))

    successful_fetches = sum(1 for r in results if r['success'])
    print(f"Successfully fetched and cached {successful_fetches}/{len(results)} asset names")

def get_asset_names_for_dataframe(df):
    """
    Add asset names to a dataframe efficiently using cached data.

    Args:
        df: DataFrame with either 'Ticker' column or ticker symbols as index

    Returns:
        DataFrame with 'Name' column added
    """
    if 'Name' in df.columns:
        return df  # Already has names

    df_copy = df.copy()

    # Get ticker symbols from dataframe
    if 'Ticker' in df.columns:
        tickers = df['Ticker'].tolist()
        ticker_column_exists = True
    else:
        tickers = df.index.tolist()
        ticker_column_exists = False

    # Ensure we have cached names for all tickers
    batch_update_asset_names(tickers)

    # Get names from cache
    names = []
    for ticker in tickers:
        cached_name = get_asset_name_from_cache(ticker)
        names.append(cached_name or ticker)  # Fallback to ticker if no name found

    # Add names to dataframe
    if ticker_column_exists:
        # Insert Name column right after Ticker column
        ticker_index = df.columns.get_loc('Ticker')
        cols = df.columns.tolist()
        cols.insert(ticker_index + 1, 'Name')
        df_copy = df_copy.reindex(columns=cols)
        df_copy['Name'] = names
    else:
        # Insert Name as first column when ticker is index
        df_copy.insert(0, 'Name', names)

    return df_copy

def preload_asset_names(assets_file=None, currencies_file=None):
    """
    Preload and cache names for all assets and currencies.
    Call this once to populate the cache for better performance.

    Args:
        assets_file: Path to assets file (uses default from config if None)
        currencies_file: Path to currencies file (uses default from config if None)
    """
    assets_file = assets_file or ASSETS_FILE
    currencies_file = currencies_file or CURRENCIES_FILE

    all_tickers = []

    # Load assets
    if os.path.exists(assets_file):
        with open(assets_file) as f:
            assets = [line.strip() for line in f if line.strip()]
            all_tickers.extend(assets)
            print(f"Loaded {len(assets)} assets from {assets_file}")

    # Load currencies
    if os.path.exists(currencies_file):
        with open(currencies_file) as f:
            currencies = [line.strip() for line in f if line.strip()]
            all_tickers.extend(currencies)
            print(f"Loaded {len(currencies)} currencies from {currencies_file}")

    if all_tickers:
        print(f"Preloading names for {len(all_tickers)} tickers...")
        batch_update_asset_names(all_tickers)
        print("Name preloading complete!")
    else:
        print("No tickers found to preload")

def cleanup_old_name_cache(days_to_keep=30):
    """Clean up old cached names."""
    with sqlite3.connect(DB_PATH) as conn:
        cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
        deleted_count = conn.execute(
            "DELETE FROM asset_names WHERE last_updated < ?",
            (cutoff_date,)
        ).rowcount
        print(f"Cleaned up {deleted_count} old cached asset names")

# Keep all existing functions from the original loader.py...
# [All the previous functions remain the same]

def get_last_update_date(ticker, data_type='daily'):
    """Get the last update date for a ticker."""
    with sqlite3.connect(DB_PATH) as conn:
        if data_type == 'daily':
            result = conn.execute(
                "SELECT last_daily_update FROM update_metadata WHERE ticker = ?",
                (ticker,)
            ).fetchone()
        else:  # hourly
            result = conn.execute(
                "SELECT last_hourly_update FROM update_metadata WHERE ticker = ?",
                (ticker,)
            ).fetchone()

    if result and result[0]:
        return pd.to_datetime(result[0])
    return None

def save_daily_data(ticker, df):
    """Save daily data to SQLite database."""
    if df.empty:
        return

    # Handle MultiIndex columns from yfinance
    df_copy = df.copy()

    # Check if we have MultiIndex columns
    if isinstance(df_copy.columns, pd.MultiIndex):
        # Flatten MultiIndex columns - take the first level (metric name)
        df_copy.columns = [col[0] if isinstance(col, tuple) else col for col in df_copy.columns]

    # Reset index to get Date as a column
    if isinstance(df_copy.index, pd.DatetimeIndex):
        df_copy.reset_index(inplace=True)
        date_col = 'Date'
    else:
        df_copy.reset_index(inplace=True)
        date_col = df_copy.columns[0]  # First column should be date

    # Ensure we have the required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df_copy.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols} for {ticker}")
        print(f"Available columns: {list(df_copy.columns)}")
        return

    # Add ticker and convert date
    df_copy['ticker'] = ticker
    df_copy['date'] = pd.to_datetime(df_copy[date_col]).dt.date

    # Select and rename columns to match DB schema
    columns_map = {
        'Open': 'open', 'High': 'high', 'Low': 'low',
        'Close': 'close', 'Volume': 'volume'
    }
    df_copy = df_copy.rename(columns=columns_map)

    # Ensure we have the columns we need
    final_cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
    df_copy = df_copy[final_cols]

    # Remove any rows with NaN values in critical columns
    df_copy = df_copy.dropna(subset=['open', 'high', 'low', 'close'])

    if df_copy.empty:
        print(f"Warning: No valid data to save for {ticker}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        # Use INSERT OR REPLACE for upsert behavior
        for _, row in df_copy.iterrows():
            # Convert all values to Python native types, handling NaN properly
            values = (
                str(row['ticker']),
                row['date'],
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                int(row['volume']) if pd.notna(row['volume']) and row['volume'] != 0 else 0
            )

            conn.execute("""
                INSERT OR REPLACE INTO daily_data 
                (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, values)

        # Update metadata
        last_date = df_copy['date'].max()
        conn.execute("""
            INSERT OR REPLACE INTO update_metadata (ticker, last_daily_update)
            VALUES (?, ?)
        """, (ticker, last_date))

        print(f"Saved {len(df_copy)} records for {ticker}")

def save_hourly_data(ticker, df):
    """Save hourly data to SQLite database."""
    if df.empty:
        return

    # Handle MultiIndex columns from yfinance
    df_copy = df.copy()

    # Check if we have MultiIndex columns
    if isinstance(df_copy.columns, pd.MultiIndex):
        # Flatten MultiIndex columns - take the first level (metric name)
        df_copy.columns = [col[0] if isinstance(col, tuple) else col for col in df_copy.columns]

    # Reset index to get Datetime as a column
    if isinstance(df_copy.index, pd.DatetimeIndex):
        df_copy.reset_index(inplace=True)
        datetime_col = 'Datetime' if 'Datetime' in df_copy.columns else df_copy.columns[0]
    else:
        df_copy.reset_index(inplace=True)
        datetime_col = df_copy.columns[0]  # First column should be datetime

    # Ensure we have the required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df_copy.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols} for {ticker}")
        print(f"Available columns: {list(df_copy.columns)}")
        return

    # Add ticker and convert datetime
    df_copy['ticker'] = ticker
    df_copy['datetime'] = pd.to_datetime(df_copy[datetime_col])

    # Select and rename columns to match DB schema
    columns_map = {
        'Open': 'open', 'High': 'high', 'Low': 'low',
        'Close': 'close', 'Volume': 'volume'
    }
    df_copy = df_copy.rename(columns=columns_map)

    # Ensure we have the columns we need
    final_cols = ['ticker', 'datetime', 'open', 'high', 'low', 'close', 'volume']
    df_copy = df_copy[final_cols]

    # Remove any rows with NaN values in critical columns
    df_copy = df_copy.dropna(subset=['open', 'high', 'low', 'close'])

    if df_copy.empty:
        print(f"Warning: No valid data to save for {ticker}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        # Use INSERT OR REPLACE for upsert behavior
        for _, row in df_copy.iterrows():
            # Convert all values to Python native types, handling NaN properly
            values = (
                str(row['ticker']),
                row['datetime'].isoformat(),
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                int(row['volume']) if pd.notna(row['volume']) and row['volume'] != 0 else 0
            )

            conn.execute("""
                INSERT OR REPLACE INTO hourly_data 
                (ticker, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, values)

        # Update metadata
        last_datetime = df_copy['datetime'].max()
        conn.execute("""
            INSERT OR REPLACE INTO update_metadata (ticker, last_hourly_update)
            VALUES (?, ?)
        """, (ticker, last_datetime.isoformat()))

        print(f"Saved {len(df_copy)} hourly records for {ticker}")

def load_daily_data_from_db(ticker, start_date=None, end_date=None):
    """Load daily data from SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT date, open, high, low, close, volume FROM daily_data WHERE ticker = ?"
        params = [ticker]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"

        df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            print(f"No cached data found for {ticker}")
            return pd.DataFrame()

        # Convert to the format expected by your existing code
        df['Date'] = pd.to_datetime(df['date'])
        df.set_index('Date', inplace=True)
        df = df.drop('date', axis=1)

        # Capitalize column names to match yfinance format
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        print(f"Loaded {len(df)} cached records for {ticker}")
        return df

def load_hourly_data_from_db(ticker, start_datetime=None, end_datetime=None):
    """Load hourly data from SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT datetime, open, high, low, close, volume FROM hourly_data WHERE ticker = ?"
        params = [ticker]

        if start_datetime:
            query += " AND datetime >= ?"
            params.append(start_datetime)
        if end_datetime:
            query += " AND datetime <= ?"
            params.append(end_datetime)

        query += " ORDER BY datetime"

        df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:
            df['Datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('Datetime', inplace=True)
            df = df.drop('datetime', axis=1)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        return df

def download_incremental_daily_data(ticker, period='15mo'):
    """Download only new daily data since last update."""
    ensure_db_exists()

    last_update = get_last_update_date(ticker, 'daily')

    if last_update is None:
        # First time download - get full period
        print(f"First time downloading {ticker} daily data ({period})")
        try:
            data = yf.download(ticker, period=period, interval='1d', auto_adjust=True)
            if data.empty:
                print(f"Warning: No data received for {ticker} - possibly delisted or invalid ticker")
                return pd.DataFrame()

            # Debug: print data structure
            print(f"DEBUG {ticker}: columns={list(data.columns)}, index_type={type(data.index)}")

            # Save to database
            save_daily_data(ticker, data)

            # Return properly formatted data (load from DB to ensure consistent format)
            formatted_data = load_daily_data_from_db(ticker)
            if not formatted_data.empty:
                return formatted_data
            else:
                # Fallback: format the data manually if DB load fails
                return format_yfinance_data(data)

        except Exception as e:
            print(f"Error downloading {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    # Calculate days since last update
    days_since_update = (datetime.now() - last_update).days

    if days_since_update <= 1:
        print(f"{ticker} daily data is up to date")
        return load_daily_data_from_db(ticker)

    # Download only recent data
    start_date = (last_update - timedelta(days=1)).strftime('%Y-%m-%d')  # Overlap by 1 day
    print(f"Updating {ticker} daily data since {start_date}")

    try:
        new_data = yf.download(ticker, start=start_date, interval='1d', auto_adjust=True)
        if not new_data.empty:
            save_daily_data(ticker, new_data)

        # Return full dataset from DB
        return load_daily_data_from_db(ticker)
    except Exception as e:
        print(f"Error updating {ticker}: {e}")
        return load_daily_data_from_db(ticker)

def format_yfinance_data(data):
    """Format yfinance data to consistent structure."""
    if data.empty:
        return pd.DataFrame()

    df = data.copy()

    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten MultiIndex columns - take the first level (metric name)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    # Ensure we have the expected columns
    expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols} in yfinance data")
        return pd.DataFrame()

    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'Date' in df.columns:
            df.set_index('Date', inplace=True)
        else:
            print("Warning: Could not find date information in data")
            return pd.DataFrame()

    # Select only the columns we need
    df = df[expected_cols]

    return df

def download_incremental_hourly_data(ticker, hours_back=24):
    """Download hourly data for the last N hours."""
    ensure_db_exists()

    # Yahoo Finance hourly data limitations
    if hours_back > 24 * MAX_HOURLY_DAYS:
        print(f"Warning: Yahoo Finance limits hourly data to ~{MAX_HOURLY_DAYS} days")
        hours_back = 24 * MAX_HOURLY_DAYS

    last_update = get_last_update_date(ticker, 'hourly')
    current_time = datetime.now()

    if last_update is None:
        # First time download
        start_time = current_time - timedelta(hours=hours_back)
        print(f"First time downloading {ticker} hourly data (last {hours_back} hours)")
    else:
        # Check if we need to update
        hours_since_update = (current_time - last_update).total_seconds() / 3600

        if hours_since_update < 1:
            print(f"{ticker} hourly data is up to date")
            cutoff_time = current_time - timedelta(hours=hours_back)
            return load_hourly_data_from_db(ticker, start_datetime=cutoff_time)

        # Download from last update
        start_time = last_update - timedelta(hours=1)  # Small overlap
        print(f"Updating {ticker} hourly data since {start_time}")

    try:
        # For hourly data, we need to use period format
        period_map = {
            24: '1d', 48: '2d', 168: '7d', 720: '30d'  # hours to period
        }
        period = period_map.get(hours_back, f'{min(hours_back//24, 30)}d')

        new_data = yf.download(ticker, period=period, interval='1h', auto_adjust=True)

        if not new_data.empty:
            # Format data before saving
            formatted_data = format_yfinance_data(new_data)
            if not formatted_data.empty:
                save_hourly_data(ticker, formatted_data)

        # Return only the requested time window
        cutoff_time = current_time - timedelta(hours=hours_back)
        result = load_hourly_data_from_db(ticker, start_datetime=cutoff_time)

        if result.empty and not new_data.empty:
            # Fallback to formatted fresh data if DB load fails
            return format_yfinance_data(new_data)

        return result

    except Exception as e:
        print(f"Error downloading hourly data for {ticker}: {e}")
        cutoff_time = current_time - timedelta(hours=hours_back)
        return load_hourly_data_from_db(ticker, start_datetime=cutoff_time)

def validate_ticker(ticker):
    """
    Validate if a ticker exists and suggest corrections for common issues.
    Returns (is_valid, suggested_ticker, error_message)
    """
    try:
        # Quick test download
        test_data = yf.download(ticker, period='5d', interval='1d', auto_adjust=True)
        if not test_data.empty:
            return True, ticker, None

        # Common ticker format issues for European stocks
        suggestions = []

        if '.' in ticker:
            # Try without extension
            base_ticker = ticker.split('.')[0]
            suggestions.append(base_ticker)

            # Try common European exchange suffixes
            if ticker.endswith('.BD'):
                suggestions.extend([f"{base_ticker}.BU", f"{base_ticker}.VI"])
            elif ticker.endswith('.BU'):
                suggestions.extend([f"{base_ticker}.BD", f"{base_ticker}.VI"])
        else:
            # Try adding common suffixes
            suggestions.extend([f"{ticker}.BD", f"{ticker}.BU", f"{ticker}.VI"])

        # Test suggestions
        for suggestion in suggestions:
            try:
                test_data = yf.download(suggestion, period='5d', interval='1d', auto_adjust=True)
                if not test_data.empty:
                    return True, suggestion, f"Ticker corrected from {ticker} to {suggestion}"
            except:
                continue

        return False, ticker, f"No valid data found for {ticker} or common variations"

    except Exception as e:
        return False, ticker, f"Error validating {ticker}: {e}"

def read_tickers(file_path):
    """Read ticker symbols from a file."""
    with open(file_path) as f:
        return [line.strip() for line in f if line.strip()]

def load_assets_and_currencies():
    """Load asset and currency lists from config files with validation."""
    assets = read_tickers(ASSETS_FILE)
    currencies = read_tickers(CURRENCIES_FILE)

    # Optional: Validate tickers (uncomment to enable)
    # print("Validating tickers...")
    # validated_assets = []
    # for ticker in assets:
    #     is_valid, corrected_ticker, message = validate_ticker(ticker)
    #     if is_valid:
    #         validated_assets.append(corrected_ticker)
    #         if message:
    #             print(f"  {message}")
    #     else:
    #         print(f"  Warning: {message}")
    # assets = validated_assets

    return assets, currencies

def download_data(tickers, period='15mo', interval='1d', use_cache=True):
    """
    Enhanced download function with caching support.

    Args:
        tickers: List of ticker symbols or single ticker string
        period: Time period for initial download
        interval: '1d' for daily, '1h' for hourly
        use_cache: Whether to use SQLite caching
    """
    if not use_cache:
        # Original behavior - direct download
        return yf.download(
            tickers,
            period=period,
            interval=interval,
            group_by='ticker',
            threads=True,
            auto_adjust=True
        )

    # Handle single ticker vs multiple tickers
    if isinstance(tickers, str):
        single_ticker = True
        ticker_list = [tickers]
    else:
        single_ticker = False
        ticker_list = list(tickers)  # Ensure it's a list

    all_data = {}
    failed_tickers = []

    for ticker in ticker_list:
        try:
            if interval == '1d':
                data = download_incremental_daily_data(ticker, period)
            elif interval == '1h':
                # For hourly, extract hours from period (default to 24h)
                hours = 24
                if period.endswith('d'):
                    hours = int(period[:-1]) * 24
                elif period.endswith('h'):
                    hours = int(period[:-1])
                data = download_incremental_hourly_data(ticker, hours)
            else:
                # Fallback to direct download for other intervals
                print(f"Using direct download for {ticker} with interval {interval}")
                data = yf.download(ticker, period=period, interval=interval, auto_adjust=True)

            if not data.empty:
                all_data[ticker] = data
                print(f"✓ Successfully loaded {ticker}: {data.shape[0]} records")
            else:
                failed_tickers.append(ticker)
                print(f"✗ No data available for {ticker}")

        except Exception as e:
            print(f"✗ Error processing {ticker}: {e}")
            failed_tickers.append(ticker)

    if failed_tickers:
        print(f"Failed to get data for: {failed_tickers}")

    # Return format matching original yfinance behavior
    if single_ticker:
        # Single ticker case - return the DataFrame directly
        if ticker_list[0] in all_data:
            return all_data[ticker_list[0]]
        else:
            return pd.DataFrame()  # Empty DataFrame for failed single ticker
    else:
        # Multiple tickers case - ALWAYS return a dictionary, even if empty
        if len(all_data) == 0:
            print("Warning: No data was successfully downloaded for any ticker")
            return {}  # Empty dict instead of None or empty DataFrame
        else:
            print(f"Successfully downloaded data for {len(all_data)} out of {len(ticker_list)} tickers")
            return all_data