# src/financials.py

import requests
import pandas as pd


def get_cik(ticker: str, email: str) -> str:
    """
    Fetch and zero-pad the CIK for a given ticker from SEC’s index.
    """
    headers = {'User-Agent': email}
    url = "https://www.sec.gov/files/company_tickers.json"
    df = pd.DataFrame.from_dict(
        requests.get(url, headers=headers).json(),
        orient='index'
    )
    df['cik_str'] = df['cik_str'].astype(str).str.zfill(10)
    return df.loc[df['ticker'] == ticker, 'cik_str'].iloc[0]


def fetch_financials(
    cik: str,
    start: str,
    end: str,
    email: str
) -> pd.DataFrame:
    """
    Download US-GAAP XBRL facts and return a wide DataFrame of quarterly metrics.
    """
    headers = {'User-Agent': email}
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    data = requests.get(url, headers=headers).json()['facts']['us-gaap']

    desired = {
        'TotalRevenue':    ['Revenues'],
        'OperatingIncome': ['OperatingIncomeLoss'],
        'EPS_Basic':       ['EarningsPerShareBasic'],
        'NetIncome':       ['NetIncomeLoss'],
        'OpCashFlow':      ['NetCashProvidedByUsedInOperatingActivities'],
        'CapEx':           ['AdditionsToPropertyPlantAndEquipment',
                            'PaymentsToAcquirePropertyPlantAndEquipment'],
        'CurrAssets':      ['AssetsCurrent'],
        'CurrLiabilities': ['LiabilitiesCurrent'],
        'LT_Debt':         ['LongTermDebtNoncurrent'],
        'InterestExpense': ['InterestExpense'],
        'CostOfRevenue':   ['CostOfRevenue','CostsAndExpenses','CostOfGoodsAndServicesSold'],
        'Depreciation':    ['DepreciationAndAmortization']
    }

    frames = []
    available = set(data.keys())
    for metric, patterns in desired.items():
        tag = next((t for t in patterns if t in available), None)
        if not tag:
            tag = next((t for t in available
                        if any(p.lower() in t.lower() for p in patterns)), None)
        if not tag:
            print(f"⚠️ skipping {metric}: no XBRL tag")
            continue

        units = data[tag]['units']
        bucket = 'USD' if 'USD' in units else next(iter(units))
        df = pd.DataFrame(units[bucket])
        df = df[df['form'].isin(['10-Q','10-K'])]
        df['metric'] = metric
        frames.append(df[['end','val','metric']])

    all_q = pd.concat(frames, ignore_index=True)
    all_q['end'] = pd.to_datetime(all_q['end'])
    wide = (
        all_q.pivot_table(index='end', columns='metric', values='val', aggfunc='last')
             .sort_index()
    )

    df = wide.loc[start:end].ffill()
    for col in df.columns:
        if col != 'EPS_Basic':
            df[col] = df[col] / 1e6
    rename = {m: f"{m} (USD M)" for m in df.columns if m != 'EPS_Basic'}
    rename['EPS_Basic'] = 'EPS_Basic (USD/share)'
    return df.rename(columns=rename)

def main(ticker: str, start: str, end: str, email: str):
    cik = get_cik(ticker, email)
    df = fetch_financials(cik, start, end, email)
    output_path = "outputs/financials.csv"
    df.to_csv(output_path, index=True)
    print(f"Financials saved to {output_path}")

