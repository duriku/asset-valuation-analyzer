
# output/report.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import html, dcc, dash_table, Input, Output, callback
import json

def get_color_for_percentage(value):
    """Return color based on percentage value - professional trading colors"""
    if value is None or pd.isna(value):
        return '#666666'  # Neutral gray
    elif value >= 5:
        return '#00C851'  # Strong green
    elif value >= 0:
        return '#00C851'  # Green
    elif value >= -5:
        return '#FF4444'  # Red
    else:
        return '#CC0000'  # Strong red

def get_color_for_rsi(rsi):
    """Return color based on RSI value"""
    if rsi is None or pd.isna(rsi):
        return '#666666'
    elif rsi >= 70:
        return '#FF4444'  # Overbought - red
    elif rsi >= 50:
        return '#FFA500'  # Neutral high - orange
    elif rsi >= 30:
        return '#666666'  # Neutral - gray
    else:
        return '#00C851'  # Oversold - green

def filter_dataframe(df, symbol_filter=None, type_filter=None):
    """Filter DataFrame by symbol and type"""
    if df.empty:
        return df

    filtered_df = df.copy()

    # Filter by symbol
    if symbol_filter:
        if 'Ticker' in filtered_df.columns:
            mask = filtered_df['Ticker'].str.contains(symbol_filter, case=False, na=False)
            filtered_df = filtered_df[mask]
        elif filtered_df.index.name == 'Ticker':
            mask = filtered_df.index.str.contains(symbol_filter, case=False, na=False)
            filtered_df = filtered_df[mask]

    # Filter by type
    if type_filter:
        if 'Asset Class' in filtered_df.columns:
            mask = filtered_df['Asset Class'].str.contains(type_filter, case=False, na=False)
            filtered_df = filtered_df[mask]
        elif 'Type' in filtered_df.columns:
            mask = filtered_df['Type'].str.contains(type_filter, case=False, na=False)
            filtered_df = filtered_df[mask]

    return filtered_df


def create_ib_style_html_table(df, title, output_file=None, symbol_filter=None, type_filter=None):
    """Create an Interactive Brokers-style professional trading table with interactive filters"""

    # Store original data for client-side filtering
    original_data = []
    for _, row in df.iterrows():
        row_dict = {}
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                row_dict[col] = ''
            else:
                row_dict[col] = str(value)
        original_data.append(row_dict)

    # Apply server-side filters if provided
    filtered_df = filter_dataframe(df, symbol_filter, type_filter)

    # Add filter info to title if filters are applied
    if symbol_filter or type_filter:
        filter_parts = []
        if symbol_filter:
            filter_parts.append(f"Symbol: {symbol_filter}")
        if type_filter:
            filter_parts.append(f"Type: {type_filter}")
        title += f" (Filtered: {', '.join(filter_parts)})"

    # Prepare data with colors
    table_data = []
    for _, row in filtered_df.iterrows():
        row_data = {}
        for col in filtered_df.columns:
            value = row[col]
            if pd.isna(value):
                row_data[col] = {'value': '--', 'color': '#666666', 'bg': '#f8f9fa'}
            elif col in ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200', '24h_RS', '7d_RS', '1m_RS', '3m_RS', '1y_RS']:
                color = get_color_for_percentage(value)
                bg_color = '#f0f8f0' if value >= 0 else '#fff0f0'
                row_data[col] = {
                    'value': f"{value:+.2f}%" if pd.notna(value) else '--',
                    'color': color,
                    'bg': bg_color
                }
            elif col == 'RSI':
                color = get_color_for_rsi(value)
                row_data[col] = {
                    'value': f"{value:.1f}" if pd.notna(value) else '--',
                    'color': color,
                    'bg': '#f8f9fa'
                }
            elif col == 'Z-score':
                color = '#FF4444' if abs(value) > 2 else '#FFA500' if abs(value) > 1 else '#666666'
                row_data[col] = {
                    'value': f"{value:+.2f}" if pd.notna(value) else '--',
                    'color': color,
                    'bg': '#f8f9fa'
                }
            elif col == 'Price_USD':
                row_data[col] = {
                    'value': f"${value:,.2f}" if pd.notna(value) else '--',
                    'color': '#000000',
                    'bg': '#ffffff'
                }
            elif 'Alert' in col:
                row_data[col] = {
                    'value': 'ALERT' if value else '',
                    'color': '#FFFFFF' if value else '#666666',
                    'bg': '#FF4444' if value else '#f8f9fa'
                }
            else:
                row_data[col] = {
                    'value': f"{value:.2f}" if isinstance(value, (int, float)) and pd.notna(value) else str(value),
                    'color': '#000000',
                    'bg': '#ffffff'
                }
        table_data.append(row_data)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&family=Roboto:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
                font-family: 'Roboto', sans-serif;
                color: #333;
            }}
            .ib-container {{
                background: #ffffff;
                margin: 0;
                padding: 0;
                min-height: 100vh;
            }}
            .ib-header {{
                background: #0d47a1;
                color: white;
                padding: 15px 20px;
                border-bottom: 3px solid #1565c0;
            }}
            .ib-title {{
                font-size: 18px;
                font-weight: 600;
                margin: 0;
                font-family: 'Roboto', sans-serif;
            }}
            .filter-panel {{
                background: #e3f2fd;
                padding: 15px 20px;
                border-bottom: 2px solid #1565c0;
                display: flex;
                gap: 20px;
                align-items: center;
                flex-wrap: wrap;
            }}
            .filter-group {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .filter-label {{
                font-weight: 600;
                color: #0d47a1;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .filter-input {{
                padding: 6px 12px;
                border: 1px solid #1565c0;
                border-radius: 4px;
                font-size: 12px;
                font-family: 'Roboto Mono', monospace;
                background: white;
                min-width: 120px;
            }}
            .filter-input:focus {{
                outline: none;
                border-color: #0d47a1;
                box-shadow: 0 0 0 2px rgba(13, 71, 161, 0.2);
            }}
            .filter-button {{
                padding: 6px 16px;
                background: #0d47a1;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }}
            .filter-button:hover {{
                background: #1565c0;
            }}
            .clear-button {{
                background: #666;
                padding: 6px 12px;
            }}
            .clear-button:hover {{
                background: #888;
            }}
            .filter-info {{
                background: #fff3e0;
                padding: 8px 20px;
                border-bottom: 1px solid #ffb74d;
                font-size: 12px;
                color: #ef6c00;
                display: none;
            }}
            .ib-toolbar {{
                background: #f8f9fa;
                padding: 10px 20px;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: #666;
            }}
            .ib-stats {{
                display: flex;
                gap: 30px;
            }}
            .ib-stat {{
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .ib-stat-number {{
                font-weight: 600;
                font-size: 14px;
                color: #0d47a1;
            }}
            .ib-stat-label {{
                font-size: 11px;
                color: #666;
                text-transform: uppercase;
            }}
            .ib-table-container {{
                overflow: auto;
                background: white;
                position: relative;
                max-height: 70vh;
            }}
            .ib-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                font-family: 'Roboto Mono', monospace;
                font-size: 12px;
                background: white;
            }}
            .ib-table thead {{
                background: #e3f2fd;
            }}
            .ib-table th {{
                padding: 8px 12px;
                text-align: right;
                font-weight: 600;
                font-size: 11px;
                color: #0d47a1;
                border-right: 1px solid #ccc;
                border-bottom: 2px solid #0d47a1;
                white-space: nowrap;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                cursor: pointer;
                user-select: none;
                position: relative;
                background: #e3f2fd;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            .ib-table th:hover {{
                background: #bbdefb;
            }}
            .ib-table th::after {{
                content: '⇅';
                position: absolute;
                right: 4px;
                top: 50%;
                transform: translateY(-50%);
                opacity: 0.5;
                font-size: 10px;
            }}
            .ib-table th:first-child {{
                text-align: left;
                background: #bbdefb;
                position: sticky;
                left: 0;
                z-index: 11;
                border-right: 2px solid #0d47a1;
            }}
            .ib-table th:first-child:hover {{
                background: #90caf9;
            }}
            .ib-table td {{
                padding: 6px 12px;
                text-align: right;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #f0f0f0;
                font-weight: 400;
                white-space: nowrap;
            }}
            .ib-table td:first-child {{
                text-align: left;
                font-weight: 600;
                background: #fafafa;
                border-right: 2px solid #ccc;
                position: sticky;
                left: 0;
                z-index: 5;
                box-shadow: 2px 0 5px rgba(0,0,0,0.1);
            }}
            .ib-table tbody tr:hover td:first-child {{
                background-color: #e3f2fd;
            }}
            .ib-table tbody tr:hover {{
                background-color: #f0f8ff;
            }}
            .ib-table tbody tr:nth-child(even) {{
                background-color: #fafafa;
            }}
            .ib-table tbody tr:nth-child(even):hover {{
                background-color: #f0f8ff;
            }}
            .ib-table tbody tr:nth-child(even) td:first-child {{
                background-color: #f5f5f5;
            }}
            .ib-table tbody tr:nth-child(even):hover td:first-child {{
                background-color: #e3f2fd;
            }}
            .positive {{
                color: #00C851 !important;
                font-weight: 500;
            }}
            .negative {{
                color: #FF4444 !important;
                font-weight: 500;
            }}
            .neutral {{
                color: #666666;
            }}
            .alert-cell {{
                background: #FF4444 !important;
                color: white !important;
                font-weight: 600;
                text-align: center;
                animation: blink 2s infinite;
            }}
            @keyframes blink {{
                0%, 50% {{ opacity: 1; }}
                51%, 100% {{ opacity: 0.7; }}
            }}
            .price-cell {{
                font-weight: 600;
                color: #000;
            }}
            .ticker-cell {{
                color: #0d47a1;
                font-weight: 600;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 8px 20px;
                border-top: 1px solid #dee2e6;
                font-size: 10px;
                color: #666;
                text-align: center;
            }}
            .hidden-row {{
                display: none !important;
            }}
            @media (max-width: 768px) {{
                .filter-panel {{
                    flex-direction: column;
                    gap: 10px;
                    align-items: stretch;
                }}
                .filter-group {{
                    justify-content: space-between;
                }}
                .filter-input {{
                    min-width: 100px;
                }}
                .ib-table {{
                    font-size: 10px;
                }}
                .ib-table th,
                .ib-table td {{
                    padding: 4px 6px;
                }}
                .ib-stats {{
                    gap: 15px;
                }}
                .ib-table-container {{
                    max-height: 60vh;
                }}
            }}
        </style>
        <script>
            let sortDirection = {{}};
            let originalData = {json.dumps(original_data)};
            let allRows = [];
            
            function initializeFilters() {{
                // Store all table rows for filtering
                const tbody = document.querySelector('.ib-table tbody');
                allRows = Array.from(tbody.querySelectorAll('tr'));
                
                // Set initial filter values if provided
                const symbolInput = document.getElementById('symbol-filter');
                const typeInput = document.getElementById('type-filter');
                
                if ('{symbol_filter or ""}') {{
                    symbolInput.value = '{symbol_filter or ""}';
                }}
                if ('{type_filter or ""}') {{
                    typeInput.value = '{type_filter or ""}';
                }}
                
                // Add event listeners
                symbolInput.addEventListener('input', applyFilters);
                typeInput.addEventListener('input', applyFilters);
                
                // Apply initial filters
                applyFilters();
            }}
            
            function applyFilters() {{
                const symbolFilter = document.getElementById('symbol-filter').value.toLowerCase();
                const typeFilter = document.getElementById('type-filter').value.toLowerCase();
                const filterInfo = document.querySelector('.filter-info');
                
                let visibleCount = 0;
                
                allRows.forEach((row, index) => {{
                    const rowData = originalData[index];
                    let showRow = true;
                    
                    // Apply symbol filter
                    if (symbolFilter && rowData.Ticker) {{
                        showRow = showRow && rowData.Ticker.toLowerCase().includes(symbolFilter);
                    }}
                    
                    // Apply type filter
                    if (typeFilter) {{
                        const assetClass = rowData['Asset Class'] || '';
                        showRow = showRow && assetClass.toLowerCase().includes(typeFilter);
                    }}
                    
                    if (showRow) {{
                        row.classList.remove('hidden-row');
                        visibleCount++;
                    }} else {{
                        row.classList.add('hidden-row');
                    }}
                }});
                
                // Update stats
                document.querySelector('.ib-stat-number').textContent = visibleCount;
                
                // Show/hide filter info
                if (symbolFilter || typeFilter) {{
                    const filters = [];
                    if (symbolFilter) filters.push(`Symbol contains: "${{symbolFilter}}"`);
                    if (typeFilter) filters.push(`Type contains: "${{typeFilter}}"`);
                    
                    filterInfo.innerHTML = `<strong>Active Filters:</strong> ${{filters.join(', ')}} | Showing ${{visibleCount}} of ${{originalData.length}} assets`;
                    filterInfo.style.display = 'block';
                }} else {{
                    filterInfo.style.display = 'none';
                }}
            }}
            
            function clearFilters() {{
                document.getElementById('symbol-filter').value = '';
                document.getElementById('type-filter').value = '';
                applyFilters();
            }}
            
            function sortTable(columnIndex, columnName) {{
                const table = document.querySelector('.ib-table tbody');
                const visibleRows = Array.from(table.querySelectorAll('tr:not(.hidden-row)'));
                
                // Toggle sort direction
                sortDirection[columnName] = sortDirection[columnName] === 'asc' ? 'desc' : 'asc';
                const direction = sortDirection[columnName];
                
                // Update header indicators
                document.querySelectorAll('.ib-table th').forEach((th, index) => {{
                    if (index === columnIndex) {{
                        th.style.background = direction === 'asc' ? '#90caf9' : '#64b5f6';
                        th.innerHTML = th.innerHTML.replace(/ [↑↓]/g, '');
                        th.innerHTML += direction === 'asc' ? ' ↑' : ' ↓';
                    }} else {{
                        th.innerHTML = th.innerHTML.replace(/ [↑↓]/g, '');
                        if (index === 0) {{
                            th.style.background = '#bbdefb';
                        }} else {{
                            th.style.background = '#e3f2fd';
                        }}
                    }}
                }});
                
                visibleRows.sort((a, b) => {{
                    const aVal = a.cells[columnIndex].textContent.trim();
                    const bVal = b.cells[columnIndex].textContent.trim();
                    
                    const aNum = parseFloat(aVal.replace(/[^-0-9.]/g, ''));
                    const bNum = parseFloat(bVal.replace(/[^-0-9.]/g, ''));
                    
                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return direction === 'asc' ? aNum - bNum : bNum - aNum;
                    }}
                    
                    return direction === 'asc' ? 
                        aVal.localeCompare(bVal) : 
                        bVal.localeCompare(aVal);
                }});
                
                // Reappend sorted visible rows
                const hiddenRows = Array.from(table.querySelectorAll('tr.hidden-row'));
                table.innerHTML = '';
                visibleRows.forEach(row => table.appendChild(row));
                hiddenRows.forEach(row => table.appendChild(row));
            }}
            
            // Initialize when page loads
            document.addEventListener('DOMContentLoaded', initializeFilters);
        </script>
    </head>
    <body>
        <div class="ib-container">
            <div class="ib-header">
                <h1 class="ib-title">{title}</h1>
            </div>
            
            <div class="filter-panel">
                <div class="filter-group">
                    <label class="filter-label" for="symbol-filter">Symbol:</label>
                    <input type="text" id="symbol-filter" class="filter-input" placeholder="Filter by symbol...">
                </div>
                <div class="filter-group">
                    <label class="filter-label" for="type-filter">Type:</label>
                    <input type="text" id="type-filter" class="filter-input" placeholder="Filter by type...">
                </div>
                <button class="filter-button clear-button" onclick="clearFilters()">Clear Filters</button>
            </div>
            
            <div class="filter-info"></div>
            
            <div class="ib-toolbar">
                <div class="ib-stats">
                    <div class="ib-stat">
                        <div class="ib-stat-number">{len(filtered_df)}</div>
                        <div class="ib-stat-label">Positions</div>
                    </div>
                    <div class="ib-stat">
                        <div class="ib-stat-number">{pd.Timestamp.now().strftime('%H:%M:%S')}</div>
                        <div class="ib-stat-label">Last Update</div>
                    </div>
                    <div class="ib-stat">
                        <div class="ib-stat-number">{len([col for col in filtered_df.columns if 'Alert' in col])}</div>
                        <div class="ib-stat-label">Alert Types</div>
                    </div>
                </div>
                <div>
                    Market Status: <span style="color: #00C851; font-weight: 600;">LIVE</span>
                </div>
            </div>
            
            <div class="ib-table-container">
                <table class="ib-table">
                    <thead>
                        <tr>
    """

    # Add headers with appropriate icons and formatting
    column_index = 0
    for col in filtered_df.columns:
        header_name = col
        if col == 'Ticker':
            header_name = 'Symbol'
        elif col == 'Price_USD':
            header_name = 'Last Price'
        elif col == 'Asset Class':
            header_name = 'Type'
        elif col == '%FromMA50':
            header_name = 'MA50%'
        elif col == '%FromMA200':
            header_name = 'MA200%'
        elif col in ['24h', '7d', '1m', '3m', '1y']:
            header_name = col.upper()
        elif col in ['24h_RS', '7d_RS', '1m_RS', '3m_RS', '1y_RS']:
            header_name = col.upper().replace('_', ' ')

        html_content += f'<th onclick="sortTable({column_index}, \'{col}\')">{header_name}</th>'
        column_index += 1

    html_content += """
                        </tr>
                    </thead>
                    <tbody>
    """

    # Add rows with professional styling
    for row_data in table_data:
        html_content += '<tr>'
        for col in filtered_df.columns:
            cell_data = row_data[col]
            value = cell_data['value']
            color = cell_data['color']
            bg_color = cell_data.get('bg', '#ffffff')

            css_class = ""
            if 'Alert' in col and 'ALERT' in str(value):
                css_class = "alert-cell"
            elif col == 'Ticker':
                css_class = "ticker-cell"
            elif col == 'Price_USD':
                css_class = "price-cell"
            elif col in ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200', '24h_RS', '7d_RS', '1m_RS', '3m_RS', '1y_RS']:
                if '+' in str(value):
                    css_class = "positive"
                elif '-' in str(value) and value != '--':
                    css_class = "negative"
                else:
                    css_class = "neutral"

            style = f"color: {color}; background-color: {bg_color};"
            html_content += f'<td class="{css_class}" style="{style}">{value}</td>'
        html_content += '</tr>'

    html_content += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                Data provided by Yahoo Finance | 
                Portfolio Analysis System
            </div>
        </div>
    </body>
    </html>
    """

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Professional trading-style HTML report with interactive filters generated: {output_file}")

    return html_content

def create_ib_style_dash_app(df, title="Portfolio Management System"):
    """Create an Interactive Brokers-style Dash app"""

    # Prepare columns for Dash DataTable
    columns = []
    for col in df.columns:
        display_name = col
        if col == 'Ticker':
            display_name = 'Symbol'
        elif col == 'Price_USD':
            display_name = 'Last Price'
        elif col == 'Asset Class':
            display_name = 'Type'
        elif col == '%FromMA50':
            display_name = 'MA50%'
        elif col == '%FromMA200':
            display_name = 'MA200%'
        elif col in ['24h', '7d', '1m', '3m', '1y']:
            display_name = col.upper()
        elif col in ['24h_RS', '7d_RS', '1m_RS', '3m_RS', '1y_RS']:
            display_name = col.upper().replace('_', ' ')

        col_config = {
            "name": display_name,
            "id": col,
            "type": "numeric" if col not in ['Ticker', 'Asset Class', 'Currency'] and 'Alert' not in col else "text",
            "format": {"specifier": ".2f"} if col in ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200', 'Z-score', '24h_RS', '7d_RS', '1m_RS', '3m_RS', '1y_RS'] else {}
        }

        if col == 'Price_USD':
            col_config["format"] = {"specifier": "$.2f"}
        elif col == 'RSI':
            col_config["format"] = {"specifier": ".1f"}

        columns.append(col_config)

    # Prepare data
    data = df.fillna('--').to_dict('records')

    # Create Dash app
    app = dash.Dash(__name__)

    # Professional conditional styling
    style_data_conditional = []

    # Style percentage columns with professional colors (including RS columns)
    percentage_cols = ['24h', '7d', '1m', '3m', '1y', '%FromMA50', '%FromMA200', '24h_RS', '7d_RS', '1m_RS', '3m_RS', '1y_RS']
    for col in percentage_cols:
        if col in df.columns:
            style_data_conditional.extend([
                {
                    'if': {
                        'filter_query': f'{{{col}}} > 0',
                        'column_id': col
                    },
                    'color': '#00C851',
                    'fontWeight': '500',
                    'backgroundColor': '#f0f8f0'
                },
                {
                    'if': {
                        'filter_query': f'{{{col}}} < 0',
                        'column_id': col
                    },
                    'color': '#FF4444',
                    'fontWeight': '500',
                    'backgroundColor': '#fff0f0'
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
                'color': '#FF4444',
                'fontWeight': '600',
                'backgroundColor': '#fff0f0'
            },
            {
                'if': {
                    'filter_query': '{RSI} <= 30',
                    'column_id': 'RSI'
                },
                'color': '#00C851',
                'fontWeight': '600',
                'backgroundColor': '#f0f8f0'
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
            'backgroundColor': '#FF4444',
            'color': 'white',
            'fontWeight': 'bold'
        })

    # Style ticker column
    if 'Ticker' in df.columns:
        style_data_conditional.append({
            'if': {'column_id': 'Ticker'},
            'color': '#0d47a1',
            'fontWeight': '600'
        })

    app.layout = html.Div([
        # Header
        html.Div([
            html.H1(title, style={
                'margin': '0',
                'color': 'white',
                'fontSize': '18px',
                'fontWeight': '600',
                'fontFamily': 'Roboto, sans-serif'
            })
        ], style={
            'backgroundColor': '#0d47a1',
            'padding': '15px 20px',
            'borderBottom': '3px solid #1565c0'
        }),

        # Toolbar
        html.Div([
            html.Div([
                html.Div([
                    html.Div(str(len(df)), style={'fontWeight': '600', 'fontSize': '14px', 'color': '#0d47a1'}),
                    html.Div("POSITIONS", style={'fontSize': '11px', 'color': '#666', 'textTransform': 'uppercase'})
                ], style={'textAlign': 'center'}),

                html.Div([
                    html.Div(pd.Timestamp.now().strftime('%H:%M:%S'), style={'fontWeight': '600', 'fontSize': '14px', 'color': '#0d47a1'}),
                    html.Div("LAST UPDATE", style={'fontSize': '11px', 'color': '#666', 'textTransform': 'uppercase'})
                ], style={'textAlign': 'center'}),

                html.Div([
                    html.Div(str(len(alert_cols)), style={'fontWeight': '600', 'fontSize': '14px', 'color': '#0d47a1'}),
                    html.Div("ALERT TYPES", style={'fontSize': '11px', 'color': '#666', 'textTransform': 'uppercase'})
                ], style={'textAlign': 'center'}),
            ], style={'display': 'flex', 'gap': '30px'}),

            html.Div([
                "Market Status: ",
                html.Span("LIVE", style={'color': '#00C851', 'fontWeight': '600'})
            ])
        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '10px 20px',
            'borderBottom': '1px solid #dee2e6',
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'fontSize': '12px',
            'color': '#666'
        }),

        # DataTable with fixed first column
        dash_table.DataTable(
            id='ib-table',
            columns=columns,
            data=data,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_action="native",
            page_current=0,
            page_size=25,
            fixed_columns={'headers': True, 'data': 1},
            style_table={
                'overflowX': 'auto',
                'backgroundColor': 'white',
                'fontFamily': 'Roboto Mono, monospace',
                'maxHeight': '80vh'
            },
            style_header={
                'backgroundColor': '#e3f2fd',
                'color': '#0d47a1',
                'fontWeight': '600',
                'fontSize': '11px',
                'textAlign': 'right',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px',
                'borderRight': '1px solid #ccc',
                'borderBottom': '2px solid #0d47a1',
                'position': 'sticky'
            },
            style_cell={
                'textAlign': 'right',
                'padding': '6px 12px',
                'fontFamily': 'Roboto Mono, monospace',
                'fontSize': '12px',
                'borderRight': '1px solid #e0e0e0',
                'borderBottom': '1px solid #f0f0f0',
                'whiteSpace': 'nowrap'
            },
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Ticker'},
                    'textAlign': 'left',
                    'fontWeight': '600',
                    'backgroundColor': '#fafafa',
                    'borderRight': '2px solid #0d47a1'
                }
            ],
            style_data={
                'backgroundColor': 'white',
                'color': '#333'
            },
            style_data_conditional=style_data_conditional,
            export_format="csv",
            export_headers="display"
        ),

        # Footer
        html.Div([
            f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | ",
            "Data provided by Yahoo Finance | ",
            "Portfolio Analysis System"
        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '8px 20px',
            'borderTop': '1px solid #dee2e6',
            'fontSize': '10px',
            'color': '#666',
            'textAlign': 'center'
        })
    ], style={
        'fontFamily': 'Roboto, sans-serif',
        'backgroundColor': '#f5f5f5',
        'minHeight': '100vh',
        'margin': '0'
    })

    return app

# Updated main functions
def print_asset_table_modern(asset_df, output_file="professional_asset_report.html", symbol_filter=None, type_filter=None):
    """Generate professional trading-style HTML report with optional filters"""
    return create_ib_style_html_table(
        asset_df,
        "Portfolio Management System - Asset Analysis",
        output_file,
        symbol_filter,
        type_filter
    )

def create_interactive_dashboard(asset_df, trades=None, port=8050):
    """Create and run a professional trading-style dashboard"""
    app = create_ib_style_dash_app(asset_df, "Portfolio Management System")

    print(f"Starting professional trading dashboard at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    try:
        app.run(debug=True, port=port)
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        print("You can still view the HTML reports that were generated.")

def print_alerts_modern(asset_df, output_file="professional_alerts_report.html"):
    """Generate modern responsive HTML report for alerts"""

    # Create separate tables for different alert types
    alerts_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trading Alerts System</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&family=Roboto:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body {{ 
                background: #f5f5f5; 
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 20px;
            }}
            .alert-container {{ 
                background: white; 
                border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .alert-header {{
                background: #d32f2f;
                color: white;
                padding: 15px 20px;
                font-weight: 600;
                font-size: 18px;
            }}
            .alert-section {{ 
                border-bottom: 1px solid #eee;
                padding: 20px;
            }}
            .alert-title {{ 
                color: #d32f2f; 
                font-weight: 600; 
                margin-bottom: 15px;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .no-alerts {{ 
                text-align: center; 
                color: #666; 
                font-style: italic; 
                padding: 30px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="alert-container">
            <div class="alert-header">
                Trading Alerts System - Risk Management
            </div>
    """

    # Process each alert type
    alert_types = [
        ('Strong Sell Alert', 'Strong Sell Alerts - Immediate Action Required', '#d32f2f'),
        ('Strong Buy Alert', 'Strong Buy Alerts - Opportunity Identified', '#2e7d32'),
        ('Less Strong Sell Alert', 'Moderate Sell Alerts - Monitor Closely', '#f57c00'),
        ('Less Strong Buy Alert', 'Moderate Buy Alerts - Consider Entry', '#1976d2')
    ]

    for alert_col, title, color in alert_types:
        alerts_html += f'<div class="alert-section">'
        alerts_html += f'<h2 class="alert-title" style="color: {color};">{title}</h2>'

        if alert_col in asset_df.columns:
            filtered_df = asset_df[asset_df[alert_col] == True]
            if not filtered_df.empty:
                table_html = create_ib_style_html_table(filtered_df, title)
                # Extract just the table part
                table_start = table_html.find('<div class="ib-table-container">')
                table_end = table_html.find('</div>', table_start) + 6
                alerts_html += table_html[table_start:table_end]
            else:
                alerts_html += '<div class="no-alerts">No alerts in this category</div>'
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

    print(f"Professional alerts report generated: {output_file}")
    return alerts_html

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