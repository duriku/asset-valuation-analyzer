"""
Low‑level data manipulation utilities for the asset valuation reports.

These functions encapsulate the logic for enriching a pandas DataFrame
with additional information (such as friendly asset names), applying
filters, calculating conditional formatting colours and building a
structure describing how each cell should appear in an HTML table.
"""

import pandas as pd
from typing import Any, Dict, List

# Optional yfinance import for ticker name lookup
try:
    import yfinance as yf  # type: ignore
except ImportError:  # pragma: no cover
    yf = None


def get_asset_name(symbol: str) -> str:
    """Return a human-readable asset name for the given ticker."""
    if yf is None:
        return symbol
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info.get("shortName") or symbol
    except Exception:
        return symbol


def enrich_asset_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add calculated columns or derived fields to the asset DataFrame."""
    df = df.copy()
    if "Ticker" in df.columns and "Name" not in df.columns:
        df["Name"] = [get_asset_name(t) for t in df["Ticker"]]
    return df


def build_conditional_styles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Build conditional formatting rules for the Dash DataTable or HTML table.
    Example: highlight 'Strong Buy Alert' cells in green, 'Strong Sell Alert' in red.
    """
    styles = []
    if "Strong Buy Alert" in df.columns:
        styles.append({
            "if": {"filter_query": "{Strong Buy Alert} = True"},
            "backgroundColor": "#C8E6C9",
            "color": "black",
        })
    if "Strong Sell Alert" in df.columns:
        styles.append({
            "if": {"filter_query": "{Strong Sell Alert} = True"},
            "backgroundColor": "#FFCDD2",
            "color": "black",
        })
    return styles


def add_names_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Legacy alias for enrich_asset_data, kept for backwards compatibility.

    Old code may still import this name; internally it now just calls
    enrich_asset_data.
    """
    return enrich_asset_data(df)
