# main_refactored.py

from financials import get_cik, fetch_financials
from parser import read_transcripts
from stock import fetch_stock
from analytics import (compute_correlations, granger_tests,
                       fit_arimax, forecast_arimax)

import pandas as pd

def run_pipeline(ticker, start_date, end_date, email, transcript_dir="data"):
    # 1) SEC financials
    cik      = get_cik(ticker, email)
    fin_df   = fetch_financials(cik, start_date, end_date, email)
    fin_df.to_csv("outputs/financials.csv")

    # 2) Text features
    txt_df   = read_transcripts(transcript_dir,
                                int(start_date[:4]), int(end_date[:4]))
    txt_df.to_csv("outputs/text_features.csv")

    # 3) Stock prices
    stk_df   = fetch_stock(ticker, start_date, f"{int(end_date[:4])+1}-01-01")
    stk_df.to_csv("outputs/stock_quarterly.csv")

    # 4) Merge
    merged = fin_df.merge(txt_df,  left_index=True, right_index=True, how="left") \
                   .merge(stk_df, left_index=True, right_index=True, how="left")
    merged.to_csv("outputs/merged_pipeline.csv")

    # 5) Analytics
    # Determine the correct stock price column for return calculation
    expected_col = f"{ticker}_Close"
    price_col = expected_col if expected_col in merged.columns else "Close" if "Close" in merged.columns else None
    if price_col:
        merged['Return'] = merged[price_col].pct_change()
    else:
        merged['Return'] = None  # or raise a warning/log
    feats = ['avg_sentiment','buzz_count'] + [c for c in merged if c.startswith('SWOT_')]
    corrs = compute_correlations(merged, 'Return', feats)

    pos_feats = corrs[corrs>0].index.tolist()
    exog      = merged[pos_feats].shift(1).dropna()
    y, exog   = merged['Return'].align(exog, join="inner")
    res       = fit_arimax(y, exog)
    fc        = forecast_arimax(res, exog.iloc[-1], steps=4)
    fc.to_csv("outputs/dual_forecast.csv")

    return {
        "financials": "outputs/financials.csv",
        "text_features": "outputs/text_features.csv",
        "stock": "outputs/stock_quarterly.csv",
        "merged": "outputs/merged_pipeline.csv",
        "forecast": "outputs/dual_forecast.csv"
    }
