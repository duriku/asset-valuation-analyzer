"""
HTML template helpers for the asset valuation reports.

Functions here return fully-formed HTML strings for asset tables and
alerts, with all CSS and JS embedded. This way, UI presentation is
completely isolated from business logic.
"""

import pandas as pd
from typing import List

STYLE = """
<style>
* { box-sizing: border-box; }
body { margin: 0; padding: 0; background: #f5f5f5; font-family: Roboto, sans-serif; }
.ib-container { background: white; margin: 0 auto; padding: 1em; }
.ib-header { background: #0d47a1; color: white; padding: 1em; }
table { border-collapse: collapse; width: 100%; }
th, td { padding: 0.5em; border-bottom: 1px solid #ddd; }
tr:hover { background-color: #f1f1f1; }
.alert-buy { background-color: #C8E6C9; }
.alert-sell { background-color: #FFCDD2; }
</style>
"""

SCRIPT = """
<script>
function highlightAlerts() {
  document.querySelectorAll("td").forEach(td => {
    if (td.innerText === "True") {
      if (td.previousElementSibling && td.previousElementSibling.innerText.includes("Buy")) {
        td.parentElement.classList.add("alert-buy");
      }
      if (td.previousElementSibling && td.previousElementSibling.innerText.includes("Sell")) {
        td.parentElement.classList.add("alert-sell");
      }
    }
  });
}
window.onload = highlightAlerts;
</script>
"""


def generate_asset_table_html(df: pd.DataFrame, title: str = "Portfolio Analysis") -> str:
    """Generate a complete HTML page containing the asset table."""
    html_table = df.to_html(classes="data-table", index=False)
    return (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>{STYLE}</head>"
        f"<body><div class='ib-container'><div class='ib-header'><h1>{title}</h1></div>{html_table}</div>{SCRIPT}</body></html>"
    )


def generate_alerts_html(alerts: List[str], title: str = "Alerts") -> str:
    """Generate a complete HTML page showing alerts."""
    alerts_html = "".join(f"<li>{a}</li>" for a in alerts)
    return (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>{STYLE}</head>"
        f"<body><div class='ib-container'><div class='ib-header'><h1>{title}</h1></div><ul>{alerts_html}</ul></div>{SCRIPT}</body></html>"
    )
