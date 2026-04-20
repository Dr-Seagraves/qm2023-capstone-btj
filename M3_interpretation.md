# M3 Interpretation Memo

## 1. Model A Headline Result
A 1 percentage point increase in FEDFUNDS (12-month lag) is associated with a -0.0134 change in monthly REIT return (p-value = 0.2414) in the two-way fixed effects model with clustered standard errors.

## 2. Economic Interpretation
The estimated effect is interpreted through three channels:
1. Leverage channel: higher policy rates raise financing costs, reducing equity cash-flow residuals.
2. Discount-rate channel: higher rates raise discount factors, lowering present values of long-duration real-estate cash flows.
3. Demand channel: tighter monetary policy slows macro demand and property market turnover.

## 3. Model B Summary (ML Comparison)
Out-of-sample comparison shows:
- OLS: R2 = 0.0032, RMSE = 0.1029
- Random Forest: R2 = -0.0788, RMSE = 0.1070

Interpretation: any predictive gain from Random Forest should be weighed against reduced interpretability relative to linear coefficients.

## 4. Diagnostics
- Heteroskedasticity (Breusch-Pagan LM p-value): 0.0000
- Maximum VIF across baseline predictors: 8.3962
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
