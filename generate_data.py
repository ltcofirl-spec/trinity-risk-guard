"""Generate SYNTHETIC credit-card/consumer-credit scorecard demo samples.

All ranges, dependencies and labels are designed, not empirically calibrated.
The sample has 800 reference / 800 current cases by DEFAULT, not a power claim.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scorecard_port import predict_probability

ROOT = Path(__file__).resolve().parent

def make_data(n=1600, seed=2026):
    if n < 100 or n % 2 != 0:
        raise ValueError('Use an even sample size >=100 (equal comparison periods)')
    rng = np.random.default_rng(seed)
    period = np.array(['reference']*(n//2) + ['current']*(n//2), dtype=object)
    # Income EUR 18k-180k, intentionally right-skewed rather than Gaussian.
    income = np.clip(rng.lognormal(mean=np.log(52), sigma=.38, size=n),18,180)
    # Current period is slightly more indebted: deliberate stress-test drift.
    util = np.clip(rng.beta(2.3,4.8,n) + .07*(period=='current'),0.01,.99)
    dti = np.clip(.19 + .32*util + .08*(income < 35) + rng.normal(0,.09,n)
                  + .02*(period=='current'), .05,.82)
    late_rate = .09 + .48*util + .28*(dti>.52)
    late = np.clip(rng.poisson(late_rate),0,4).astype(int)
    # Context and ethical review: age is NOT a scoring feature.
    age = rng.integers(21,76,size=n)
    audit_group = rng.choice(['SIM_A','SIM_B'],size=n, p=[.5,.5])
    loan_amount = np.round(np.clip(income*1000*rng.uniform(.06,.4,n),2000,35000),2)
    loans = pd.DataFrame({
      'customer_id':[f'SYN-{i+1:05d}' for i in range(n)],
      'period':period,
      'income_k':np.round(income,5),
      'utilization':np.round(util,7),
      'dti':np.round(dti,7),
      'late_payments_12m':late,
      'loan_amount_eur':loan_amount,
      'age_years_audit_only':age,
      'simulated_audit_group':audit_group,
    })
    predicted = predict_probability(loans)
    # Independent disturbance and omitted-variable effects prevent a PERFECT
    # circular match between score and synthetic labels; still NOT external proof.
    unobserved = rng.normal(0,.22,size=n)
    nonlinear = .28 * (loans['utilization'].to_numpy() > .70) + .18*(late>=2)
    log_odds = np.log(predicted/(1-predicted)) + unobserved + nonlinear
    p_true = 1/(1+np.exp(-log_odds))
    loans['defaulted'] = rng.binomial(1,p_true).astype(int)
    return loans

if __name__=='__main__':
    d=make_data()
    path=ROOT/'synthetic_credit_data.csv'
    d.to_csv(path,index=False)
    print(f'Generated {len(d)} synthetic cases: {d.period.value_counts().to_dict()} -> {path}')
