"""Auditable Python migration of self-authored legacy R scorecard v1.1.

NOT a bank-trained model. Coefficients are transparent illustrative assumptions.
Identical features, validation, coefficients and bands are defined in R source.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

VERSION = 'SC-CREDIT-1.1'
COLUMNS = ('utilization', 'dti', 'income_k', 'late_payments_12m')
COEFFICIENTS = {
    'intercept': -2.98,
    'utilization': 1.65,
    'dti': 1.13,
    'income_k': -0.0041,
    'late_payments_12m': 0.62,
}
# The ranges are SYNTHETIC SCENARIO / INPUT CONTRACT assumptions, not bank rules.
RANGES = {'utilization': (0, 1), 'dti': (0, .85), 'income_k': (18, 180), 'late_payments_12m': (0, 4)}

def _validate(df: pd.DataFrame) -> dict[str, np.ndarray]:
    if not isinstance(df, pd.DataFrame):
        raise TypeError('Expected a pandas DataFrame')
    if df.empty:
        raise ValueError('Input data must not be empty')
    missing = [c for c in COLUMNS if c not in df]
    if missing:
        raise ValueError('Missing required columns: '+', '.join(missing))
    result = {}
    for c in COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise ValueError(f'{c} must be numeric (not text)')
        x = df[c].to_numpy(dtype=np.float64)
        lo, hi = RANGES[c]
        if not np.isfinite(x).all() or ((x<lo)|(x>hi)).any():
            raise ValueError(f'{c} must be finite and in [{lo}, {hi}]')
        if c == 'late_payments_12m' and (x!=np.floor(x)).any():
            raise ValueError('late_payments_12m must be an integer')
        result[c] = x
    if 'customer_id' in df:
        if df['customer_id'].isna().any() or df['customer_id'].duplicated().any():
            raise ValueError('customer_id must be unique and nonmissing')
    return result

def predict_probability(df: pd.DataFrame) -> np.ndarray:
    x = _validate(df)
    z = (COEFFICIENTS['intercept']
         + COEFFICIENTS['utilization']*x['utilization']
         + COEFFICIENTS['dti']*x['dti']
         + COEFFICIENTS['income_k']*x['income_k']
         + COEFFICIENTS['late_payments_12m']*x['late_payments_12m'])
    return 1.0 / (1.0 + np.exp(-z))

def classify_risk(probability: np.ndarray) -> np.ndarray:
    """Illustrative policy: thresholds are NOT empirically set/approved."""
    p = np.asarray(probability, dtype=np.float64)
    return np.where(p < .08, 'LOW', np.where(p < .18, 'MEDIUM', 'HIGH'))

def score_frame(df: pd.DataFrame) -> pd.DataFrame:
    p = predict_probability(df)
    ids = df['customer_id'].astype(str).to_numpy() if 'customer_id' in df else np.arange(len(df)).astype(str)
    return pd.DataFrame({'customer_id':ids, 'python_probability':p,
                         'python_risk_band':classify_risk(p), 'model_version':VERSION})
