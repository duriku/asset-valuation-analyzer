# output/report.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import html, dcc, dash_table, Input, Output, callback
import json

def get_color_for_percentage(value):
    """Return color based on percentage value"""
    if value is None or pd.isna(value):
        return '#6c757d'  # Bootstrap gray
    elif value >= 5:
        return '#198754'  # Bootstrap success green
    elif value >= 0:
        return '#20c997'  # Bootstrap teal
    elif value >= -5:
        return '#fd7e14'  # Bootstrap orange
    else:
        return '#dc3545'  # Bootstrap danger red

def get_color_for_rsi(rsi):
    """Return color based on RSI value"""
    if rsi is None or pd.isna(rsi):
        return '#6c757d'
    elif rsi >= 70:
        return '#dc3545'  # Overbought - red
    elif rsi >= 50:
        return '#fd7e14'  # Neutral high - orange
    elif rsi >= 30:
        return '#20c997'  # Neutral low - teal
    else:
        return '#198754'  # Oversold - green

def create_modern_html_table(df, title, output_file=None):
    """Create a modern, responsive HTML table using Bootstrap and custom CSS"""

    # Prepare data with colors
    table_data = []
    for _, row in df.iterrows():
        row_data = {}
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                row_data[col] = {'value': 'N/A', 'color': '#6c757d'}
            elif col in ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200']:
                row_data[col] = {
                    'value': f"{value:.2f}%" if pd.notna(value) else 'N/A',
                    'color': get_color_for_percentage(value)
                }
            elif col == 'RSI':
                row_data[col] = {
                    'value': f"{value:.2f}" if pd.notna(value) else 'N/A',
                    'color': get_color_for_rsi(value)
                }
            elif 'Alert' in col:
                row_data[col] = {
                    'value': '⚠️ YES' if value else 'No',
                    'color': '#dc3545' if value else '#6c757d'
                }
            else:
                row_data[col] = {
                    'value': f"{value:.2f}" if isinstance(value, (int, float)) and pd.notna(value) else str(value),
                    'color': '#212529'
                }
        table_data.append(row_data)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .main-container {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                margin: 20px;
                padding: 30px;
            }}
            .title {{
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 700;
                margin-bottom: 30px;
                text-align: center;
                font-size: 2.5rem;
            }}
            .modern-table {{
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                background: white;
            }}
            .modern-table thead {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .modern-table th {{
                border: none;
                padding: 20px 15px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 0.9rem;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            .modern-table td {{
                border: none;
                padding: 15px;
                vertical-align: middle;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            }}
            .modern-table tbody tr {{
                transition: all 0.3s ease;
            }}
            .modern-table tbody tr:hover {{
                background: rgba(102, 126, 234, 0.05);
                transform: scale(1.01);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }}
            .table-wrapper {{
                max-height: 70vh;
                overflow-x: auto;
                overflow-y: auto;
                border-radius: 15px;
            }}
            .metric-badge {{
                padding: 5px 10px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.85rem;
                display: inline-block;
                min-width: 60px;
                text-align: center;
            }}
            .alert-badge {{
                padding: 3px 8px;
                border-radius: 15px;
                font-size: 0.75rem;
                font-weight: 600;
            }}
            @media (max-width: 768px) {{
                .main-container {{
                    margin: 10px;
                    padding: 15px;
                }}
                .title {{
                    font-size: 1.8rem;
                }}
                .modern-table th,
                .modern-table td {{
                    padding: 10px 8px;
                    font-size: 0.85rem;
                }}
                .table-wrapper {{
                    max-height: 60vh;
                }}
            }}
            .summary-stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
                text-align: center;
                border: 1px solid rgba(102, 126, 234, 0.1);
            }}
            .stat-number {{
                font-size: 2rem;
                font-weight: 700;
                color: #667eea;
            }}
            .stat-label {{
                color: #6c757d;
                font-size: 0.9rem;
                margin-top: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <h1 class="title">
                <i class="fas fa-chart-line me-3"></i>{title}
            </h1>
            
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number">{len(df)}</div>
                    <div class="stat-label">Total Assets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{pd.Timestamp.now().strftime('%H:%M')}</div>
                    <div class="stat-label">Last Updated</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len([col for col in df.columns if 'Alert' in col])}</div>
                    <div class="stat-label">Alert Types</div>
                </div>
            </div>
            
            <div class="table-wrapper">
                <table class="table modern-table mb-0">
                    <thead>
                        <tr>
    """

    # Add headers
    for col in df.columns:
        icon = ""
        if "%" in col or col in ['24h', '7d', '1m', '3m', '1y']:
            icon = '<i class="fas fa-percentage me-1"></i>'
        elif "Alert" in col:
            icon = '<i class="fas fa-bell me-1"></i>'
        elif col == "RSI":
            icon = '<i class="fas fa-chart-area me-1"></i>'
        elif col == "Ticker":
            icon = '<i class="fas fa-tag me-1"></i>'
        elif "Z-score" in col:
            icon = '<i class="fas fa-chart-bar me-1"></i>'

        html_content += f'<th>{icon}{col}</th>'

    html_content += """
                        </tr>
                    </thead>
                    <tbody>
    """

    # Add rows
    for row_data in table_data:
        html_content += '<tr>'
        for col in df.columns:
            cell_data = row_data[col]
            value = cell_data['value']
            color = cell_data['color']

            if 'Alert' in col:
                badge_class = 'alert-badge text-white' if 'YES' in str(value) else 'alert-badge'
                bg_color = 'background-color: #dc3545;' if 'YES' in str(value) else 'background-color: #e9ecef; color: #6c757d;'
                html_content += f'<td><span class="{badge_class}" style="{bg_color}">{value}</span></td>'
            elif col in ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200', 'RSI']:
                html_content += f'<td><span class="metric-badge text-white" style="background-color: {color};">{value}</span></td>'
            else:
                html_content += f'<td style="color: {color}; font-weight: 500;">{value}</td>'
        html_content += '</tr>'

    html_content += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="mt-4 text-center">
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    Report generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
                </small>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Modern responsive HTML report generated: {output_file}")

    return html_content

def create_simple_dash_app(df, title="Financial Data Dashboard"):
    """Create a simple Dash app with DataTable for interactive financial data"""

    # Prepare columns for Dash DataTable
    columns = []
    for col in df.columns:
        col_config = {
            "name": col,
            "id": col,
            "type": "numeric" if col not in ['Ticker', 'Asset Class', 'Currency'] and 'Alert' not in col else "text",
        }

        # Add formatting for percentage columns
        if col in ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200']:
            col_config["format"] = {"specifier": ".2f"}
        elif col == 'RSI':
            col_config["format"] = {"specifier": ".2f"}
        elif col == 'Z-score':
            col_config["format"] = {"specifier": ".3f"}
        elif col == 'Price_USD':
            col_config["format"] = {"specifier": ".2f"}

        columns.append(col_config)

    # Prepare data for DataTable
    data = df.fillna('N/A').to_dict('records')

    # Create Dash app
    app = dash.Dash(__name__)

    # Define styles for conditional formatting
    style_data_conditional = []

    # Style percentage columns
    percentage_cols = ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200']
    for col in percentage_cols:
        if col in df.columns:
            # Positive values (green)
            style_data_conditional.extend([
                {
                    'if': {
                        'filter_query': f'{{{col}}} >= 5',
                        'column_id': col
                    },
                    'backgroundColor': '#d4edda',
                    'color': '#155724',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': f'{{{col}}} >= 0 && {{{col}}} < 5',
                        'column_id': col
                    },
                    'backgroundColor': '#d1ecf1',
                    'color': '#0c5460',
                    'fontWeight': 'bold'
                },
                # Negative values (red)
                {
                    'if': {
                        'filter_query': f'{{{col}}} < 0 && {{{col}}} >= -5',
                        'column_id': col
                    },
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': f'{{{col}}} < -5',
                        'column_id': col
                    },
                    'backgroundColor': '#f5c6cb',
                    'color': '#721c24',
                    'fontWeight': 'bold'
                }
            ])

    # Style RSI column
    if 'RSI' in df.columns:
        style_data_conditional.extend([
            {
                'if': {
                    'filter_query': '{RSI} >= 70',
                    'column_id': 'RSI'
                },
                'backgroundColor': '#f5c6cb',
                'color': '#721c24',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{RSI} <= 30',
                    'column_id': 'RSI'
                },
                'backgroundColor': '#d4edda',
                'color': '#155724',
                'fontWeight': 'bold'
            }
        ])

    # Style alert columns
    alert_cols = [col for col in df.columns if 'Alert' in col]
    for col in alert_cols:
        style_data_conditional.append({
            'if': {
                'filter_query': f'{{{col}}} = True',
                'column_id': col
            },
            'backgroundColor': '#fff3cd',
            'color': '#856404',
            'fontWeight': 'bold'
        })

    app.layout = html.Div([
        # Header
        html.Div([
            html.H1(
                [html.I(className="fas fa-chart-line", style={'marginRight': '15px'}), title],
                style={
                    'textAlign': 'center',
                    'color': '#2c3e50',
                    'marginBottom': '30px',
                    'fontWeight': '700',
                    'background': 'linear-gradient(45deg, #667eea, #764ba2)',
                    'WebkitBackgroundClip': 'text',
                    'WebkitTextFillColor': 'transparent',
                    'backgroundClip': 'text'
                }
            ),

            # Summary cards
            html.Div([
                html.Div([
                    html.H3(str(len(df)), style={'color': '#3498db', 'margin': '0'}),
                    html.P("Total Assets", style={'color': '#7f8c8d', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                          'borderRadius': '10px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.1)', 'margin': '10px'}),

                html.Div([
                    html.H3(pd.Timestamp.now().strftime('%H:%M'), style={'color': '#27ae60', 'margin': '0'}),
                    html.P("Last Updated", style={'color': '#7f8c8d', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                          'borderRadius': '10px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.1)', 'margin': '10px'}),

                html.Div([
                    html.H3(str(len(alert_cols)), style={'color': '#f39c12', 'margin': '0'}),
                    html.P("Alert Types", style={'color': '#7f8c8d', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                          'borderRadius': '10px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.1)', 'margin': '10px'}),

                html.Div([
                    html.H3("Live", style={'color': '#e74c3c', 'margin': '0'}),
                    html.P("Market Data", style={'color': '#7f8c8d', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                          'borderRadius': '10px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.1)', 'margin': '10px'})
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                      'gap': '10px', 'marginBottom': '30px'}),

            # Interactive DataTable
            dash_table.DataTable(
                id='financial-table',
                columns=columns,
                data=data,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current=0,
                page_size=20,
                style_table={
                    'overflowX': 'auto',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 15px rgba(0,0,0,0.1)'
                },
                style_header={
                    'backgroundColor': '#3498db',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'border': '1px solid #2980b9'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '12px',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '14px',
                    'border': '1px solid #ecf0f1'
                },
                style_data={
                    'backgroundColor': '#ffffff',
                    'color': '#2c3e50'
                },
                style_data_conditional=style_data_conditional,
                export_format="csv",
                export_headers="display"
            )
        ], style={'padding': '20px', 'maxWidth': '1400px', 'margin': '0 auto'})
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif'
    })

    return app

def print_asset_table_modern(asset_df, output_file="modern_asset_report.html"):
    """Generate modern responsive HTML report for asset table"""
    return create_modern_html_table(
        asset_df,
        "📊 Financial Assets Analysis",
        output_file
    )

def print_alerts_modern(asset_df, output_file="modern_alerts_report.html"):
    """Generate modern responsive HTML report for alerts"""

    # Create separate tables for different alert types
    alerts_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trading Alerts Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); min-height: 100vh; }}
            .alert-container {{ background: rgba(255,255,255,0.95); margin: 20px; padding: 30px; border-radius: 20px; }}
            .alert-section {{ margin-bottom: 40px; }}
            .alert-title {{ color: #e74c3c; font-weight: 700; margin-bottom: 20px; }}
            .no-alerts {{ text-align: center; color: #6c757d; font-style: italic; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="alert-container">
            <h1 class="text-center mb-5" style="color: #e74c3c; font-weight: 700;">
                <i class="fas fa-exclamation-triangle me-3"></i>Trading Alerts Dashboard
            </h1>
    """

    # Process each alert type
    alert_types = [
        ('Strong Sell Alert', '🔴 STRONG SELL ALERTS', '#dc3545'),
        ('Strong Buy Alert', '🟢 STRONG BUY ALERTS', '#198754'),
        ('Less Strong Sell Alert', '🟠 MODERATE SELL ALERTS', '#fd7e14'),
        ('Less Strong Buy Alert', '🟡 MODERATE BUY ALERTS', '#ffc107')
    ]

    for alert_col, title, color in alert_types:
        alerts_html += f'<div class="alert-section">'
        alerts_html += f'<h2 style="color: {color};">{title}</h2>'

        if alert_col in asset_df.columns:
            filtered_df = asset_df[asset_df[alert_col] == True]
            if not filtered_df.empty:
                table_html = create_modern_html_table(filtered_df, title)
                # Extract just the table part
                table_start = table_html.find('<div class="table-wrapper">')
                table_end = table_html.find('</div>', table_start) + 6
                alerts_html += table_html[table_start:table_end]
            else:
                alerts_html += '<div class="no-alerts">No alerts found</div>'
        else:
            alerts_html += '<div class="no-alerts">Alert data not available</div>'

        alerts_html += '</div>'

    alerts_html += """
        </div>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(alerts_html)

    print(f"Modern alerts report generated: {output_file}")
    return alerts_html

def create_interactive_dashboard(asset_df, trades=None, port=8050):
    """Create and run an interactive Dash dashboard"""
    app = create_simple_dash_app(asset_df, "Financial Portfolio Dashboard")

    print(f"Starting interactive dashboard at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    try:
        app.run(debug=True, port=port)
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        print("You can still view the HTML reports that were generated.")

# Keep original functions for backward compatibility
def print_asset_table(asset_df):
    print("\n=== All Assets (excluding currencies) ===")
    print(asset_df.to_string(index=False))

def print_alerts(asset_df):
    print("\n=== STRONG SELL ALERTS (Overheated) ===")
    if 'Strong Sell Alert' in asset_df.columns and asset_df['Strong Sell Alert'].any():
        print(asset_df[asset_df['Strong Sell Alert']].to_string(index=False))
    else:
        print("None found.")

    print("\n=== STRONG BUY ALERTS (Washed Out) ===")
    if 'Strong Buy Alert' in asset_df.columns and asset_df['Strong Buy Alert'].any():
        print(asset_df[asset_df['Strong Buy Alert']].to_string(index=False))
    else:
        print("None found.")

def print_rebalance(trades):
    print("\n=== Suggested Rebalance Trades (excluding currencies) ===")
    for sell, z_sell, buy, z_buy, delta_z in trades:
        print(f"SELL {sell} (Z={z_sell:.2f}) → BUY {buy} (Z={z_buy:.2f}) | ΔZ = {delta_z:.2f}")