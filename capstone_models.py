"""
QM 2023 Capstone: Milestone 3 Econometric Models
Team: REIT Sectoral Rate Sensitivity Analysis Team
Members: Josh Love, Brody Duffel, Tallulah Pascucci
Date: 2026-04-16

This script estimates panel regression models to identify causal effects of
interest-rate drivers on REIT returns. It estimates:
- Model A (required): Two-way Fixed Effects panel model
- Model B (chosen): Machine Learning comparison (Random Forest vs OLS)

Outputs:
- Publication-ready regression and diagnostics tables -> results/tables/
- Diagnostic and robustness figures -> results/figures/
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure code/ imports resolve when this script runs from repository root.
ROOT_DIR = Path(__file__).resolve().parent
CODE_DIR = ROOT_DIR / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from config_paths import FINAL_DATA_DIR, FIGURES_DIR, TABLES_DIR

try:
    from linearmodels.panel import PanelOLS
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "linearmodels is required for Model A. Install with: pip install linearmodels"
    ) from exc


PANEL_FILE = FINAL_DATA_DIR / "reit_fred_analysis_panel.csv"


MODEL_A_OUTCOME = "usdret"
MODEL_A_PREDICTORS = [
    "FEDFUNDS_LAG12",
    "lag_return_1m",
    "log_market_cap",
    "UNRATE",
]


MODEL_B_FEATURES = [
    "FEDFUNDS_LAG1",
    "FEDFUNDS_LAG3",
    "FEDFUNDS_LAG12",
    "MORTGAGE30US",
    "UNRATE",
    "INFLATION_RATE",
    "lag_return_1m",
    "lag_return_3m",
    "log_market_cap",
]


RANDOM_STATE = 42


sns.set_theme(style="whitegrid")


def significance_stars(p_value: float) -> str:
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def format_coef_row(coef: float, se: float, p_value: float) -> str:
    return f"{coef:.4f}{significance_stars(p_value)} ({se:.4f})"


def ensure_outputs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)


def load_and_engineer_data() -> pd.DataFrame:
    if not PANEL_FILE.exists():
        raise FileNotFoundError(
            f"Final panel not found at {PANEL_FILE}. Run merge_final_panel.py first."
        )

    df = pd.read_csv(PANEL_FILE)
    df["ym"] = pd.to_datetime(df["ym"])
    df = df.sort_values(["permno", "ym"]).reset_index(drop=True)

    # M2 indicated delayed effects; include long lag for M3 baseline model.
    if "FEDFUNDS" in df.columns:
        df["FEDFUNDS_LAG12"] = df.groupby("permno")["FEDFUNDS"].shift(12)

    # Outlier/crisis windows for robustness checks.
    crisis_2008 = (df["ym"] >= "2008-01-01") & (df["ym"] <= "2009-12-31")
    crisis_covid = (df["ym"] >= "2020-03-01") & (df["ym"] <= "2020-05-31")
    df["is_crisis_period"] = (crisis_2008 | crisis_covid).astype(int)

    # Size group for subgroup robustness.
    df["size_group"] = pd.qcut(
        df["log_market_cap"], q=2, labels=["Small", "Large"], duplicates="drop"
    )

    return df


def make_panel(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    needed = ["permno", "ym", outcome] + predictors
    sample = df[needed].dropna().copy()
    sample = sample.set_index(["permno", "ym"])

    y = sample[outcome]
    X = sample[predictors]
    return sample, y, X


def fit_fe(
    y: pd.Series,
    X: pd.DataFrame,
    clustered: bool,
):
    model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
    if clustered:
        return model.fit(cov_type="clustered", cluster_entity=True)
    return model.fit(cov_type="unadjusted")


def run_model_a(df: pd.DataFrame) -> Dict[str, object]:
    sample, y, X = make_panel(df, MODEL_A_OUTCOME, MODEL_A_PREDICTORS)

    fe_unadjusted = fit_fe(y, X, clustered=False)
    fe_clustered = fit_fe(y, X, clustered=True)

    return {
        "sample": sample,
        "y": y,
        "X": X,
        "fe_unadjusted": fe_unadjusted,
        "fe_clustered": fe_clustered,
    }


def run_diagnostics(model_a: Dict[str, object]) -> Dict[str, pd.DataFrame]:
    sample = model_a["sample"].copy().reset_index()
    predictors = MODEL_A_PREDICTORS

    # Breusch-Pagan on pooled OLS residuals as diagnostic proxy.
    ols_exog = sm.add_constant(sample[predictors])
    pooled_ols = sm.OLS(sample[MODEL_A_OUTCOME], ols_exog).fit()
    bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(
        pooled_ols.resid,
        pooled_ols.model.exog,
    )

    bp_table = pd.DataFrame(
        {
            "Metric": [
                "LM Statistic",
                "LM p-value",
                "F Statistic",
                "F-test p-value",
            ],
            "Value": [bp_stat, bp_pvalue, f_stat, f_pvalue],
        }
    )
    bp_table.to_csv(TABLES_DIR / "M3_breusch_pagan.csv", index=False)

    # VIF diagnostics.
    X_vif = sample[predictors].copy()
    vif_values = [
        variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])
    ]
    vif_table = pd.DataFrame({"Variable": predictors, "VIF": vif_values})
    vif_table.to_csv(TABLES_DIR / "M3_vif_table.csv", index=False)

    # Residual plots from FE clustered model.
    fe_clustered = model_a["fe_clustered"]
    fitted = np.asarray(fe_clustered.fitted_values).reshape(-1)
    residuals = np.asarray(fe_clustered.resids).reshape(-1)

    plt.figure(figsize=(10, 6))
    plt.scatter(fitted, residuals, alpha=0.25)
    plt.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.xlabel("Fitted Values")
    plt.ylabel("Residuals")
    plt.title("M3: Residuals vs Fitted (Fixed Effects)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "M3_residuals_vs_fitted.png", dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title("M3: Q-Q Plot of FE Residuals")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "M3_qq_plot.png", dpi=300)
    plt.close()

    return {
        "bp_table": bp_table,
        "vif_table": vif_table,
    }


def run_robustness(df: pd.DataFrame, model_a: Dict[str, object]) -> Dict[str, pd.DataFrame]:
    records = []

    # Check 1: clustered vs non-clustered FE standard errors.
    base_clustered = model_a["fe_clustered"]
    base_unadjusted = model_a["fe_unadjusted"]
    for label, result in [
        ("Baseline_FE_Clustered", base_clustered),
        ("Baseline_FE_Unadjusted", base_unadjusted),
    ]:
        records.append(
            {
                "Check": "SE Comparison",
                "Model": label,
                "Driver": "FEDFUNDS_LAG12",
                "Coef": result.params.get("FEDFUNDS_LAG12", np.nan),
                "SE": result.std_errors.get("FEDFUNDS_LAG12", np.nan),
                "p_value": result.pvalues.get("FEDFUNDS_LAG12", np.nan),
                "N": result.nobs,
                "R2_within": result.rsquared_within,
            }
        )

    # Check 2: alternative lag structures (1, 3, 12).
    alt_lag_specs = {
        "Lag1": ["FEDFUNDS_LAG1", "lag_return_1m", "log_market_cap", "UNRATE"],
        "Lag3": ["FEDFUNDS_LAG3", "lag_return_1m", "log_market_cap", "UNRATE"],
        "Lag12": ["FEDFUNDS_LAG12", "lag_return_1m", "log_market_cap", "UNRATE"],
    }

    lag_plot_data = []
    for lag_name, predictors in alt_lag_specs.items():
        sample, y, X = make_panel(df, MODEL_A_OUTCOME, predictors)
        result = fit_fe(y, X, clustered=True)

        driver = predictors[0]
        coef = result.params.get(driver, np.nan)
        se = result.std_errors.get(driver, np.nan)
        pval = result.pvalues.get(driver, np.nan)

        records.append(
            {
                "Check": "Alternative Lag",
                "Model": f"FE_{lag_name}",
                "Driver": driver,
                "Coef": coef,
                "SE": se,
                "p_value": pval,
                "N": result.nobs,
                "R2_within": result.rsquared_within,
            }
        )

        lag_plot_data.append(
            {
                "Lag": lag_name,
                "Coef": coef,
                "Lower95": coef - 1.96 * se,
                "Upper95": coef + 1.96 * se,
            }
        )

    lag_plot_df = pd.DataFrame(lag_plot_data)
    plt.figure(figsize=(8, 5))
    plt.errorbar(
        lag_plot_df["Lag"],
        lag_plot_df["Coef"],
        yerr=[lag_plot_df["Coef"] - lag_plot_df["Lower95"], lag_plot_df["Upper95"] - lag_plot_df["Coef"]],
        fmt="o-",
        capsize=5,
    )
    plt.axhline(0, color="black", linestyle="--", linewidth=1)
    plt.title("M3 Robustness: FEDFUNDS Coefficient Across Lag Specs")
    plt.ylabel("Coefficient Estimate")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "M3_robustness_lag_coefficients.png", dpi=300)
    plt.close()

    # Check 3: exclude crisis windows.
    df_no_crisis = df[df["is_crisis_period"] == 0].copy()
    sample_nc, y_nc, X_nc = make_panel(df_no_crisis, MODEL_A_OUTCOME, MODEL_A_PREDICTORS)
    result_nc = fit_fe(y_nc, X_nc, clustered=True)
    records.append(
        {
            "Check": "Exclude Crisis Periods",
            "Model": "FE_NoCrisis_Clustered",
            "Driver": "FEDFUNDS_LAG12",
            "Coef": result_nc.params.get("FEDFUNDS_LAG12", np.nan),
            "SE": result_nc.std_errors.get("FEDFUNDS_LAG12", np.nan),
            "p_value": result_nc.pvalues.get("FEDFUNDS_LAG12", np.nan),
            "N": result_nc.nobs,
            "R2_within": result_nc.rsquared_within,
        }
    )

    # Check 4: subgroup robustness by size.
    for subgroup in ["Small", "Large"]:
        subgroup_df = df[df["size_group"].astype(str) == subgroup].copy()
        if subgroup_df.empty:
            continue
        sample_s, y_s, X_s = make_panel(subgroup_df, MODEL_A_OUTCOME, MODEL_A_PREDICTORS)
        if len(sample_s) < 500:
            continue
        result_s = fit_fe(y_s, X_s, clustered=True)
        records.append(
            {
                "Check": "Size Subsample",
                "Model": f"FE_{subgroup}_Clustered",
                "Driver": "FEDFUNDS_LAG12",
                "Coef": result_s.params.get("FEDFUNDS_LAG12", np.nan),
                "SE": result_s.std_errors.get("FEDFUNDS_LAG12", np.nan),
                "p_value": result_s.pvalues.get("FEDFUNDS_LAG12", np.nan),
                "N": result_s.nobs,
                "R2_within": result_s.rsquared_within,
            }
        )

    robustness_table = pd.DataFrame(records)
    robustness_table.to_csv(TABLES_DIR / "M3_robustness_summary.csv", index=False)

    return {
        "robustness_table": robustness_table,
    }


def build_publication_table(model_a: Dict[str, object], robustness: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    base_unadj = model_a["fe_unadjusted"]
    base_clust = model_a["fe_clustered"]

    robust_table = robustness["robustness_table"]
    nocrisis = robust_table[robust_table["Model"] == "FE_NoCrisis_Clustered"]
    nocrisis_coef = np.nan
    nocrisis_se = np.nan
    nocrisis_p = np.nan
    nocrisis_n = np.nan
    nocrisis_r2 = np.nan
    if not nocrisis.empty:
        nocrisis_coef = float(nocrisis.iloc[0]["Coef"])
        nocrisis_se = float(nocrisis.iloc[0]["SE"])
        nocrisis_p = float(nocrisis.iloc[0]["p_value"])
        nocrisis_n = float(nocrisis.iloc[0]["N"])
        nocrisis_r2 = float(nocrisis.iloc[0]["R2_within"])

    rows = []
    variable_order = MODEL_A_PREDICTORS
    for var in variable_order:
        rows.append(
            {
                "Variable": var,
                "Model_1_FE_Unadjusted": format_coef_row(
                    base_unadj.params.get(var, np.nan),
                    base_unadj.std_errors.get(var, np.nan),
                    base_unadj.pvalues.get(var, np.nan),
                ),
                "Model_2_FE_Clustered": format_coef_row(
                    base_clust.params.get(var, np.nan),
                    base_clust.std_errors.get(var, np.nan),
                    base_clust.pvalues.get(var, np.nan),
                ),
                "Model_3_FE_NoCrisis_Clustered": (
                    format_coef_row(nocrisis_coef, nocrisis_se, nocrisis_p)
                    if pd.notna(nocrisis_coef)
                    else "NA"
                ),
            }
        )

    rows.append(
        {
            "Variable": "Entity FE",
            "Model_1_FE_Unadjusted": "Yes",
            "Model_2_FE_Clustered": "Yes",
            "Model_3_FE_NoCrisis_Clustered": "Yes",
        }
    )
    rows.append(
        {
            "Variable": "Time FE",
            "Model_1_FE_Unadjusted": "Yes",
            "Model_2_FE_Clustered": "Yes",
            "Model_3_FE_NoCrisis_Clustered": "Yes",
        }
    )
    rows.append(
        {
            "Variable": "Clustered SE",
            "Model_1_FE_Unadjusted": "No",
            "Model_2_FE_Clustered": "Yes",
            "Model_3_FE_NoCrisis_Clustered": "Yes",
        }
    )
    rows.append(
        {
            "Variable": "N",
            "Model_1_FE_Unadjusted": int(base_unadj.nobs),
            "Model_2_FE_Clustered": int(base_clust.nobs),
            "Model_3_FE_NoCrisis_Clustered": int(nocrisis_n) if pd.notna(nocrisis_n) else "NA",
        }
    )
    rows.append(
        {
            "Variable": "R2_within",
            "Model_1_FE_Unadjusted": round(float(base_unadj.rsquared_within), 4),
            "Model_2_FE_Clustered": round(float(base_clust.rsquared_within), 4),
            "Model_3_FE_NoCrisis_Clustered": round(float(nocrisis_r2), 4) if pd.notna(nocrisis_r2) else "NA",
        }
    )

    table = pd.DataFrame(rows)
    table.to_csv(TABLES_DIR / "M3_regression_table.csv", index=False)
    return table


def run_model_b_ml(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    needed = ["ym", MODEL_A_OUTCOME] + MODEL_B_FEATURES
    sample = df[needed].dropna().copy()

    unique_dates = np.array(sorted(sample["ym"].unique()))
    split_idx = int(len(unique_dates) * 0.8)
    split_idx = max(split_idx, 1)
    cutoff = unique_dates[split_idx - 1]

    train = sample[sample["ym"] <= cutoff].copy()
    test = sample[sample["ym"] > cutoff].copy()

    if train.empty or test.empty:
        raise ValueError("Train/test split failed for Model B. Check date coverage.")

    X_train = train[MODEL_B_FEATURES]
    y_train = train[MODEL_A_OUTCOME]
    X_test = test[MODEL_B_FEATURES]
    y_test = test[MODEL_A_OUTCOME]

    # Interpretable baseline model.
    ols = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    ols_pred = ols.predict(sm.add_constant(X_test, has_constant="add"))

    # Nonlinear benchmark model.
    rf = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    metrics = pd.DataFrame(
        {
            "Model": ["OLS", "RandomForest"],
            "R2_test": [r2_score(y_test, ols_pred), r2_score(y_test, rf_pred)],
            "RMSE_test": [
                np.sqrt(mean_squared_error(y_test, ols_pred)),
                np.sqrt(mean_squared_error(y_test, rf_pred)),
            ],
            "N_train": [len(train), len(train)],
            "N_test": [len(test), len(test)],
        }
    )
    metrics.to_csv(TABLES_DIR / "M3_modelB_ml_metrics.csv", index=False)

    ols_coef_table = pd.DataFrame(
        {
            "Variable": ols.params.index,
            "Coef": ols.params.values,
            "StdErr": ols.bse.values,
            "p_value": ols.pvalues.values,
        }
    )
    ols_coef_table.to_csv(TABLES_DIR / "M3_modelB_ols_coefficients.csv", index=False)

    feat_importance = pd.DataFrame(
        {
            "Feature": MODEL_B_FEATURES,
            "Importance": rf.feature_importances_,
        }
    ).sort_values("Importance", ascending=False)
    feat_importance.to_csv(TABLES_DIR / "M3_modelB_rf_feature_importance.csv", index=False)

    # Plot 1: Out-of-sample performance over time (monthly means for readability).
    perf_df = pd.DataFrame(
        {
            "ym": test["ym"],
            "actual": y_test,
            "ols_pred": ols_pred,
            "rf_pred": rf_pred,
        }
    )
    perf_monthly = perf_df.groupby("ym", as_index=False).mean(numeric_only=True)

    plt.figure(figsize=(11, 6))
    plt.plot(perf_monthly["ym"], perf_monthly["actual"], label="Actual", linewidth=2)
    plt.plot(perf_monthly["ym"], perf_monthly["ols_pred"], label="OLS Prediction", alpha=0.9)
    plt.plot(perf_monthly["ym"], perf_monthly["rf_pred"], label="RF Prediction", alpha=0.9)
    plt.title("M3 Model B: Out-of-Sample Monthly Mean Predictions")
    plt.xlabel("Date")
    plt.ylabel("REIT Return")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "M3_modelB_actual_vs_predictions.png", dpi=300)
    plt.close()

    # Plot 2: RF feature importance.
    plt.figure(figsize=(10, 5))
    sns.barplot(data=feat_importance, x="Importance", y="Feature", orient="h")
    plt.title("M3 Model B: Random Forest Feature Importance")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "M3_modelB_rf_feature_importance.png", dpi=300)
    plt.close()

    return {
        "metrics": metrics,
        "ols_coef_table": ols_coef_table,
        "feat_importance": feat_importance,
    }


def write_interpretation_memo(
    model_a: Dict[str, object],
    diagnostics: Dict[str, pd.DataFrame],
    robustness: Dict[str, pd.DataFrame],
    model_b: Dict[str, pd.DataFrame],
) -> None:
    fe = model_a["fe_clustered"]

    driver_coef = float(fe.params.get("FEDFUNDS_LAG12", np.nan))
    driver_p = float(fe.pvalues.get("FEDFUNDS_LAG12", np.nan))

    bp_pval = float(
        diagnostics["bp_table"].loc[
            diagnostics["bp_table"]["Metric"] == "LM p-value", "Value"
        ].iloc[0]
    )

    max_vif = float(diagnostics["vif_table"]["VIF"].max())

    ml_metrics = model_b["metrics"].set_index("Model")
    ols_r2 = float(ml_metrics.loc["OLS", "R2_test"])
    rf_r2 = float(ml_metrics.loc["RandomForest", "R2_test"])
    ols_rmse = float(ml_metrics.loc["OLS", "RMSE_test"])
    rf_rmse = float(ml_metrics.loc["RandomForest", "RMSE_test"])

    robustness_table = robustness["robustness_table"]

    memo_text = f"""# M3 Interpretation Memo

## 1. Model A Headline Result
A 1 percentage point increase in FEDFUNDS (12-month lag) is associated with a {driver_coef:.4f} change in monthly REIT return (p-value = {driver_p:.4f}) in the two-way fixed effects model with clustered standard errors.

## 2. Economic Interpretation
The estimated effect is interpreted through three channels:
1. Leverage channel: higher policy rates raise financing costs, reducing equity cash-flow residuals.
2. Discount-rate channel: higher rates raise discount factors, lowering present values of long-duration real-estate cash flows.
3. Demand channel: tighter monetary policy slows macro demand and property market turnover.

## 3. Model B Summary (ML Comparison)
Out-of-sample comparison shows:
- OLS: R2 = {ols_r2:.4f}, RMSE = {ols_rmse:.4f}
- Random Forest: R2 = {rf_r2:.4f}, RMSE = {rf_rmse:.4f}

Interpretation: any predictive gain from Random Forest should be weighed against reduced interpretability relative to linear coefficients.

## 4. Diagnostics
- Heteroskedasticity (Breusch-Pagan LM p-value): {bp_pval:.4f}
- Maximum VIF across baseline predictors: {max_vif:.4f}
- Residual diagnostics saved to:
  - results/figures/M3_residuals_vs_fitted.png
  - results/figures/M3_qq_plot.png

Implication: clustered standard errors are retained as the default inference strategy for panel dependence and potential heteroskedasticity.

## 5. Robustness Checks
Robustness checks completed (>=3 required):
1. Clustered vs unadjusted standard errors.
2. Alternative lag structures (1, 3, 12 months).
3. Excluding crisis periods (2008-2009 and 2020-03 to 2020-05).
4. Size-based subsample regressions.

Detailed outputs are saved in results/tables/M3_robustness_summary.csv.

## 6. Caveats and Identification Limits
1. Omitted variable bias remains possible for unobserved time-varying factors (for example sentiment or liquidity shocks).
2. The panel appears sector-limited in this extract, so heterogeneity claims should be framed primarily as size/regime heterogeneity.
3. Fixed effects identify within-entity variation and do not directly recover cross-sectional long-run level effects.

## 7. Files Produced
- capstone_models.py
- results/tables/M3_regression_table.csv
- results/tables/M3_breusch_pagan.csv
- results/tables/M3_vif_table.csv
- results/tables/M3_robustness_summary.csv
- results/tables/M3_modelB_ml_metrics.csv
- results/tables/M3_modelB_ols_coefficients.csv
- results/tables/M3_modelB_rf_feature_importance.csv
- results/figures/M3_residuals_vs_fitted.png
- results/figures/M3_qq_plot.png
- results/figures/M3_robustness_lag_coefficients.png
- results/figures/M3_modelB_actual_vs_predictions.png
- results/figures/M3_modelB_rf_feature_importance.png
"""

    memo_path = ROOT_DIR / "M3_interpretation.md"
    memo_path.write_text(memo_text, encoding="utf-8")


def main() -> None:
    print("=" * 80)
    print("MILESTONE 3: ECONOMETRIC MODELS")
    print("=" * 80)

    ensure_outputs()

    print("\n[1/6] Loading and engineering data...")
    df = load_and_engineer_data()
    print(f"  Loaded {len(df):,} rows")

    print("\n[2/6] Estimating Model A (Two-Way Fixed Effects)...")
    model_a = run_model_a(df)
    print("  Model A estimated (unadjusted and clustered SE variants)")

    print("\n[3/6] Running required diagnostics...")
    diagnostics = run_diagnostics(model_a)
    print("  Diagnostics saved to results/tables and results/figures")

    print("\n[4/6] Running robustness checks...")
    robustness = run_robustness(df, model_a)
    print("  Robustness outputs saved")

    print("\n[5/6] Building publication-ready regression table...")
    build_publication_table(model_a, robustness)
    print("  Regression table saved")

    print("\n[6/6] Estimating Model B (ML comparison: RF vs OLS)...")
    model_b = run_model_b_ml(df)
    print("  Model B outputs saved")

    print("\n[7/7] Writing interpretation memo scaffold with model outputs...")
    write_interpretation_memo(model_a, diagnostics, robustness, model_b)
    print("  M3_interpretation.md written")

    print("\nDone. Milestone 3 artifacts are in results/tables and results/figures.")


if __name__ == "__main__":
    main()
