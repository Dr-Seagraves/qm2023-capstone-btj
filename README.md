# QM 2023 Capstone Project: [Team Name]

## Team Members
- [Josh Love] - [Role]
- [Brody Duffel] - [Role]
- [Tallulah Pacucci] - [Role]

## Research Question
[Write a 1-2 sentence research question here.]

## Dataset Overview
- **Primary Dataset:** REIT Master (instructor-provided)
  - Entities: REITs (`permno`) | Time: Monthly (`ym`) | Outcome: `ret`
- **Supplementary Dataset:** FRED macro series
  - `FEDFUNDS`, `MORTGAGE30US`, `CPIAUCSL`, `UNRATE`

## Preliminary Hypotheses
1. [Hypothesis 1]
2. [Hypothesis 2]
3. [Hypothesis 3]

## Repository Structure
```
qm2023-capstone-btj/
├── code/
│   ├── config_paths.py
│   ├── fetch_reit_data.py
│   ├── fetch_macro_data.py
│   └── merge_final_panel.py
├── data/
│   ├── raw/
│   │   ├── reit_master_raw.csv
│   │   └── fred_macro_raw.csv (optional fallback)
│   ├── processed/
│   │   ├── reit_master_clean.csv
│   │   └── fred_macro_clean.csv
│   └── final/
│       ├── reit_analysis_panel.csv
│       └── data_dictionary.md
├── results/
│   ├── figures/
│   ├── reports/
│   └── tables/
├── tests/
├── M1_data_quality_report.md
└── AI_AUDIT_APPENDIX.md
```

## How to Run (Milestone 1)
1. Verify paths:
	- `python code/config_paths.py`
2. Put raw file in `data/raw/`:
	- `reit_master_raw.csv`
3. Install dependencies:
	- `python -m pip install -r requirements.txt`
4. Run fetch/clean scripts:
	- `python code/fetch_reit_data.py`
	- `python code/fetch_macro_data.py`
5. Run merge script:
	- `python code/merge_final_panel.py`
6. Check outputs:
	- `data/final/reit_analysis_panel.csv`
	- `data/final/data_dictionary.md`

## Notes
- All scripts use relative paths through `code/config_paths.py`.
- Do not manually edit output CSV files in Excel; regenerate from scripts.
