# Data Dictionary: REIT Analysis Panel

## Dataset Overview
- **Dataset Name:** REIT Analysis Panel (BTJ Team)
- **Primary Source:** CRSP/Compustat REIT Master
- **Supplementary Source:** FRED (Federal Reserve Economic Data)
- **Number of Entities (permno):** 290
- **Number of Time Periods (ym):** 300
- **Total Observations:** 34,960
- **Time Range:** 2000-01 to 2024-12
- **Panel Structure:** Unbalanced (min 1, max 300 periods)

## Variable Definitions
| Variable | Description | Type | Source | Units | Missing % |
|----------|-------------|------|--------|-------|-----------|
| permno | CRSP permanent security identifier | int | CRSP | ID | 0.0% |
| ticker | Stock ticker symbol | str | CRSP | symbol | 0.0% |
| comnam | Company name | str | CRSP | name | 0.0% |
| rtype | REIT type code | float | CRSP | code | 0.0% |
| ptype | Property type code | float | CRSP | code | 0.0% |
| psub | Property sub-type code | float | CRSP | code | 0.0% |
| date | Observation end date | str | CRSP | YYYY-MM-DD | 0.0% |
| caldt | Calendar date | str | CRSP | YYYY-MM-DD | 0.0% |
| ym | Year-month (time variable) | str | CRSP | YYYY-MM | 0.0% |
| usdret | Monthly USD total return | float | CRSP | decimal (0.05 = 5%) | 0.0% |
| usdprc | Monthly closing price (USD) | float | CRSP | USD | 0.0% |
| market_equity | Market capitalization | float | CRSP | millions USD | 0.0% |
| assets | Total assets | float | Compustat | millions USD | 0.3% |
| sales | Total revenues/sales | float | Compustat | millions USD | 0.7% |
| net_income | Net income | float | Compustat | millions USD | 0.6% |
| book_equity | Book equity | float | Compustat | millions USD | 2.5% |
| debt_at | Total debt / total assets | float | Compustat | ratio | 0.3% |
| cash_at | Cash / total assets | float | Compustat | ratio | 0.3% |
| ocf_at | Operating cash flow / total assets | float | Compustat | ratio | 0.6% |
| roe | Return on equity | float | Compustat | ratio | 5.2% |
| btm | Book-to-market ratio | float | Compustat | ratio | 2.5% |
| beta | Market beta | float | CRSP | dimensionless | 6.9% |
| fedfunds | Effective Federal Funds Rate | float | FRED | percent | 0.0% |
| mortgage30us | 30-Year Fixed Mortgage Rate | float | FRED | percent | 0.0% |
| cpiaucsl | Consumer Price Index (1982-84=100) | float | FRED | index | 0.0% |
| unrate | Unemployment Rate | float | FRED | percent | 0.0% |

## Cleaning Decisions Summary
- **Missing usdret:** Dropped (delistings / IPO gaps) — see M1_data_quality_report.md
- **Date filter:** Restricted to 2000-01 onward to align with FRED macro coverage
- **Outliers (usdret):** Winsorized at 1st/99th percentile
- **Size filter:** Dropped observations with market_equity < $10M
- **Duplicates (permno-ym):** Kept first occurrence (none found in this dataset)
- **Macro alignment:** Monthly last-observation; forward-filled any FRED gaps
