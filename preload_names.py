#!/usr/bin/env python3
"""
Asset Names Preload Utility

This script preloads and caches asset names for all tickers in your configuration files.
Run this periodically (e.g., weekly) to keep the name cache fresh and improve performance.

Usage:
    python preload_names.py                    # Preload all tickers from config files
    python preload_names.py --assets-only      # Preload only assets (skip currencies)
    python preload_names.py --currencies-only  # Preload only currencies (skip assets)
    python preload_names.py --cleanup          # Clean up old cached names (30+ days)
    python preload_names.py --status           # Show cache status
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import (
    preload_asset_names,
    cleanup_old_name_cache,
    get_asset_name_from_cache,
    batch_update_asset_names,
    ensure_db_exists
)
from config import ASSETS_FILE, CURRENCIES_FILE
import sqlite3

DB_PATH = "data/market_data.db"

def get_cache_status():
    """Get status of the asset names cache."""
    ensure_db_exists()

    with sqlite3.connect(DB_PATH) as conn:
        # Total cached names
        total_count = conn.execute("SELECT COUNT(*) FROM asset_names").fetchone()[0]

        # Recent names (last 30 days)
        recent_count = conn.execute(
            "SELECT COUNT(*) FROM asset_names WHERE last_updated > date('now', '-30 days')"
        ).fetchone()[0]

        # Old names (older than 30 days)
        old_count = total_count - recent_count

        # Get some sample entries
        samples = conn.execute(
            """SELECT ticker, long_name, short_name, last_updated
               FROM asset_names
               ORDER BY last_updated DESC
                   LIMIT 5"""
        ).fetchall()

    return {
        'total_count': total_count,
        'recent_count': recent_count,
        'old_count': old_count,
        'samples': samples
    }

def read_tickers_from_file(file_path):
    """Read ticker symbols from a file."""
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found")
        return []

    with open(file_path) as f:
        tickers = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(tickers)} tickers from {file_path}")
    return tickers

def main():
    parser = argparse.ArgumentParser(description='Preload and manage asset name cache')
    parser.add_argument('--assets-only', action='store_true',
                        help='Preload only assets (skip currencies)')
    parser.add_argument('--currencies-only', action='store_true',
                        help='Preload only currencies (skip assets)')
    parser.add_argument('--cleanup', action='store_true',
                        help='Clean up old cached names (30+ days)')
    parser.add_argument('--status', action='store_true',
                        help='Show cache status')
    parser.add_argument('--max-workers', type=int, default=3,
                        help='Maximum concurrent workers for fetching names (default: 3)')
    parser.add_argument('--delay', type=float, default=0.2,
                        help='Delay between requests in seconds (default: 0.2)')

    args = parser.parse_args()

    if args.status:
        print("=== Asset Names Cache Status ===")
        status = get_cache_status()
        print(f"Total cached names: {status['total_count']}")
        print(f"Recent names (< 30 days): {status['recent_count']}")
        print(f"Old names (> 30 days): {status['old_count']}")

        if status['samples']:
            print("\nRecent cache entries:")
            for ticker, long_name, short_name, last_updated in status['samples']:
                name = long_name or short_name or 'N/A'
                print(f"  {ticker}: {name} (updated: {last_updated})")

        return

    if args.cleanup:
        print("=== Cleaning up old cached names ===")
        cleanup_old_name_cache(days_to_keep=30)
        return

    # Determine which tickers to preload
    all_tickers = []

    if not args.currencies_only:
        # Load assets
        assets = read_tickers_from_file(ASSETS_FILE)
        all_tickers.extend(assets)

    if not args.assets_only:
        # Load currencies
        currencies = read_tickers_from_file(CURRENCIES_FILE)
        all_tickers.extend(currencies)

    if not all_tickers:
        print("No tickers found to preload")
        return

    print(f"\n=== Preloading names for {len(all_tickers)} tickers ===")
    print(f"Max workers: {args.max_workers}")
    print(f"Delay between requests: {args.delay}s")
    print("This may take a few minutes depending on the number of tickers...\n")

    start_time = datetime.now()

    # Preload names with custom settings
    batch_update_asset_names(
        all_tickers,
        max_workers=args.max_workers,
        delay_between_requests=args.delay
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n=== Preloading completed in {duration:.1f} seconds ===")

    # Show final status
    status = get_cache_status()
    print(f"Total cached names: {status['total_count']}")
    print(f"Recent names: {status['recent_count']}")

if __name__ == "__main__":
    main()