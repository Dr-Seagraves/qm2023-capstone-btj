"""
QM 2023 Capstone Project: M1 - Final Panel Merge
Team: BTJ
Members: [List names]

Merges processed REIT panel with FRED macro data into an analysis-ready panel.
  - Primary: data/processed/reit_master_clean.csv  (permno × ym)
  - Supplementary: data/processed/fred_macro_clean.csv  (ym only)
  - Join: LEFT join on ym  (many-to-one, row count must be preserved)
  - Output: data/final/reit_analysis_panel.csv
  - Produces: data/final/data_dictionary.md
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_paths import FINAL_DATA_DIR, PROCESSED_DATA_DIR


# ---------------------------------------------------------------------------
# Section 7: Auto-generate data dictionary
# ---------------------------------------------------------------------------

VARIABLE_META = {
    "permno":        ("CRSP permanent security identifier", "int",     "CRSP",  "ID"),
    "ticker":        ("Stock ticker symbol",                 "str",     "CRSP",  "symbol"),
    "comnam":        ("Company name",                        "str",     "CRSP",  "name"),
    "rtype":         ("REIT type code",                      "float",   "CRSP",  "code"),
    "ptype":         ("Property type code",                  "float",   "CRSP",  "code"),
    "psub":          ("Property sub-type code",              "float",   "CRSP",  "code"),
    "date":          ("Observation end date",                "str",     "CRSP",  "YYYY-MM-DD"),
    "caldt":         ("Calendar date",                       "str",     "CRSP",  "YYYY-MM-DD"),
    "ym":            ("Year-month (time variable)",          "str",     "CRSP",  "YYYY-MM"),
    "usdret":        ("Monthly USD total return",            "float",   "CRSP",  "decimal (0.05 = 5%)"),
    "usdprc":        ("Monthly closing price (USD)",         "float",   "CRSP",  "USD"),
    "market_equity": ("Market capitalization",               "float",   "CRSP",  "millions USD"),
    "assets":        ("Total assets",                        "float",   "Compustat", "millions USD"),
    "sales":         ("Total revenues/sales",                "float",   "Compustat", "millions USD"),
    "net_income":    ("Net income",                          "float",   "Compustat", "millions USD"),
    "book_equity":   ("Book equity",                         "float",   "Compustat", "millions USD"),
    "debt_at":       ("Total debt / total assets",           "float",   "Compustat", "ratio"),
    "cash_at":       ("Cash / total assets",                 "float",   "Compustat", "ratio"),
    "ocf_at":        ("Operating cash flow / total assets",  "float",   "Compustat", "ratio"),
    "roe":           ("Return on equity",                    "float",   "Compustat", "ratio"),
    "btm":           ("Book-to-market ratio",                "float",   "Compustat", "ratio"),
    "beta":          ("Market beta",                         "float",   "CRSP",  "dimensionless"),
    "fedfunds":      ("Effective Federal Funds Rate",        "float",   "FRED",  "percent"),
    "mortgage30us":  ("30-Year Fixed Mortgage Rate",         "float",   "FRED",  "percent"),
    "cpiaucsl":      ("Consumer Price Index (1982-84=100)",  "float",   "FRED",  "index"),
    "unrate":        ("Unemployment Rate",                   "float",   "FRED",  "percent"),
}


def write_data_dictionary(df: pd.DataFrame) -> None:
    n_entities = df["permno"].nunique()
    n_periods = df["ym"].nunique()
    time_min = df["ym"].min()
    time_max = df["ym"].max()
    obs_per = df.groupby("permno")["ym"].count()
    balanced = obs_per.nunique() == 1
    struct = "Balanced" if balanced else f"Unbalanced (min {obs_per.min()}, max {obs_per.max()} periods)"

    rows = []
    for col in df.columns:
        meta = VARIABLE_META.get(col, ("TODO", str(df[col].dtype), "TODO", "TODO"))
        desc, dtype, source, units = meta
        missing_pct = f"{100 * df[col].isnull().mean():.1f}%"
        rows.append(f"| {col} | {desc} | {dtype} | {source} | {units} | {missing_pct} |")

    content = f"""# Data Dictionary: REIT Analysis Panel

## Dataset Overview
- **Dataset Name:** REIT Analysis Panel (BTJ Team)
- **Primary Source:** CRSP/Compustat REIT Master
- **Supplementary Source:** FRED (Federal Reserve Economic Data)
- **Number of Entities (permno):** {n_entities:,}
- **Number of Time Periods (ym):** {n_periods:,}
- **Total Observations:** {df.shape[0]:,}
- **Time Range:** {time_min} to {time_max}
- **Panel Structure:** {struct}

## Variable Definitions
| Variable | Description | Type | Source | Units | Missing % |
|----------|-------------|------|--------|-------|-----------|
{chr(10).join(rows)}

## Cleaning Decisions Summary
- **Missing usdret:** Dropped (delistings / IPO gaps) — see M1_data_quality_report.md
- **Date filter:** Restricted to 2000-01 onward to align with FRED macro coverage
- **Outliers (usdret):** Winsorized at 1st/99th percentile
- **Size filter:** Dropped observations with market_equity < $10M
- **Duplicates (permno-ym):** Kept first occurrence (none found in this dataset)
- **Macro alignment:** Monthly last-observation; forward-filled any FRED gaps
"""

    dict_path = FINAL_DATA_DIR / "data_dictionary.md"
    dict_path.write_text(content, encoding="utf-8")
    print(f"Saved data dictionary: {dict_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n=== M1: Merge Final Analysis Panel ===")

    # ------------------------------------------------------------------
    # Section 2: Load processed datasets
    # ------------------------------------------------------------------
    primary_file = PROCESSED_DATA_DIR / "reit_master_clean.csv"
    macro_file   = PROCESSED_DATA_DIR / "fred_macro_clean.csv"

    for f in (primary_file, macro_file):
        if not f.exists():
            raise FileNotFoundError(
                f"Missing processed input: {f}\n"
                "Run fetch_reit_data.py and fetch_macro_data.py first."
            )

    primary = pd.read_csv(primary_file, dtype={"permno": "Int64"})
    macro   = pd.read_csv(macro_file)
    print(f"Primary rows loaded:  {len(primary):,}")
    print(f"Macro rows loaded:    {len(macro):,}")

    # ------------------------------------------------------------------
    # Section 3: Align time variables
    # ------------------------------------------------------------------
    # Both should already be YYYY-MM strings; normalise just in case
    primary["ym"] = pd.to_datetime(primary["ym"], format="%Y-%m", errors="coerce").dt.strftime("%Y-%m")
    macro["ym"]   = pd.to_datetime(macro["ym"],   format="%Y-%m", errors="coerce").dt.strftime("%Y-%m")

    # Remove any time-period duplicates in supplementary before merge
    macro = macro.drop_duplicates(subset=["ym"], keep="last")

    # ------------------------------------------------------------------
    # Section 4: Left join on ym
    # ------------------------------------------------------------------
    before_rows = len(primary)
    merged = primary.merge(macro, on="ym", how="left", validate="many_to_one")
    after_rows  = len(merged)

    print(f"\nPrimary rows before merge: {before_rows:,}")
    print(f"Rows after merge:          {after_rows:,}")

    if after_rows != before_rows:
        raise AssertionError(
            f"Row count changed after merge: {before_rows} → {after_rows}. "
            "Check for duplicate ym values in macro file."
        )

    # ------------------------------------------------------------------
    # Section 5: Verify merge integrity
    # ------------------------------------------------------------------
    dup_keys = merged.duplicated(subset=["permno", "ym"]).sum()
    print(f"Duplicate permno-ym keys after merge: {dup_keys:,}")

    macro_cols = [c for c in macro.columns if c != "ym"]
    macro_nulls = merged[macro_cols].isnull().sum()
    print("Macro NaN counts after merge:")
    print(macro_nulls.to_string())

    # ------------------------------------------------------------------
    # Section 6: Save output
    # ------------------------------------------------------------------
    merged = merged.sort_values(["permno", "ym"]).reset_index(drop=True)
    output_panel = FINAL_DATA_DIR / "reit_analysis_panel.csv"
    merged.to_csv(output_panel, index=False)
    print(f"\nSaved final panel: {output_panel}")
    print(f"Final shape: {merged.shape[0]:,} rows × {merged.shape[1]:,} columns")
    print(f"Entities (permno): {merged['permno'].nunique():,}")
    print(f"Date range: {merged['ym'].min()} → {merged['ym'].max()}")

    # ------------------------------------------------------------------
    # Section 7: Data dictionary
    # ------------------------------------------------------------------
    write_data_dictionary(merged)

    print("\n✓ Milestone 1 pipeline complete.")


if __name__ == "__main__":
    main()
