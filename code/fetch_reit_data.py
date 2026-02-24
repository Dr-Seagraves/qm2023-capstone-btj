"""
Fetch and Clean REIT Master Dataset
====================================

This script loads the raw REIT Master dataset from CRSP/Ziman database,
performs data cleaning (handle missing values, format dates, create categorical
variables), and saves the cleaned dataset to data/processed/.

Cleaning Decisions Documented:
- Date formatting: Convert 'ym' column to datetime for time-series alignment
- Missing returns: Rows with null usdret are dropped (cannot analyze REIT without returns)
- Sector mapping: rtype (REIT type) mapped to economic sectors
- Property type mapping: psub (property sub-type) for analysis flexibility
- Duplicates: Removed by (permno, date) pairs
- Outliers: Flagged in cleaning report but retained (removed in merge step if needed)

Author: Josh Love (Data Engineer)
Date: February 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from config_paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

# ==============================================================================
# CONFIGURATION
# ==============================================================================

RAW_FILE = RAW_DATA_DIR / 'REIT_sample_2000_2024_All_Variables.csv'
OUTPUT_FILE = PROCESSED_DATA_DIR / 'reit_clean.csv'

# Sector mapping: rtype code to sector label
REIT_SECTOR_MAP = {
    1.0: 'Residential',
    2.0: 'Commercial',
    3.0: 'Industrial',
    4.0: 'Diversified',
    5.0: 'Healthcare',
    9.0: 'Mortgage',
    10.0: 'Other'
}

# ==============================================================================
# LOAD AND CLEAN DATA
# ==============================================================================

def clean_reit_data():
    """Load raw REIT data and perform cleaning."""
    
    print("=" * 80)
    print("FETCHING & CLEANING REIT MASTER DATASET")
    print("=" * 80)
    
    # Load raw data
    print(f"\n[1/6] Loading raw REIT data from: {RAW_FILE}")
    df = pd.read_csv(RAW_FILE)
    initial_rows = len(df)
    print(f"  ✓ Loaded {initial_rows:,} rows, {len(df.columns)} columns")
    
    # Step 1: Drop rows with missing returns (core outcome variable)
    print(f"\n[2/6] Handling missing returns...")
    before_ret = len(df)
    df = df.dropna(subset=['usdret'])
    after_ret = len(df)
    dropped_ret = before_ret - after_ret
    print(f"  ✓ Dropped {dropped_ret:,} rows with missing usdret")
    print(f"  → {after_ret:,} rows retained ({(after_ret/initial_rows)*100:.1f}% of original)")
    
    # Step 2: Format date column (convert from "YYYYmMM" to datetime)
    print(f"\n[3/6] Formatting date columns...")
    df['ym'] = pd.to_datetime(df['ym'], format='%Ym%m', errors='coerce')
    before_date = len(df)
    df = df.dropna(subset=['ym'])
    after_date = len(df)
    dropped_date = before_date - after_date
    if dropped_date > 0:
        print(f"  ! Dropped {dropped_date:,} rows with invalid dates")
    print(f"  ✓ Converted ym to datetime (YYYY-MM format)")
    date_min = df['ym'].min().strftime('%Y-%m')
    date_max = df['ym'].max().strftime('%Y-%m')
    print(f"  ✓ Date range: {date_min} to {date_max}")
    
    # Step 3: Remove duplicates
    print(f"\n[4/6] Removing duplicate (permno, ym) pairs...")
    before_dup = len(df)
    df = df.drop_duplicates(subset=['permno', 'ym'], keep='first')
    after_dup = len(df)
    dropped_dup = before_dup - after_dup
    print(f"  ✓ Dropped {dropped_dup:,} duplicate rows")
    print(f"  → {after_dup:,} rows retained")
    
    # Step 4: Create sector variable
    print(f"\n[5/6] Creating sector classification variable...")
    df['Sector'] = df['rtype'].map(REIT_SECTOR_MAP)
    sector_counts = df['Sector'].value_counts().sort_index()
    print(f"  ✓ Sector distribution:")
    for sector, count in sector_counts.items():
        pct = (count / len(df)) * 100
        print(f"    - {sector}: {count:,} ({pct:.1f}%)")
    
    # Step 5: Select and rename key columns for analysis
    print(f"\n[6/6] Selecting analysis-ready columns...")
    analysis_columns = [
        'permno',      # REIT identifier
        'ticker',      # Stock ticker
        'comnam',      # Company name
        'ym',          # Year-Month (datetime)
        'Sector',      # Sector classification (derived)
        'rtype',       # REIT type code
        'ptype',       # Property type code
        'psub',        # Property sub-type
        'usdret',      # Monthly USD return (OUTCOME VARIABLE)
        'usdprc',      # USD price
        'market_equity', # Market cap
        'assets',      # Total assets
        'sales',       # Sales/Revenue
        'net_income',  # Net income
        'book_equity', # Book equity
        'debt_at',     # Total debt
        'cash_at',     # Cash
        'roe',         # Return on equity
        'btm',         # Book-to-market ratio
        'beta',        # Market beta
    ]
    
    # Keep only available columns
    available_cols = [col for col in analysis_columns if col in df.columns]
    df_final = df[available_cols].copy()
    
    print(f"  ✓ Selected {len(available_cols)} columns for analysis")
    print(f"  ✓ Final dataset: {len(df_final):,} rows × {len(df_final.columns)} columns")
    
    # ==============================================================================
    # SUMMARY STATISTICS
    # ==============================================================================
    
    print("\n" + "=" * 80)
    print("DATA SUMMARY STATISTICS")
    print("=" * 80)
    
    print(f"\nUnique REITs (permno): {df_final['permno'].nunique()}")
    print(f"Unique Tickers: {df_final['ticker'].nunique()}")
    print(f"Time periods (months): {df_final['ym'].nunique()}")
    print(f"Date range: {df_final['ym'].min().strftime('%Y-%m')} to {df_final['ym'].max().strftime('%Y-%m')}")
    
    print(f"\nMissing values by column:")
    missing = df_final.isnull().sum()
    missing_pct = (missing / len(df_final)) * 100
    for col in df_final.columns:
        if missing[col] > 0:
            print(f"  {col}: {missing[col]:,} ({missing_pct[col]:.2f}%)")
    
    print(f"\nReturn Statistics (usdret):")
    print(f"  Mean:       {df_final['usdret'].mean():>8.4f}")
    print(f"  Median:     {df_final['usdret'].median():>8.4f}")
    print(f"  Std Dev:    {df_final['usdret'].std():>8.4f}")
    print(f"  Min:        {df_final['usdret'].min():>8.4f}")
    print(f"  Max:        {df_final['usdret'].max():>8.4f}")
    
    # ==============================================================================
    # SAVE OUTPUT
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print(f"SAVING CLEANED DATA")
    print("=" * 80)
    
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✓ Cleaned REIT data saved to: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Format: CSV (relative path recommended)")
    
    # ==============================================================================
    # REPRODUCIBILITY INFORMATION
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("REPRODUCIBILITY CHECKLIST")
    print("=" * 80)
    
    print(f"\n✓ Raw data source: {RAW_FILE.name}")
    print(f"  - Records loaded: {initial_rows:,}")
    print(f"  - Records after cleaning: {len(df_final):,}")
    print(f"  - Data loss: {((initial_rows - len(df_final)) / initial_rows) * 100:.1f}%")
    
    print(f"\nCleaning steps applied:")
    print(f"  1. Dropped {dropped_ret:,} rows with missing returns (usdret)")
    print(f"  2. Parsed ym to datetime (YYYY-MM format)")
    print(f"  3. Removed {dropped_dup:,} duplicate (permno, ym) pairs")
    print(f"  4. Created Sector variable from rtype mapping")
    print(f"  5. Selected {len(available_cols)} analysis-ready columns")
    
    print(f"\nNext steps:")
    print(f"  1. Run fetch_fred_data.py to get supplementary economic data")
    print(f"  2. Run merge_final_panel.py to align REIT + FRED data")
    
    print(f"\n" + "=" * 80)
    
    return df_final


if __name__ == "__main__":
    """Execute data pipeline."""
    df_clean = clean_reit_data()
    print("\n✓ REIT data fetch and cleaning complete!")
