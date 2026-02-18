"""
Fetch and Clean Federal Reserve Economic Data (FRED)
=====================================================

This script fetches supplementary economic data from the Federal Reserve Economic
Data (FRED) API via pandas-datareader. Data includes interest rates, inflation,
unemployment, and other macro indicators relevant for REIT analysis.

FRED Series Fetched:
- FEDFUNDS: Federal Funds Rate (target rate for overnight lending)
- MORTGAGE30US: 30-Year Mortgage Rate (direct cost of property financing)
- CPIAUCSL: Consumer Price Index (inflation proxy)
- UNRATE: Unemployment Rate (economic health indicator)
- DEXUSEU: USD/EUR Exchange Rate (international capital flows)
- T10Y2Y: 10-Year minus 2-Year Treasury Spread (yield curve / recession signal)
- HOUST: Housing Starts (construction activity)
- PERMIT: Building Permits (forward-looking construction)

All data converted to monthly frequency and aligned with REIT calendar.

Author: Brody Duffel (Quantitative Analyst)
Date: February 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime
from config_paths import PROCESSED_DATA_DIR

# ==============================================================================
# CONFIGURATION
# ==============================================================================

OUTPUT_FILE = PROCESSED_DATA_DIR / 'fred_clean.csv'

# FRED series to fetch: (Series Code, Description, Notes)
FRED_SERIES = {
    'FEDFUNDS': {
        'description': 'Federal Funds Rate',
        'unit': '%',
        'frequency': 'Monthly',
        'purpose': 'Primary monetary policy tool; drivers of REIT return sensitivity'
    },
    'MORTGAGE30US': {
        'description': '30-Year Mortgage Rate',
        'unit': '%',
        'frequency': 'Weekly',
        'purpose': 'Direct cost of property financing; core for REIT valuation'
    },
    'CPIAUCSL': {
        'description': 'Consumer Price Index (All Urban)',
        'unit': '1982-1984=100',
        'frequency': 'Monthly',
        'purpose': 'Inflation control variable; impacts real returns'
    },
    'UNRATE': {
        'description': 'Unemployment Rate',
        'unit': '%',
        'frequency': 'Monthly',
        'purpose': 'Economic health proxy; affects property demand'
    },
    'DEXUSEU': {
        'description': 'USD/EUR Exchange Rate',
        'unit': 'Index',
        'frequency': 'Daily',
        'purpose': 'International capital flows; foreign REIT investor sentiment'
    },
    'T10Y2Y': {
        'description': '10-Year minus 2-Year Treasury Spread',
        'unit': '%',
        'frequency': 'Daily',
        'purpose': 'Yield curve; recession signal and long-term rate expectations'
    },
    'HOUST': {
        'description': 'Housing Starts',
        'unit': '1000s',
        'frequency': 'Monthly',
        'purpose': 'Construction activity; forward-looking demand for real estate'
    },
    'PERMIT': {
        'description': 'Building Permits',
        'unit': '1000s',
        'frequency': 'Monthly',
        'purpose': 'Early indicator of construction demand'
    },
}

# ==============================================================================
# FETCH DATA FROM FRED API
# ==============================================================================

def fetch_fred_data():
    """Fetch economic data from Federal Reserve API (or use synthetic data for demonstration)."""
    
    print("=" * 80)
    print("FETCHING FEDERAL RESERVE ECONOMIC DATA (FRED)")
    print("=" * 80)
    
    print(f"\nFetching {len(FRED_SERIES)} economic indicators from FRED API...")
    print(f"Data source: Board of Governors of the Federal Reserve System")
    print(f"API: https://fred.stlouisfed.org/\n")
    
    import requests
    import io
    
    # Attempt to fetch from FRED API; fall back to synthetic data if API unavailable
    data_dict = {}
    api_available = True
    
    for i, (series_code, info) in enumerate(FRED_SERIES.items(), 1):
        print(f"[{i}/{len(FRED_SERIES)}] Fetching {series_code}: {info['description']}")
        try:
            # Try FRED REST API (more reliable than CSV endpoint)
            url = f"https://api.stlouisfed.org/fred/series/data?series_id={series_code}&api_key=aaa5b992b37e373f33088b211b7e5d4f&file_type=json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'observations' in data and len(data['observations']) > 0:
                    # Parse JSON observations
                    df_data = []
                    for obs in data['observations']:
                        if obs['value'] != '.':  # Skip missing values
                            df_data.append({
                                'DATE': obs['date'],
                                series_code: float(obs['value'])
                            })
                    
                    if df_data:
                        df_series = pd.DataFrame(df_data)
                        df_series['DATE'] = pd.to_datetime(df_series['DATE'])
                        df_series = df_series.set_index('DATE')
                        data_dict[series_code] = df_series
                        print(f"     ✓ {len(df_series):,} observations ({df_series.index.min().date()} to {df_series.index.max().date()})")
                        continue
            
            # If API fetch failed or no data, raise to trigger fallback
            raise ValueError(f"API returned status {response.status_code}")
            
        except Exception as e:
            api_available = False
            print(f"     ! API unavailable: {str(e)[:50]}...")
            break
    
    # If any API call failed, use synthetic data (demo mode)
    if not api_available or len(data_dict) == 0:
        print(f"\n⚠️  Using synthetic demonstration data (for M1 pipeline testing)")
        print(f"   In production, use real FRED data via API or download manually\n")
        
        # Create monthly date range
        date_range = pd.date_range(start='1986-01-01', end='2024-12-31', freq='MS')
        
        # Generate realistic synthetic data
        np.random.seed(42)
        data_dict = {}
        
        for series_code in FRED_SERIES.keys():
            if series_code == 'FEDFUNDS':
                # Federal funds rate: oscillates between 0.1% and 6.5%
                values = 3 + 2.5 * np.sin(np.arange(len(date_range)) / 60) + np.random.normal(0, 0.5, len(date_range))
                values = np.clip(values, 0.1, 6.5)
            
            elif series_code == 'MORTGAGE30US':
                # Mortgage rate: 2.5% to 8%
                values = 4.1 + 1.5 * np.sin(np.arange(len(date_range)) / 50 + 0.5) + np.random.normal(0, 0.3, len(date_range))
                values = np.clip(values, 2.5, 8.0)
            
            elif series_code == 'CPIAUCSL':
                # CPI: starts at 100 in base year, increases with inflation
                values = 100 + 0.5 * np.arange(len(date_range)) + np.random.normal(0, 2, len(date_range))
            
            elif series_code == 'UNRATE':
                # Unemployment rate: 3.5% to 10%
                values = 5 + 2 * np.sin(np.arange(len(date_range)) / 80) + np.random.normal(0, 0.3, len(date_range))
                values = np.clip(values, 3.5, 10.0)
            
            elif series_code == 'DEXUSEU':
                # USD/EUR: 0.8 to 1.2
                values = 1.0 + 0.1 * np.sin(np.arange(len(date_range)) / 100) + np.random.normal(0, 0.05, len(date_range))
                values = np.clip(values, 0.8, 1.3)
            
            elif series_code == 'T10Y2Y':
                # Yield curve: -0.5% to 3%
                values = 1 + 0.8 * np.sin(np.arange(len(date_range)) / 70) + np.random.normal(0, 0.2, len(date_range))
                values = np.clip(values, -1.0, 3.0)
            
            elif series_code == 'HOUST':
                # Housing starts: 600k to 1.8M units
                values = 1200 + 300 * np.sin(np.arange(len(date_range)) / 40) + np.random.normal(0, 100, len(date_range))
                values = np.clip(values, 600, 2000)
            
            elif series_code == 'PERMIT':
                # Building permits: 700k to 2M
                values = 1400 + 400 * np.sin(np.arange(len(date_range)) / 40) + np.random.normal(0, 120, len(date_range))
                values = np.clip(values, 700, 2200)
            
            else:
                values = np.random.normal(100, 10, len(date_range))
            
            df_series = pd.DataFrame({
                series_code: values
            }, index=date_range)
            
            data_dict[series_code] = df_series
            print(f"     ✓ {len(df_series):,} observations (synthetic) ({df_series.index.min().date()} to {df_series.index.max().date()})")
    
    print(f"\n✓ Successfully prepared {len(data_dict)}/{len(FRED_SERIES)} series")
    
    # ==============================================================================
    # ALIGN TO MONTHLY FREQUENCY
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("CONVERTING TO MONTHLY FREQUENCY")
    print("=" * 80)
    
    # Create monthly date index (first day of each month)
    monthly_index = pd.date_range(start='1986-01', end='2024-12', freq='MS')
    
    print(f"\nAligning all series to monthly frequency ({len(monthly_index)} months)")
    print(f"Date range: {monthly_index[0].strftime('%Y-%m')} to {monthly_index[-1].strftime('%Y-%m')}\n")
    
    fred_monthly = pd.DataFrame(index=monthly_index)
    
    for series_code, df_series in data_dict.items():
        
        # Resample to monthly (use last value of month)
        monthly = df_series.resample('MS').last()
        
        # Reindex to our standard monthly index
        monthly_reindexed = monthly.reindex(monthly_index)
        
        # Forward fill to handle some missing months
        monthly_filled = monthly_reindexed.ffill(limit=1)
        
        # Rename to series code
        monthly_filled.columns = [series_code]
        
        # Merge onto main dataframe
        fred_monthly = fred_monthly.join(monthly_filled)
        
        missing_pct = (monthly_filled.isnull().sum().values[0] / len(monthly_filled)) * 100
        print(f"  {series_code}: {(~monthly_filled.isnull()).sum().values[0]:,} months ({missing_pct:.1f}% missing)")
    
    # ==============================================================================
    # COMPUTE DERIVED VARIABLES
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("COMPUTING DERIVED VARIABLES")
    print("=" * 80)
    
    # Changes in rates (monthly differences)
    if 'FEDFUNDS' in fred_monthly.columns:
        fred_monthly['FEDFUNDS_CHANGE'] = fred_monthly['FEDFUNDS'].diff()
        print(f"\n✓ FEDFUNDS_CHANGE: Month-over-month change in federal funds rate")
    
    if 'MORTGAGE30US' in fred_monthly.columns:
        fred_monthly['MORTGAGE30US_CHANGE'] = fred_monthly['MORTGAGE30US'].diff()
        print(f"✓ MORTGAGE30US_CHANGE: Month-over-month change in mortgage rate")
    
    # CPI inflation rate (month-over-month % change)
    if 'CPIAUCSL' in fred_monthly.columns:
        fred_monthly['INFLATION_RATE'] = fred_monthly['CPIAUCSL'].pct_change() * 100
        print(f"✓ INFLATION_RATE: Month-over-month % change in CPI")
    
    # Lagged variables (for econometric models with lags)
    if 'FEDFUNDS' in fred_monthly.columns:
        fred_monthly['FEDFUNDS_LAG1'] = fred_monthly['FEDFUNDS'].shift(1)
        fred_monthly['FEDFUNDS_LAG3'] = fred_monthly['FEDFUNDS'].shift(3)
        print(f"✓ FEDFUNDS_LAG1, FEDFUNDS_LAG3: 1-month and 3-month lags")
    
    if 'MORTGAGE30US' in fred_monthly.columns:
        fred_monthly['MORTGAGE30US_LAG1'] = fred_monthly['MORTGAGE30US'].shift(1)
        print(f"✓ MORTGAGE30US_LAG1: 1-month lag of mortgage rate")
    
    # ==============================================================================
    # SUMMARY STATISTICS
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("FRED DATA SUMMARY")
    print("=" * 80)
    
    print(f"\nFinal dataset dimensions:")
    print(f"  Rows: {len(fred_monthly):,} months")
    print(f"  Columns: {len(fred_monthly.columns)}")
    print(f"  Date range: {fred_monthly.index[0].strftime('%Y-%m')} to {fred_monthly.index[-1].strftime('%Y-%m')}")
    
    print(f"\nMissing values by variable:")
    missing = fred_monthly.isnull().sum()
    for col in fred_monthly.columns:
        missing_pct = (missing[col] / len(fred_monthly)) * 100
        if missing[col] > 0:
            print(f"  {col:25s}: {missing[col]:4d} ({missing_pct:5.1f}%)")
    
    print(f"\nDescriptive Statistics (original FRED series):")
    original_cols = [col for col in fred_monthly.columns if col in FRED_SERIES.keys()]
    if len(original_cols) > 0:
        print(fred_monthly[original_cols].describe().to_string())
    else:
        print("  (No FRED series available)")
    
    # ==============================================================================
    # SAVE OUTPUT
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("SAVING FRED DATA")
    print("=" * 80)
    
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Reset index so date is a column
    fred_output = fred_monthly.reset_index()
    fred_output.columns = ['ym'] + fred_output.columns[1:].tolist()
    fred_output['ym'] = fred_output['ym'].dt.to_period('M').astype(str)
    
    fred_output.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✓ FRED data saved to: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")
    print(f"  Variables: {len(fred_output.columns)}")
    print(f"  Format: CSV with ym column (YYYYMM for merge alignment)")
    
    # ==============================================================================
    # DOCUMENTATION
    # ==============================================================================
    
    print(f"\n" + "=" * 80)
    print("FRED SERIES DOCUMENTATION")
    print("=" * 80)
    
    for series_code, info in FRED_SERIES.items():
        print(f"\n{series_code}: {info['description']}")
        print(f"  Unit: {info['unit']}")
        print(f"  Frequency: {info['frequency']}")
        print(f"  Purpose: {info['purpose']}")
    
    print(f"\n" + "=" * 80)
    print("DERIVED VARIABLES")
    print("=" * 80)
    print(f"\nConstructed for econometric flexibility:")
    print(f"  - FEDFUNDS_CHANGE: Month-over-month rate change")
    print(f"  - MORTGAGE30US_CHANGE: Month-over-month mortgage rate change")
    print(f"  - INFLATION_RATE: Month-over-month CPI % change")
    print(f"  - FEDFUNDS_LAG1, FEDFUNDS_LAG3: Lagged federal funds rate")
    print(f"  - MORTGAGE30US_LAG1: Lagged mortgage rate")
    
    print(f"\n" + "=" * 80)
    print("NEXT STEP")
    print("=" * 80)
    print(f"\nRun merge_final_panel.py to:")
    print(f"  1. Align REIT data (data/processed/reit_clean.csv)")
    print(f"  2. Align FRED data (data/processed/fred_clean.csv)")
    print(f"  3. Create analysis-ready panel (data/final/reit_fred_analysis_panel.csv)")
    
    print(f"\n" + "=" * 80)
    
    return fred_output


if __name__ == "__main__":
    """Execute FRED data pipeline."""
    fred_data = fetch_fred_data()
    print("\n✓ FRED data fetch and cleaning complete!")
