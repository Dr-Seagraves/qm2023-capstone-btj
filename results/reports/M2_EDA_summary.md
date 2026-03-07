# M2 EDA Summary

## Key Findings
- The contemporaneous correlation between average REIT return (`usdret`) and the Federal Funds Rate (`FEDFUNDS`) is weakly negative (`r = -0.0129`), suggesting policy effects are likely delayed or mediated by other channels.
- Macro controls show strong collinearity: `UNRATE` vs `CPIAUCSL` (`|r| = 0.8926`) and `UNRATE` vs `T10Y2Y` (`|r| = 0.8259`), so M3 should avoid overloading specifications with redundant macro controls.
- Lag analysis of `FEDFUNDS` by REIT entity indicates the largest absolute correlation at the 12-month lag (`r = -0.0176`), with shorter lags close to zero; this supports testing distributed lags in M3.
- Because the panel currently has one observed sector category, heterogeneity was evaluated with approved alternatives: size quartile boxplots and 12-month rolling correlation.
- Rolling 12-month correlation of average returns with `FEDFUNDS` ranges from `-0.729` to `0.607`, showing meaningful time variation in rate sensitivity and motivating subperiod robustness checks.

## Hypotheses for M3

### Hypothesis 1: Driver Effect
- Claim: Higher policy rates reduce REIT returns with a delayed effect.
- Model specification: `usdret_it ~ FEDFUNDS_{t-k} + controls_it + entity_FE + time_FE`, where `k` includes 0, 3, 6, 12.
- Expected sign: Negative for medium-to-longer lags.
- Mechanism: Financing cost repricing and refinancing cycles can transmit policy shocks with delay.

### Hypothesis 2: Control Premiums
- Claim: Momentum-related controls affect near-term returns.
- Model specification: include `lag_return_1m` (and potentially `lag_return_3m`) as controls.
- Expected sign: Positive under momentum, though sign may vary by regime.
- Mechanism: Return persistence and behavioral underreaction can produce short-horizon autocorrelation.

### Hypothesis 3: Time-Varying Sensitivity
- Claim: Rate sensitivity is unstable across macro regimes.
- Model specification: include interaction terms with period indicators (e.g., crisis/tightening windows) or estimate subperiod models.
- Expected sign: Stronger negative sensitivity in tightening stress periods.
- Mechanism: Balance-sheet constraints and risk premia shift across monetary regimes.

## Data Quality Flags and M3 Mitigations
- Outliers in returns are present (crisis months). Mitigation: robust/clustered standard errors, influence diagnostics, and sensitivity checks with winsorized outcomes.
- Missingness is low in key variables (`lag_return_1m` ~ 0.77%, outcome complete). Mitigation: use consistent complete-case filters by model.
- Macro multicollinearity risk is high among controls. Mitigation: VIF screening, parsimonious control sets, and alternate specifications.
- Panel is unbalanced and sector variation is limited in this extract (single sector observed). Mitigation: emphasize within-entity/time identification, and frame heterogeneity via size/regime alternatives.

## Files Produced for M2
- `capstone_eda.ipynb`
- `results/figures/M2_plot1_correlation_heatmap.png`
- `results/figures/M2_plot2_outcome_timeseries.png`
- `results/figures/M2_plot3_dual_axis_return_fedfunds.png`
- `results/figures/M2_plot4_lagged_effects.png`
- `results/figures/M2_plot5_group_or_size_boxplot.png`
- `results/figures/M2_plot6_group_or_rolling_sensitivity.png`
- `results/figures/M2_plot7_scatter_controls.png`
- `results/figures/M2_plot8_time_series_decomposition.png`
