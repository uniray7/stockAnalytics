# US Stock Analytics

A complete US stock analysis service featuring:
1. Real-time data crawler (5-min intervals) using `yfinance`
2. Visualization dashboard using `Streamlit`
3. Strategy backtesting tool using `backtrader`

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the crawler:
```bash
python src/crawler.py
```

4. Run the visualization web dashboard:
```bash
streamlit run src/app.py
```
