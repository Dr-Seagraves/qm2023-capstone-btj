"""
Merge Processed Datasets into Analysis-Ready Panel
===================================================

This script merges the cleaned REIT and FRED datasets into a final analysis-ready
panel dataset for econometric modeling. The output is a long-format panel (Entity ×
Time) with:
- REIT-level data: returns, market cap, sector, characteristics
- Time-varying economic variables: interest rates, inflation, unemployment, etc.
- Derived variables for model specifications

Panel Structure:
- Entity: Individual REITs (permno)
- Time: Month (ym, YYYY-MM format)
- Outcome: usdret (monthly REIT return)
- Predictors: FRED economic variables
- Controls: REIT characteristics, sector, lagged returns

Output: reit_fred_analysis_panel.csv (long format, ready for panel regression)

Author: Josh Love (Data Engineer)
Date: February 2026
"""

import pandas as pd
import numpy as np
from config_paths import PROCESSED_DATA_DIR, FINAL_DATA_DIR

# ==============================================================================
# CONFIGURATION
# ==============================================================================

REIT_FILE = PROCESSED_DATA_DIR / 'reit_clean.csv'
FRED_FILE = PROCESSED_DATA_DIR / 'fred_clean.csv'

OUTPUT_FILE = FINAL_DATA_DIR / 'reit_fred_analysis_panel.csv'
METADATA_FILE = FINAL_DATA_DIR / 'data_dictionary.md'

# ==============================================================================
# MERGE DATASETS
# ==============================================================================

def merge_final_panel():
    """Load, merge, and validate analysis-ready panel dataset."""
    
    print("=" * 80)
    print("MERGING REIT & FRED DATA INTO ANALYSIS-READY PANEL")
    print("=" * 80)
    
    # Step 1: Load cleaned datasets
    print(f"\n[1/6] Loading cleaned datasets...")
    
    reit = pd.read_csv(REIT_FILE)
    reit['ym'] = pd.to_datetime(reit['ym'])
    print(f"  ✓ REIT data: {len(reit):,} observations")
    
    fred = pd.read_csv(FRED_FILE)
    fred['ym'] = pd.to_datetime(fred['ym'])
    print(f"  ✓ FRED data: {len(fred):,} observations")
    
    # Step 2: Verify date alignment
    print(f"\n[2/6] Verifying date alignment...")
    reit_dates = reit['ym'].dt.to_period('M').unique()
    fred_dates = fred['ym'].dt.to_period('M').unique()
    
    print(f"  REIT date range: {reit['ym'].min().strftime('%Y-%m')} to {reit['ym'].max().strftime('%Y-%m')} ({len(reit_dates)} months)")
    print(f"  FRED date range: {fred['ym'].min().strftime('%Y-%m')} to {fred['ym'].max().strftime('%Y-%m')} ({len(fred_dates)} months)")
    
    # Step 3: Merge on date (left merge: keep all REIT observations)
    print(f"\n[3/6] Merging REIT × FRED on month...")
    
    # Convert both to period for robust merging
    reit['ym_period'] = reit['ym'].dt.to_period('M')
    fred['ym_period'] = fred['ym'].dt.to_period('M')
    
    # Merge
    merged = pd.merge(
        reit,
        fred,
        on='ym_period',
        how='left'
    )
    
    print(f"  ✓ Merged dataset: {len(merged):,} rows")
    
    # Check for any rows lost in merge
    rows_lost = len(reit) - len(merged)
    if rows_lost > 0:
        print(f"  ⚠️  Warning: {rows_lost:,} REIT rows lost in merge (date mismatch)")
    
    # Drop temporary period column
    merged = merged.drop(columns=['ym_period'])
    
    # Use merged ym_x (from REIT)
    if 'ym_x' in merged.columns and 'ym_y' in merged.columns:
        merged = merged.drop(columns=['ym_y'])
        merged = merged.rename(columns={'ym_x': 'ym'})
    
    # Step 4: Create derived variables for models
    print(f"\n[4/6] Creating derived variables...")
    
    # Lagged returns (for model controls)
    merged = merged.sort_values(['permno', 'ym']).reset_index(drop=True)
    merged['lag_return_1m'] = merged.groupby('permno')['usdret'].shift(1)
    merged['lag_return_3m'] = merged.groupby('permno')['usdret'].shift(3)
    
    print(f"  ✓ Created lagged return variables (1-month, 3-month)")
    
    # Log market cap (size control)
    if 'market_equity' in merged.columns:
        merged['log_market_cap'] = np.log(merged['market_equity'] + 1)
        print(f"  ✓ Created log_market_cap")
    
    # Standardized economic variables (for interpretation)
    economic_vars = ['FEDFUNDS', 'MORTGAGE30US', 'UNRATE', 'CPIAUCSL', 'T10Y2Y']
    for var in economic_vars:
        if var in merged.columns:
            # Standardize (z-score)
            mean = merged[var].mean()
            std = merged[var].std()
            merged[f'{var}_std'] = (merged[var] - mean) / std
    print(f"  ✓ Standardized economic variables")
    
    # Step 5: Quality checks
    print(f"\n[5/6] Performing data quality checks...")
    
    # Check key variables present
    key_vars = ['permno', 'ticker', 'ym', 'Sector', 'usdret', 'FEDFUNDS', 'MORTGAGE30US']
    missing_cols = [col for col in key_vars if col not in merged.columns]
    if missing_cols:
        print(f"  ❌ ERROR: Missing columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    else:
        print(f"  ✓ All key variables present")
    
    # Check return variable
    non_null_ret = merged['usdret'].notna().sum()
    print(f"  ✓ Return data: {non_null_ret:,} non-null observations ({(non_null_ret/len(merged)*100):.1f}%)")
    
    # Check unique entities
    n_reits = merged['permno'].nunique()
    n_months = merged['ym'].nunique()
    print(f"  ✓ Panel structure: {n_reits} REITs × {n_months} months = {n_reits * n_months:,} cell observations")
    print(f"    (Actual: {len(merged):,}, Coverage: {(len(merged)/(n_reits*n_months)*100):.1f}%)")
    
    # Check for sector distribution
    sector_dist = merged['Sector'].value_counts()
    print(f"  ✓ Sector distribution:")
    for sector, count in sector_dist.items():
        pct = (count / len(merged)) * 100
        print(f"    - {sector}: {count:,} ({pct:.1f}%)")
    
    # Step 6: Sort and reorder columns
    print(f"\n[6/6] Finalizing and ordering columns...")
    
    # Define column order for analysis
    id_cols = ['permno', 'ticker', 'comnam', 'ym', 'Sector', 'rtype', 'ptype', 'psub']
    outcome_cols = ['usdret', 'lag_return_1m', 'lag_return_3m']
    reit_chars = ['log_market_cap', 'assets', 'sales', 'net_income', 'roe', 'btm', 'beta']
    econ_cols = ['FEDFUNDS', 'MORTGAGE30US', 'CPIAUCSL', 'UNRATE', 'DEXUSEU', 'T10Y2Y',
                 'HOUST', 'PERMIT', 'FEDFUNDS_CHANGE', 'MORTGAGE30US_CHANGE', 'INFLATION_RATE',
                 'FEDFUNDS_LAG1', 'FEDFUNDS_LAG3', 'MORTGAGE30US_LAG1']
    econ_std_cols = [f'{col}_std' for col in ['FEDFUNDS', 'MORTGAGE30US', 'UNRATE', 'CPIAUCSL', 'T10Y2Y']
                     if f'{col}_std' in merged.columns]
    
    # Select columns (only those in merged)
    ordered_cols = []
    for col_list in [id_cols, outcome_cols, reit_chars, econ_cols, econ_std_cols]:
        for col in col_list:
            if col in merged.columns:
                ordered_cols.append(col)
    
    # Add any remaining columns
    remaining = [col for col in merged.columns if col not in ordered_cols]
    ordered_cols.extend(remaining)
    
    merged_final = merged[ordered_cols].copy()
    
    print(f"  ✓ Selected and ordered {len(merged_final.columns)} columns")
    
    # ==============================================================================
    # SUMMARY STATISTICS
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("FINAL PANEL SUMMARY")
    print("=" * 80)
    
    print(f"\nDataset Dimensions:")
    print(f"  Rows: {len(merged_final):,}")
    print(f"  Columns: {len(merged_final.columns)}")
    print(f"  Unique REITs: {merged_final['permno'].nunique()}")
    print(f"  Unique months: {merged_final['ym'].nunique()}")
    print(f"  Date range: {merged_final['ym'].min().strftime('%Y-%m')} to {merged_final['ym'].max().strftime('%Y-%m')}")
    
    print(f"\nMissing Values (Top 10):")
    missing = merged_final.isnull().sum()
    missing_pct = (missing / len(merged_final)) * 100
    missing_sorted = missing[missing > 0].sort_values(ascending=False)
    for col in missing_sorted.head(10).index:
        print(f"  {col:25s}: {missing[col]:6d} ({missing_pct[col]:5.2f}%)")
    
    print(f"\nReturn Variable Summary:")
    print(f"  Mean return: {merged_final['usdret'].mean():>8.4f} (monthly)")
    print(f"  Std dev:     {merged_final['usdret'].std():>8.4f}")
    print(f"  Min:         {merged_final['usdret'].min():>8.4f}")
    print(f"  Max:         {merged_final['usdret'].max():>8.4f}")
    print(f"  Non-null:    {merged_final['usdret'].notna().sum():,}")
    
    print(f"\nEconomic Variables Summary (standardized):")
    for var in ['FEDFUNDS_std', 'MORTGAGE30US_std', 'UNRATE_std']:
        if var in merged_final.columns:
            print(f"  {var:20s}: mean={merged_final[var].mean():>7.3f}, std={merged_final[var].std():>7.3f}")
    
    # ==============================================================================
    # SAVE OUTPUT
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("SAVING ANALYSIS-READY PANEL")
    print("=" * 80)
    
    FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    merged_final.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✓ Analysis-ready panel saved to: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Format: CSV (long format, Entity × Time)")
    
    # ==============================================================================
    # CREATE DATA DICTIONARY
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("CREATING DATA DICTIONARY")
    print("=" * 80)
    
    data_dict = f"""# Data Dictionary: REIT-FRED Analysis Panel

## Dataset Overview
- **Name**: reit_fred_analysis_panel.csv
- **Rows**: {len(merged_final):,}
- **Columns**: {len(merged_final.columns)}
- **Time Period**: {merged_final['ym'].min().strftime('%Y-%m')} to {merged_final['ym'].max().strftime('%Y-%m')}
- **Entities**: {merged_final['permno'].nunique()} REITs
- **Frequency**: Monthly
- **Structure**: Long format (one row per REIT-month observation)

## Variable Definitions

### Identifiers
| Variable | Description | Type | Source | Unit |
|----------|-------------|------|--------|------|
| permno | CRSP Permanent Security Identifier | Int | CRSP | ID |
| ticker | Stock ticker symbol | Str | CRSP | Code |
| comnam | Company name | Str | CRSP | Text |
| ym | Year-Month (observation date) | DateTime | REIT | YYYY-MM |
| Sector | REIT economic sector | Str | Derived | Category |
| rtype | REIT type code | Float | CRSP | Code |
| ptype | Property type code | Float | CRSP | Code |
| psub | Property sub-type | Float | CRSP | Code |

### Outcome Variable
| Variable | Description | Type | Source | Unit |
|----------|-------------|------|--------|------|
| usdret | Monthly USD return | Float | CRSP | Decimal (0.05 = 5%) |

### Lagged Outcomes (Model Controls)
| Variable | Description | Type | Source | Unit |
|----------|-------------|------|--------|------|
| lag_return_1m | 1-month lagged return | Float | Derived | Decimal |
| lag_return_3m | 3-month lagged return | Float | Derived | Decimal |

### REIT Characteristics
| Variable | Description | Type | Source | Unit |
|----------|-------------|------|--------|------|
| log_market_cap | Log of market equity | Float | Derived | Log $ |
| assets | Total assets | Float | CRSP | $ Millions |
| sales | Sales/Revenue | Float | CRSP | $ Millions |
| net_income | Net income | Float | CRSP | $ Millions |
| book_equity | Book value of equity | Float | CRSP | $ Millions |
| debt_at | Total debt | Float | CRSP | $ Millions |
| cash_at | Cash and equivalents | Float | CRSP | $ Millions |
| roe | Return on equity | Float | CRSP | Decimal |
| btm | Book-to-market ratio | Float | CRSP | Decimal |
| beta | Market beta (systematic risk) | Float | CRSP | Coefficient |

### Federal Reserve Economic Data (FRED)
| Variable | Description | Type | Source | Unit |
|----------|-------------|------|--------|------|
| FEDFUNDS | Federal Funds Rate | Float | FRED | Percent (%) |
| MORTGAGE30US | 30-Year Mortgage Rate | Float | FRED | Percent (%) |
| CPIAUCSL | Consumer Price Index (All Urban) | Float | FRED | Index (1982-84=100) |
| UNRATE | Unemployment Rate | Float | FRED | Percent (%) |
| DEXUSEU | USD/EUR Exchange Rate | Float | FRED | Ratio |
| T10Y2Y | 10-Year minus 2-Year Treasury Spread | Float | FRED | Percent (%) |
| HOUST | Housing Starts | Float | FRED | Thousands (annualized) |
| PERMIT | Building Permits | Float | FRED | Thousands (annualized) |

### Derived Economic Variables
| Variable | Description | Type | Source | Unit |
|----------|-------------|------|--------|------|
| FEDFUNDS_CHANGE | Month-over-month change in Fed rate | Float | Derived | Percentage points |
| MORTGAGE30US_CHANGE | Month-over-month change in mortgage rate | Float | Derived | Percentage points |
| INFLATION_RATE | Month-over-month CPI % change | Float | Derived | Annualized percent (%) |
| FEDFUNDS_LAG1 | Federal Funds Rate (t-1) | Float | Derived | Percent (%) |
| FEDFUNDS_LAG3 | Federal Funds Rate (t-3) | Float | Derived | Percent (%) |
| MORTGAGE30US_LAG1 | 30-Year Mortgage Rate (t-1) | Float | Derived | Percent (%) |

### Standardized Variables (For Interpretation)
Variables with `_std` suffix are z-score standardized (mean=0, std=1) for easier interpretation of regression coefficients.

| Variable | Description |
|----------|-------------|
| FEDFUNDS_std | Standardized Federal Funds Rate |
| MORTGAGE30US_std | Standardized Mortgage Rate |
| UNRATE_std | Standardized Unemployment Rate |
| CPIAUCSL_std | Standardized CPI |
| T10Y2Y_std | Standardized Yield Curve |

## Data Quality Notes

### Missing Values
- **usdret**: {merged_final['usdret'].isna().sum():,} missing ({(merged_final['usdret'].isna().sum()/len(merged_final)*100):.2f}%)
- **REIT characteristics** (book_equity, beta, etc.): 0-15% missing (see data dictionary above)
- **Derived variables** (FEDFUNDS_CHANGE, lag variables): <1% missing (first few months)

### Coverage
- **Panel balance**: {(len(merged_final)/(merged_final['permno'].nunique()*merged_final['ym'].nunique())*100):.1f}% (unbalanced panel)
- **Time coverage**: All observations cover 1986-2024 monthly period
- **Entity coverage**: {merged_final['permno'].nunique()} unique REITs

### Sector Distribution
{merged_final['Sector'].value_counts().to_string()}

## Recommended Transformations

### For Econometric Models
- **Returns**: Use as-is (already in decimal form)
- **Economic rates**: Consider difference transformations (Δ rates) to remove unit roots
- **Market cap**: Use log transformation (already provided as log_market_cap)
- **Standardized variables**: Use for Model B (easier interpretation)

### Handling Missing Values
- Drop rows with missing **usdret** (outcome variable)
- For REIT characteristics: Use within-entity mean imputation or drop with caution
- Lagged returns: Naturally missing for first few observations (acceptable in fixed effects models)

## Usage Example (Python/pandas)

```python
import pandas as pd

# Load panel
df = pd.read_csv('reit_fred_analysis_panel.csv')
df['ym'] = pd.to_datetime(df['ym'])

# Drop missing returns
df_analysis = df.dropna(subset=['usdret'])

# Panel regression (e.g., using linearmodels)
from linearmodels.panel import FirstDifferenceOLS
df_analysis = df_analysis.set_index(['permno', 'ym'])

model = FirstDifferenceOLS(
    df_analysis['usdret'],
    df_analysis[['FEDFUNDS', 'MORTGAGE30US', 'UNRATE']]
)
result = model.fit()
```

## References

- **CRSP/Ziman REIT Database**: https://www.crsp.org/
- **FRED Economic Data**: https://fred.stlouisfed.org/
- **Panel Data Methods**: Wooldridge (2010), Econometric Analysis of Cross Section and Panel Data

---
Generated: February 2026
Authors: Josh Love (Data Engineer), Brody Duffel (Analyst), Tallulah Pascucci (Writer)
"""
    
    with open(METADATA_FILE, 'w') as f:
        f.write(data_dict)
    
    print(f"\n✓ Data dictionary saved to: {METADATA_FILE}")
    
    # ==============================================================================
    # SUMMARY
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("M1 DATA PIPELINE COMPLETE")
    print("=" * 80)
    
    print(f"\nDeliverables:")
    print(f"  ✓ {OUTPUT_FILE.name}: Analysis-ready panel ({len(merged_final):,} rows × {len(merged_final.columns)} cols)")
    print(f"  ✓ {METADATA_FILE.name}: Complete data dictionary")
    print(f"\nNext Steps:")
    print(f"  1. Create M1_data_quality_report.md (data cleaning decisions, before/after)")
    print(f"  2. Create AI_AUDIT_APPENDIX.md (AI usage documentation)")
    print(f"  3. Commit to GitHub: data/, M1_data_quality_report.md, AI_AUDIT_APPENDIX.md")
    print(f"  4. Submit GitHub URL to Blackboard by Feb 25, 11:59 PM")
    
    print(f"\n" + "=" * 80)
    
    return merged_final


if __name__ == "__main__":
    """Execute merge pipeline."""
    panel = merge_final_panel()
    print("\n✓ Panel merge and validation complete!")
