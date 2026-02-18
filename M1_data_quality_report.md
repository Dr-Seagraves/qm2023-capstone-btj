# Milestone 1 Data Quality Report

## 1) Data Sources

### Primary Dataset
- **Name:** REIT Sample 2000–2024 (All Variables)
- **File:** `data/raw/reit_master_raw.csv`
- **Source:** CRSP / Compustat (instructor-provided)
- **Initial rows:** 48,019 | **Entities (permno):** 369
- **Raw date range:** 1986-12 → 2024-12 (monthly)
- **Key variables:** `permno`, `ym`, `usdret`, `usdprc`, `market_equity`, `assets`, `sales`, `net_income`, `book_equity`, `debt_at`, `cash_at`, `ocf_at`, `roe`, `btm`, `beta`

### Supplementary Dataset
- **Source:** FRED (Federal Reserve Economic Data) — public CSV download
- **Series:** `FEDFUNDS`, `MORTGAGE30US`, `CPIAUCSL`, `UNRATE`
- **Coverage:** Monthly, 2000-01 → 2024-12 | **Rows:** 300
- **Files:** `data/raw/FEDFUNDS.csv`, `MORTGAGE30US.csv`, `CPIAUCSL.csv`, `UNRATE.csv`

## 2) Data Cleaning Decisions

| Dataset | Variable | Missing / Count | Decision | Justification |
|---------|----------|----------------:|----------|---------------|
| REIT | `usdret` | 324 (0.7%) | **Drop** | Delistings and IPO gaps; no reasonable imputation for returns |
| REIT | Pre-2000 rows | 12,899 rows | **Drop (date filter)** | FRED macro starts 2000-01; aligning panels avoids macro NaNs |
| REIT | `usdret` outliers | 700 values outside [1st/99th pctl] | **Winsorize** at [-0.2454, 0.2770] | Standard for financial returns; extreme values likely data errors or corporate actions |
| REIT | `market_equity < $10M` | 0 observations | No impact | All remaining REITs exceed threshold |
| REIT | Duplicate `permno-ym` | 0 | N/A | No duplicates found |
| Macro | Sub-monthly `MORTGAGE30US` | Weekly series | **Last-of-month** collapse + ffill | Align to monthly REIT panel |

## 3) Merge Strategy
- **Join type:** Left join (REIT panel drives row count)
- **Merge key:** `ym` (YYYY-MM, normalised on both tables)
- **Supplementary:** De-duplicated to one row per month before merge
- **Primary rows before merge:** 34,960
- **Rows after merge:** 34,960 ✓
- **Duplicate `permno-ym` after merge:** 0 ✓
- **Macro NaNs after merge:** 0 for all four series ✓

## 4) Final Dataset Summary
- **Entity variable:** `permno` | **Time variable:** `ym`
- **Panel type:** Unbalanced
- **Final dimensions:** 34,960 rows × 26 columns
- **Entities:** 290 REITs | **Time periods:** 300 months (2000-01 → 2024-12)

| Variable | Mean | Std Dev | Min | Max | Missing % |
|---|---:|---:|---:|---:|---:|
| usdret | 0.0103 | 0.0805 | -0.2454 | 0.2770 | 0.0% |
| market_equity | 4,683 M | 10,263 M | 10.0 M | 133,209 M | 0.0% |
| fedfunds | 1.89% | 2.00% | 0.05% | 6.54% | 0.0% |
| mortgage30us | 5.05% | 1.42% | 2.67% | 8.62% | 0.0% |
| cpiaucsl | 233.2 | 38.2 | 169.3 | 317.6 | 0.0% |
| unrate | 5.53% | 1.90% | 3.40% | 14.80% | 0.0% |

## 5) Reproducibility Checklist
- [x] All scripts run without manual edits
- [x] Relative paths only via `config_paths.py`
- [x] Outputs in `data/processed/` and `data/final/`
- [x] No Excel/manual editing
- [x] `data/final/data_dictionary.md` auto-generated
- [ ] `AI_AUDIT_APPENDIX.md` — complete before submission

## 6) Ethical Considerations
- **Pre-2000 exclusion:** 12,899 rows (79 entities) dropped to align with FRED start. These are older REITs with sparse data; focusing on 2000+ is appropriate for modern institutional analysis.
- **Market cap filter:** Screen retained as standard institutional filter. No observations dropped; micro-caps were already absent from this sample.
- **Winsorization:** Extreme monthly returns clipped at 1st/99th percentile. Suppresses real tail events (COVID crash, GFC). Robustness checks with raw returns planned for M3.

## Team Sign-off
- [Name 1]
- [Name 2]
- [Name 3]
- [Name 4]
