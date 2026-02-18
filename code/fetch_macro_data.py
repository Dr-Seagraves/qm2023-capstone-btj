"""
QM 2023 Capstone Project: M1 - Macro Supplementary Data Fetch & Clean
Team: BTJ
Members: [List names]

Fetches monthly FRED series aligned to the REIT panel (2000-01 to 2024-09):
  FEDFUNDS     — Effective Federal Funds Rate (%)
  MORTGAGE30US — 30-Year Fixed Mortgage Rate (%)
  CPIAUCSL     — Consumer Price Index (1982-84=100)
  UNRATE       — Unemployment Rate (%)

Two modes (tried in order):
  1. FRED API key set → fetch live via fredapi
  2. No key → load pre-downloaded CSVs from data/raw/fred_macro_raw.csv
     OR individual CSVs from FRED website (e.g. data/raw/FEDFUNDS.csv)

To use FRED API:
  - Register free at https://fred.stlouisfed.org/docs/api/api_key.html
  - Set environment variable:  export FRED_API_KEY="your32charkey"
    OR replace the FRED_API_KEY placeholder below.

To download CSVs manually (no API key needed):
  1. Go to https://fred.stlouisfed.org/series/FEDFUNDS → Download → CSV
  2. Repeat for MORTGAGE30US, CPIAUCSL, UNRATE
  3. Save all four files to data/raw/  (keep original FRED filenames, e.g. FEDFUNDS.csv)
  4. Run this script — it will merge them automatically.

Steps:
  1. Load data (API or CSVs)
  2. Align to monthly frequency (YYYY-MM)
  3. Forward-fill any sub-monthly gaps
  4. Save to data/processed/fred_macro_clean.csv
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

FRED_SERIES = ["FEDFUNDS", "MORTGAGE30US", "CPIAUCSL", "UNRATE"]
START = "2000-01-01"
END = "2024-12-31"

# Set your API key here OR via environment variable FRED_API_KEY
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")


# ---------------------------------------------------------------------------
# Section 1A: Fetch from FRED API (requires valid API key)
# ---------------------------------------------------------------------------

def fetch_from_api() -> pd.DataFrame:
    from fredapi import Fred

    if not FRED_API_KEY or len(FRED_API_KEY) != 32:
        raise ValueError("No valid FRED API key. Set FRED_API_KEY environment variable.")

    fred = Fred(api_key=FRED_API_KEY)
    frames = []
    for series in FRED_SERIES:
        print(f"  Fetching {series} from FRED API...")
        s = fred.get_series(series, observation_start=START, observation_end=END)
        s.name = series.lower()
        frames.append(s)
        time.sleep(0.5)

    macro = pd.concat(frames, axis=1).reset_index()
    macro = macro.rename(columns={"index": "date"})
    return macro


# ---------------------------------------------------------------------------
# Section 1B: Load from locally downloaded FRED CSV files
# ---------------------------------------------------------------------------

def load_from_local_csvs() -> pd.DataFrame:
    """
    Accepts either:
      (a) Individual FRED CSVs named FEDFUNDS.csv, MORTGAGE30US.csv, etc.
      (b) A single combined file: fred_macro_raw.csv with columns date + series names
    """
    # Option (b): single combined file
    combined = RAW_DATA_DIR / "fred_macro_raw.csv"
    if combined.exists():
        print(f"  Loading combined file: {combined.name}")
        df = pd.read_csv(combined)
        df.columns = df.columns.str.strip().str.lower()
        return df

    # Option (a): individual FRED-downloaded CSVs
    frames = []
    for series in FRED_SERIES:
        csv_path = RAW_DATA_DIR / f"{series}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Missing {csv_path.name}.\n"
                f"Download from https://fred.stlouisfed.org/series/{series} and save to data/raw/\n"
                "OR set a valid FRED API key."
            )
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip().str.lower()
        # FRED CSV has columns: DATE, <SERIES>
        date_col = [c for c in df.columns if "date" in c][0]
        val_col  = [c for c in df.columns if c != date_col][0]
        df = df.rename(columns={date_col: "date", val_col: series.lower()})
        # FRED marks missing as "."
        df[series.lower()] = pd.to_numeric(df[series.lower()], errors="coerce")
        frames.append(df.set_index("date"))
        print(f"  Loaded {csv_path.name}: {len(df):,} rows")

    combined_df = pd.concat(frames, axis=1).reset_index()
    combined_df = combined_df.rename(columns={"index": "date"})
    return combined_df


# ---------------------------------------------------------------------------
# Section 2: Align to monthly frequency
# ---------------------------------------------------------------------------

def align_to_monthly(macro: pd.DataFrame) -> pd.DataFrame:
    macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
    macro = macro.dropna(subset=["date"]).copy()

    value_cols = [c for c in macro.columns if c not in ("date",)]
    macro["ym"] = macro["date"].dt.to_period("M").dt.strftime("%Y-%m")

    # Collapse sub-monthly series (e.g. MORTGAGE30US is weekly) to monthly last
    monthly = (
        macro.groupby("ym")[value_cols]
        .last()
        .reset_index()
        .sort_values("ym")
    )
    monthly[value_cols] = monthly[value_cols].ffill()
    return monthly


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n=== M1: Fetch/Clean Supplementary Macro Data (FRED) ===")

    # Section 1: Load data
    if FRED_API_KEY and len(FRED_API_KEY) == 32:
        print("Using FRED API key.")
        macro_raw = fetch_from_api()
    else:
        print("No valid API key — loading from local FRED CSVs in data/raw/")
        macro_raw = load_from_local_csvs()

    print(f"Raw FRED rows: {len(macro_raw):,}")

    # Section 2: Align to monthly
    monthly = align_to_monthly(macro_raw)

    # Restrict to REIT panel date range
    monthly = monthly[(monthly["ym"] >= "2000-01") & (monthly["ym"] <= "2024-12")].copy()

    # Verify coverage
    value_cols = [c for c in monthly.columns if c != "ym"]
    missing_counts = monthly[value_cols].isnull().sum()
    print("Missing values per series after cleaning:")
    print(missing_counts.to_string())

    print(f"\nMacro rows: {len(monthly):,}")
    print(f"Date range: {monthly['ym'].min()} → {monthly['ym'].max()}")
    print(monthly.head(3).to_string())

    # Section 5: Save
    output_file = PROCESSED_DATA_DIR / "fred_macro_clean.csv"
    monthly.to_csv(output_file, index=False)
    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()
