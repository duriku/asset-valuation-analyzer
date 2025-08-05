"""
Dash application builder for the asset valuation reports.

Encapsulates Dash DataTable creation with styling, filters, and sorting.
"""

from typing import Optional
import pandas as pd

try:
    import dash  # type: ignore
    from dash import html, dash_table  # type: ignore
except ImportError:
    dash = None
    html = None
    dash_table = None


def build_dash_app(df: pd.DataFrame, title: str = "Portfolio Analysis") -> "dash.Dash":
    """Return a Dash app displaying the portfolio table."""
    if dash is None:
        raise ImportError("Dash is not installed. Please install dash to use this feature.")

    app = dash.Dash(__name__)
    app.title = title

    table = dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in df.columns],
        data=df.to_dict("records"),
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "5px"},
    )

    app.layout = html.Div([
        html.H1(title),
        table
    ])
    return app
