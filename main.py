import argparse
from src.financials import get_cik, fetch_financials
from src.parser    import read_transcripts
from src.stock     import fetch_stock
from src.analytics import (compute_correlations, granger_tests,
                           fit_arimax, forecast_arimax, evaluate_forecasts)

def main():
    p = argparse.ArgumentParser(...)
    p.add_argument("--email", required=True)
    p.add_argument("--ticker", required=True)
    p.add_argument("--transcript_dir", required=True)
    p.add_argument("--start_year", type=int, default=2020)
    p.add_argument("--end_year",   type=int, default=2024)
    args = p.parse_args()

    # 1) SEC financials
    cik      = get_cik(args.ticker, args.email)
    fin_df   = fetch_financials(cik, f"{args.start_year}-01-01",
                                f"{args.end_year}-12-31", args.email)
    fin_df.to_csv("financials.csv")

    # 2) Text features
    txt_df   = read_transcripts(args.transcript_dir, args.ticker,
                                args.start_year, args.end_year)
    txt_df.to_csv("text_features.csv")

    # 3) Stock prices
    stk_df   = fetch_stock(args.ticker,
                           f"{args.start_year}-01-01",
                           f"{args.end_year+1}-01-01")
    stk_df.to_csv("stock_quarterly.csv")

    # 4) Merge
    merged = fin_df.merge(txt_df,  left_index=True, right_index=True, how="left") \
                   .merge(stk_df, left_index=True, right_index=True, how="left")
    merged.to_csv("merged_pipeline.csv")

    # 5) Analytics
    merged['Return'] = merged[f"{args.ticker}_Close"].pct_change()
    feats = ['avg_sentiment','buzz_count'] + [c for c in merged if c.startswith('SWOT_')]
    corrs = compute_correlations(merged, 'Return', feats)
    print("Correlations:\n", corrs)

    pvals = granger_tests(merged, 'Return', feats)
    print("Granger p-values:\n", pvals)

    # 6) ARIMAX with only positive-corr exog
    pos_feats = corrs[corrs>0].index.tolist()
    exog      = merged[pos_feats].shift(1).dropna()
    y, exog   = merged['Return'].align(exog, join="inner")
    res       = fit_arimax(y, exog)
    print(res.summary())

    fc        = forecast_arimax(res, exog.iloc[-1], steps=4)
    print("Forecast:\n", fc)

    # 7) Optional: evaluate against naive / etc.
    #    results = evaluate_forecasts(...)
    #    print(results)

if __name__=="__main__":
    main()

