# src/parser.py

import os
import glob
import re
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter

# Download VADER lexicon if needed
nltk.download('vader_lexicon')

# Map quarters to month‐ends
MONTH_END = {
    "Q1": "03-31",
    "Q2": "06-30",
    "Q3": "09-30",
    "Q4": "12-31",
}

# Keywords for buzz & SWOT
PRODUCT_KEYWORDS = ["Optum", "UnitedHealthcare", "Rx", "Behavioral Health", "Benefits"]
SWOT_BUCKETS = {
    "Strength":    ["advantage", "lead", "innovate", "strength"],
    "Weakness":    ["challenge", "risk", "weakness", "concern"],
    "Opportunity": ["opportunity", "expand", "growth", "launch"],
    "Threat":      ["threat", "competitive", "pressure", "decline"],
}

def parse_quarter_end(path: str) -> pd.Timestamp:
    """
    Extract year and quarter from a filename, e.g.
      - "Aetna_2022_Q2.txt"
      - "UNH 2023 Q1.txt"
    """
    base = os.path.basename(path).replace(".txt", "")
    parts = re.split(r"[\s_]+", base)
    if len(parts) < 2:
        raise ValueError(f"Cannot parse quarter from filename: {base}")
    year, q = parts[-2], parts[-1].upper()
    if not re.match(r"Q[1-4]$", q):
        raise ValueError(f"Invalid quarter '{q}' in filename: {base}")
    return pd.to_datetime(f"{year}-{MONTH_END[q]}")

def read_transcripts(
    dirpath: str,
    start_year: int,
    end_year: int
) -> pd.DataFrame:
    """
    Load every .txt in `dirpath` between start_year and end_year,
    compute avg sentiment, buzz_count, and SWOT ratios per quarter.
    """
    pattern = os.path.join(dirpath, "*.txt")        # ← changed from ticker‐only
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No '.txt' transcripts found in {dirpath}")

    sia = SentimentIntensityAnalyzer()
    records = []

    for path in files:
        end = parse_quarter_end(path)
        if not (start_year <= end.year <= end_year):
            continue

        # read with fallback encodings
        try:
            text = open(path, encoding="utf8").read()
        except UnicodeDecodeError:
            text = open(path, encoding="latin-1").read()

        # sentence‐level sentiment
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        scores = [sia.polarity_scores(s)["compound"] for s in sentences]
        avg_sent = sum(scores) / len(scores) if scores else 0.0

        # buzz count
        buzz = sum(text.lower().count(k.lower()) for k in PRODUCT_KEYWORDS)

        # SWOT ratios
        cnt = Counter()
        for s in sentences:
            low = s.lower()
            for bkt, kws in SWOT_BUCKETS.items():
                if any(kw in low for kw in kws):
                    cnt[bkt] += 1
        swot = {f"SWOT_{b}": cnt[b] / len(sentences) if sentences else 0.0
                for b in SWOT_BUCKETS}

        records.append({
            "end": end,
            "avg_sentiment": avg_sent,
            "buzz_count": buzz,
            **swot
        })

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError(f"No valid transcripts parsed between {start_year} and {end_year}")
    df.set_index("end", inplace=True)
    df.sort_index(inplace=True)
    return df
