# src/stock.py
import yfinance as yf
import pandas as pd


def fetch_stock(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Download daily close prices and resample to quarterly end.
    """
    hist = yf.Ticker(ticker).history(start=start, end=end)
    hist.index = hist.index.tz_localize(None)
    df = hist['Close'].resample('Q').last().to_frame(name=f"{ticker}_Close")
    df.index.name = 'end'
    return df
