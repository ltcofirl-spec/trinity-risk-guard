# Trinity Risk Guard — Model Validation Evidence (Synthetic Demo)
> NOT independent validation, model approval, EXL sample data or real banking evidence.

## Data and documentation
- 3 author-generated model inventory entries (Credit / Fraud / Pricing); only Credit migrated.
- 1,600 fabricated loan records, seed 2026, 800 reference and 800 current.
- Four coefficients and risk bands are disclosed scenario assumptions, not fitted or approved.

## R → Python migration
- **Current parity status:** NOT_RUN
- A PASS requires actual Rscript execution and 1,600 matched IDs and probabilities/bands.

## Predictive performance (synthetic labels)
- ROC-AUC: 0.6295
- Average Precision: 0.1983
- Brier score: 0.1039
- Observed default rate: 12.12%; mean predicted PD: 12.18%
- AUC reference: 0.6528; current: 0.5970

## Stability (two designed simulation periods)
- utilization_psi: 0.2692
- dti_psi: 0.1464
- income_k_psi: 0.0316
- late_payments_12m_psi: 0.0084
- predicted_pd_psi: 0.2335

## Fairness diagnostics (NOT a real fairness audit)
- Fictional labels SIM_A and SIM_B are random group identifiers, not protected traits.
- TPR, FPR, Brier and predicted-PD gaps illustrate validation methodology only.
- No real-world fairness conclusion is possible; representative protected-group information and independent review are needed.

## Automatic review flags
- REVIEW: low_synthetic_auc — AUC < 0.70 heuristic, not EXL or bank threshold
- REVIEW: utilization_shift — PSI > .25 exploratory heuristic, not a bank policy
- LIMITATION: fictional_groups — SIM_A/SIM_B are randomly assigned and NOT protected traits; no fairness conclusion possible

## Governance
- Human review required before accepting any documentation or migration as validated.
- Parity does NOT prove statistical validity; synthetic testing does NOT establish regulatory compliance.
- LLM Agent status: NOT_RUN
