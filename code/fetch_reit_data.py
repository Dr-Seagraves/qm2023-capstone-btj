"""
QM 2023 Capstone Project: M1 - REIT Data Fetch & Clean
Team: BTJ
Members: [List names]

Dataset: REIT_sample_2000_2024_All_Variables.csv
  - 369 REITs, monthly data, 2000-2024
  - Primary outcome: usdret (USD return)
  - Entity key: permno | Time key: ym (format: 2003m10 → YYYY-MM)

Cleaning steps:
  1. Load & inspect raw data
  2. Parse ym column  (e.g. "2003m10" → "2003-10")
  3. Drop missing outcome (usdret) and missing entity/time keys
  4. Remove duplicate permno-ym pairs
  5. Winsorize usdret at 1st/99th percentile
  6. Drop observations with market_equity < 10M
  7. Save to data/processed/reit_master_clean.csv
"""

import sys
from pathlib import Path
import pandas as pd

# Allow running from project root or from code/
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_paths import RAW_DATA_DIR, PROCESSED_DATA_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_ym(series: pd.Series) -> pd.Series:
    """Convert 'YYYYmM' / 'YYYY-MM' strings to 'YYYY-MM' string format."""
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.lower()
        # "2003m10" → "2003-10", "2003m1" → "2003-01"
        .str.replace(r"m(\d)$", r"-0\1", regex=True)   # single-digit month
        .str.replace(r"m(\d{2})$", r"-\1", regex=True)  # two-digit month
    )
    parsed = pd.to_datetime(cleaned, format="%Y-%m", errors="coerce")
    return parsed.dt.strftime("%Y-%m")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n=== M1: Fetch/Clean Primary REIT Data ===")

    # ------------------------------------------------------------------
    # Section 1: Load raw data
    # ------------------------------------------------------------------
    raw_file = RAW_DATA_DIR / "reit_master_raw.csv"
    if not raw_file.exists():
        raise FileNotFoundError(
            f"Missing: {raw_file}\n"
            "Place reit_master_raw.csv in data/raw/ and rerun."
        )

    df = pd.read_csv(raw_file, dtype={"permno": "Int64"})
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    print(f"Rows loaded:   {len(df):,}")
    print(f"Columns: {df.columns.tolist()}")

    required = {"permno", "ym", "usdret", "market_equity"}
    missing_cols = sorted(required - set(df.columns))
    if missing_cols:
        raise ValueError(f"Raw file missing required columns: {missing_cols}")

    # ------------------------------------------------------------------
    # Section 2: Parse time variable
    # ------------------------------------------------------------------
    df["ym"] = parse_ym(df["ym"])
    invalid_ym = df["ym"].isna().sum()
    if invalid_ym:
        print(f"Rows with unparseable ym (dropped): {invalid_ym:,}")

    # ------------------------------------------------------------------
    # Section 3: Drop missing keys and missing outcome
    # ------------------------------------------------------------------
    before = len(df)
    df = df.dropna(subset=["permno", "ym", "usdret"]).copy()
    dropped_missing = before - len(df)
    pct_missing = 100 * dropped_missing / before
    print(f"Dropped (missing permno/ym/usdret): {dropped_missing:,}  ({pct_missing:.1f}%)")

    # Restrict to 2000-2024 to align with supplementary FRED data
    df = df[df["ym"] >= "2000-01"].copy()
    print(f"Rows after 2000-01 start filter:   {len(df):,}")

    # ------------------------------------------------------------------
    # Section 4: Remove duplicates
    # ------------------------------------------------------------------
    dup_count = df.duplicated(subset=["permno", "ym"]).sum()
    if dup_count:
        print(f"Duplicate permno-ym pairs removed (keep first): {dup_count:,}")
    df = df.drop_duplicates(subset=["permno", "ym"], keep="first")

    # ------------------------------------------------------------------
    # Section 5: Winsorize usdret at 1st/99th percentile
    # ------------------------------------------------------------------
    lower_pct = df["usdret"].quantile(0.01)
    upper_pct = df["usdret"].quantile(0.99)
    extreme = ((df["usdret"] < lower_pct) | (df["usdret"] > upper_pct)).sum()
    df["usdret"] = df["usdret"].clip(lower=lower_pct, upper=upper_pct)
    print(f"Winsorized usdret [{lower_pct:.4f}, {upper_pct:.4f}] — {extreme:,} values clipped")

    # ------------------------------------------------------------------
    # Section 6: Size filter (market_equity >= $10M)
    # ------------------------------------------------------------------
    pre_sz = len(df)
    df = df[df["market_equity"] >= 10].copy()
    print(f"Rows after market_equity >= $10M filter: {len(df):,}  (dropped {pre_sz - len(df):,})")

    # ------------------------------------------------------------------
    # Section 7: Sort and save
    # ------------------------------------------------------------------
    df = df.sort_values(["permno", "ym"]).reset_index(drop=True)

    output_file = PROCESSED_DATA_DIR / "reit_master_clean.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved: {output_file}")
    print(f"Final shape: {df.shape[0]:,} rows × {df.shape[1]:,} columns")
    print(f"Entities (permno): {df['permno'].nunique():,}")
    print(f"Date range: {df['ym'].min()} → {df['ym'].max()}")
    print(df.describe(include="all").to_string())


if __name__ == "__main__":
    main()
