[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/gp9US0IQ)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=22634834&assignment_repo_type=AssignmentRepo)
# QM 2023 Capstone Project

Semester-long capstone for Statistics II: Data Analytics.

## Project Structure

- **code/** — Python scripts and notebooks. Use `config_paths.py` for paths.
- **data/raw/** — Original data (read-only)
- **data/processed/** — Intermediate cleaning outputs
- **data/final/** — M1 output: analysis-ready panel
- **results/figures/** — Visualizations
- **results/tables/** — Regression tables, summary stats
- **results/reports/** — Milestone memos
- **tests/** — Autograding test suite

Run `python code/config_paths.py` to verify paths.
## Team Members & Roles

- **Member 1: Josh Love** — Data Engineer
  - Owns data pipeline (fetch_*.py, merge_final_panel.py)
  - Manages data/raw/ → data/processed/ → data/final/ workflow
  - Key deliverable: Analysis-ready panel dataset
  
- **Member 2: Brody Duffel** — Quantitative Analyst
  - Owns exploratory data analysis (M2) and econometric models (M3)
  - Builds visualizations, regression specifications, interprets coefficients
  - Key deliverable: Model code + results interpretation
  
- **Member 3: Tallulah Pascucci** — Technical Writer & Documentation Lead
  - Owns README.md, data quality report, final memo (M4)
  - Translates technical findings for Investment Committee audience
  - Key deliverable: Professional narrative + presentation materials


## Datasets & Data Sources

### Primary Dataset
- **REIT Master Dataset** (Default)
  - Source: CRSP/Ziman Real Estate Database
  - N REITs: 500+
  - Time Period: 120+ months
  - Variables: permno, ym (year-month), ret (returns), mcap, sector, price

### Supplementary Data (TBD — Add your planned sources)
Planned supplementary datasets/indicators (minimum 10-15 series):
- **Federal Reserve Economic Data (FRED)** — Primary drivers of REIT returns:
  - **FEDFUNDS** — Federal Funds Rate (primary monetary policy tool)
  - **MORTGAGE30US** — 30-Year Mortgage Rate (direct impact on property financing costs)
  - **CPIAUCSL** — Consumer Price Index (inflation control variable)
  - **UNRATE** — Unemployment Rate (economic health / demand proxy)
  
- **Additional FRED Series** (economic control variables):
  - **DEXUSEU** — USD/EUR exchange rate (international capital flows)
  - **T10Y2Y** — 10-Year minus 2-Year Treasury Spread (yield curve, recession signal)
  - **HOUST** — Housing Starts (construction activity, real estate demand)
  - **PERMIT** — Building Permits (forward-looking construction indicator)
  - Additional series TBD based on M2 EDA insights
  
- **Derived Variables:**
  - Change in Fed rate (Δ FEDFUNDS)
  - Change in mortgage rate (Δ MORTGAGE30US)
  - Lagged rate variables (1-month, 2-month, 3-month lags)

## Preliminary Research Question

**Primary Research Question:**
How do different REIT sectors (residential, commercial, industrial, healthcare, mortgage, etc.) respond differentially to changes in federal funds rates and mortgage rates? Which sectors are most rate-sensitive, and which are most resilient?

**Investment Context:** The Investment Committee is concerned about REIT return sensitivity following the 2022-2023 Federal Reserve interest rate hikes. This analysis will inform sector-level allocation and risk management decisions.

## Empirical Direction

### Hypotheses (Preliminary)
1. Mortgage REITs exhibit the highest sensitivity to federal funds rate changes (strongest negative relationship).
2. Residential REITs show moderate rate sensitivity; commercial and industrial REITs display lower sensitivity.
3. Healthcare REITs are most resilient to rate shocks due to long-term lease contracts and inflation-protected revenues.
4. Lag effects matter: Rate changes take 1-3 months to fully impact REIT returns across sectors.

### Econometric Approach (Planned)
- **Model A (Primary):** Fixed Effects panel regression with sector interactions
  - Specification: REIT_Return ~ (FEDFUNDS + MORTGAGE30US) × Sector + Economic_Controls + REIT_FE + Time_FE
  - Key coefficient: Sector × Rate interaction (allows each sector's rate sensitivity to vary)
  - Standard errors: Clustered by REIT and time period
  - Interpretation: Differential sector sensitivity to rate changes
  
- **Model B (Alternative):** 
  - Time series ARIMA forecast of sector-level returns
  - OR Random Forest feature importance (which FRED variables matter most by sector?)
  - *(TBD: Choose based on M2 EDA insights)*

### Data Pipeline & Validation
1. Load REIT Master dataset
2. Fetch supplementary data from FRED (via pandas-datareader)
3. Clean: Handle missing values, outliers, duplicates
4. Merge: Align on date/month across all datasets
5. Output: Analysis-ready long-format panel (Entity × Time)
6. Validate: Check row counts, collinearity, data quality

## How to Run the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Verify paths
python code/config_paths.py

# Execute data pipeline
python code/fetch_reit_data.py          # Load primary dataset
python code/fetch_fred_data.py          # Fetch supplementary data
python code/merge_final_panel.py        # Merge into final analysis dataset

# Output
# → data/final/[dataset]_analysis_panel.csv
# → data/final/data_dictionary.md
```

## Project Timeline

- **Weeks 1-4:** Data exploration, pipeline design ✓
- **Week 5:** M1 Due — Data Pipeline (Feb 25)
- **Week 9:** M2 Due — EDA Dashboard (Mar 27)
- **Week 12:** M3 Due — Econometric Models (Apr 17)
- **Week 14:** M4 Due — Final Investment Memo (May 1)
- **Weeks 14-15:** Final Presentation