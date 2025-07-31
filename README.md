# Asset Valuation Analyzer

A comprehensive portfolio analysis tool that combines technical indicators, statistical analysis, and modern interactive reporting to help make informed investment decisions.

## 🚀 Features

- **Technical Analysis**: Calculates Z-scores, performance metrics, and statistical indicators
- **Multi-Currency Support**: Automatic currency conversion with FX rate validation
- **Trading Alerts**: Generates buy/sell signals based on statistical thresholds
- **Portfolio Rebalancing**: Provides rebalancing recommendations
- **Modern HTML Reports**: Interactive, responsive dashboards with filtering capabilities
- **Console Output**: Traditional tabular data for quick analysis

## 📋 Prerequisites

- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
    - pandas
    - yfinance (or your preferred data source)
    - Additional dependencies as specified in your requirements

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/asset-valuation-analyzer.git
   cd asset-valuation-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your assets and settings in the configuration files

## 🎯 Usage

### Basic Usage

Run the analyzer with default settings:

```bash
python main.py
```

The script will:
1. Load your configured assets and currencies
2. Download market data
3. Calculate technical indicators and performance metrics
4. Generate trading alerts
5. Create interactive HTML reports
6. Optionally launch an interactive dashboard

### Output Files

The analyzer generates several output files:

- **modern_asset_report.html** - Interactive asset table with filtering and sorting
- **modern_alerts_report.html** - Alert dashboard with buy/sell recommendations
- **Console output** - Real-time analysis results and summary statistics

### Runtime

- HTML reports are typically generated in 20-30 seconds, depending on the number of securities analyzed
- Simply open the generated HTML files in your browser to view the interactive reports

## 📊 What It Analyzes

### Assets & Performance
- **Z-Score Analysis**: Statistical overvaluation/undervaluation metrics
- **Multi-timeframe Performance**: Configurable performance periods
- **Benchmark Comparison**: Relative performance against market indices
- **Currency Normalization**: All values converted to USD for comparison

### Trading Signals
- **Strong Buy/Sell Alerts**: High-confidence signals based on statistical thresholds
- **Moderate Alerts**: Less aggressive signals for conservative strategies
- **Portfolio Rebalancing**: Top-N recommendations for portfolio optimization

### Technical Features
- **FX Rate Validation**: Sanity checks for currency conversion rates
- **Data Quality Checks**: Handles missing data and validation
- **Flexible Configuration**: Easy customization of indicators and thresholds

## 🔧 Configuration

The tool uses configuration files to specify:
- Asset tickers to analyze
- Currency pairs for FX conversion
- Performance calculation periods
- Alert thresholds and parameters
- Benchmark comparisons

## 📱 Interactive Features

### Modern HTML Reports
- **Responsive Design**: Works on desktop and mobile devices
- **Interactive Filtering**: Sort and filter assets by any metric
- **Real-time Search**: Quick asset lookup
- **Visual Indicators**: Color-coded alerts and performance metrics

### Optional Dashboard
When prompted, you can launch an interactive web dashboard for real-time analysis and deeper exploration of the data.

## 🚨 Alerts System

The analyzer generates four types of alerts:
- **Strong Sell Alert**: High-confidence sell signals
- **Strong Buy Alert**: High-confidence buy opportunities
- **Less Strong Sell Alert**: Moderate sell considerations
- **Less Strong Buy Alert**: Moderate buy opportunities

## 📈 Sample Output

```
📊 HTML Reports Generated:
- modern_asset_report.html (Interactive asset table with filtering)
- modern_alerts_report.html (Alert dashboard)

🎯 Want to launch interactive dashboard? (y/n):
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. It does not constitute financial advice. Always do your own research and consult with financial professionals before making investment decisions.

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub or contact the maintainer.

---

**Happy Analyzing! 📈**