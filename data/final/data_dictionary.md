# Data Dictionary: REIT-FRED Analysis Panel

## Dataset Overview
- **Name**: reit_fred_analysis_panel.csv
- **Rows**: 47,695
- **Columns**: 42
- **Time Period**: 1986-12 to 2024-12
- **Entities**: 367 REITs
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
- **usdret**: 0 missing (0.00%)
- **REIT characteristics** (book_equity, beta, etc.): 0-15% missing (see data dictionary above)
- **Derived variables** (FEDFUNDS_CHANGE, lag variables): <1% missing (first few months)

### Coverage
- **Panel balance**: 28.4% (unbalanced panel)
- **Time coverage**: All observations cover 1986-2024 monthly period
- **Entity coverage**: 367 unique REITs

### Sector Distribution
Sector
Commercial    47695

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
