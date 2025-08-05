"""
Utility package for generating asset valuation reports.

This package separates business logic, presentation templates, and Dash
application construction into independent modules. The goal is to make the
codebase easier to maintain and extend – for example, porting the UI
to a React front‑end – without having to wade through a monolithic file.

By exposing clear, documented functions in this __init__.py, importing
code elsewhere can remain simple (e.g., `from output import print_asset_table_modern`).
"""

from .data_utils import (
    enrich_asset_data,
    build_conditional_styles,
    add_names_to_dataframe,  # legacy alias for backward compatibility
)
from .html_templates import (
    generate_asset_table_html,
    generate_alerts_html,
)
from .dash_app import build_dash_app

__all__ = [
    "enrich_asset_data",
    "build_conditional_styles",
    "add_names_to_dataframe",
    "generate_asset_table_html",
    "generate_alerts_html",
    "build_dash_app",
]
