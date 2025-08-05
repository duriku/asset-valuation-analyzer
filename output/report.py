"""
Facade module for generating asset valuation reports.

This module re‑exports the core functionality from the underlying
packages :mod:`output.data_utils`, :mod:`output.html_templates` and
:mod:`output.dash_app`.  It exists primarily for backwards
compatibility: existing code that imported functions from the original
monolithic ``report.py`` can continue to do so without modification.

At the same time, it provides a much cleaner structure for new
development – HTML rendering, data processing and UI framework
integration live in separate modules, and the public API here
intentionally mirrors the functions most scripts will need.
"""

import pandas as pd
from typing import List

from .data_utils import (
    enrich_asset_data,
    build_conditional_styles,
    add_names_to_dataframe,  # legacy alias included here as well
)
from .html_templates import (
    generate_asset_table_html,
    generate_alerts_html,
)
from .dash_app import build_dash_app


# --- Public API for HTML output ---

def print_asset_table_modern(df: pd.DataFrame, title: str = "Portfolio Analysis") -> str:
    """Return a complete HTML page representing the asset table."""
    enriched = enrich_asset_data(df)
    return generate_asset_table_html(enriched, title=title)


def print_alerts_modern(alerts: List[str], title: str = "Alerts") -> str:
    """Return a complete HTML page representing a list of alerts."""
    return generate_alerts_html(alerts, title=title)


# --- Public API for Dash app ---

def create_ib_style_dash_app(df: pd.DataFrame, title: str = "Portfolio Analysis"):
    """
    Legacy compatibility wrapper for the old create_ib_style_dash_app.

    Ensures that names are present (via enrich_asset_data) and returns a simple
    Dash app built with build_dash_app. Conditional styling from the old report
    can be added later by wiring build_conditional_styles into the Dash table.
    """
    enriched = enrich_asset_data(df)
    # compute but ignore styles for now; could be passed into dash_table.DataTable later
    _ = build_conditional_styles(enriched)
    return build_dash_app(enriched, title=title)


# --- Compatibility shims for older code ---

def create_ib_style_html_table(df: pd.DataFrame, title: str = "Portfolio Analysis") -> str:
    """Alias for print_asset_table_modern to support legacy imports."""
    return print_asset_table_modern(df, title=title)
