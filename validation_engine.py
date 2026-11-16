"""Deterministic model-risk checks on fully synthetic samples.
These are demonstration diagnostics, NOT independent validation or regulatory approval.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, confusion_matrix


def psi(reference, current, n_bins=10):
    """Population Stability Index with reference-derived quantile buckets.
    Conventional thresholds are illustrative investigation heuristics, not bank policy.
    """
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    if not (len(ref) and len(cur) and np.isfinite(ref).all() and np.isfinite(cur).all()):
        raise ValueError('PSI requires non-empty finite numeric groups')
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, n_bins + 1)))
    if len(edges) < 3:
        return None  # cannot estimate PSI when reference is constant
    edges[0], edges[-1] = -np.inf, np.inf
    rp = np.histogram(ref, bins=edges)[0] / len(ref)
    cp = np.histogram(cur, bins=edges)[0] / len(cur)
    rp, cp = np.maximum(rp, 1e-6), np.maximum(cp, 1e-6)
    return float(np.sum((cp - rp) * np.log(cp / rp)))


def _metrics(y, p, threshold=0.18):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    if len(y) != len(p) or not len(y):
        raise ValueError('Metrics need same-length nonempty arrays')
    if not np.isin(y, [0,1]).all() or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid labels or probabilities')
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    return {
        'n': int(len(y)),
        'positives': int(np.sum(y)),
        'prevalence': float(y.mean()),
        'mean_predicted_pd': float(p.mean()),
        'auc': float(roc_auc_score(y,p)) if len(np.unique(y)) == 2 else None,
        'average_precision': float(average_precision_score(y,p)) if int(y.sum()) else None,
        'brier': float(brier_score_loss(y,p)),
        'tpr': float(tp / (tp+fn)) if tp+fn else None,
        'fpr': float(fp / (fp+tn)) if fp+tn else None,
        'precision_at_threshold': float(tp/(tp+fp)) if tp+fp else None,
        'confusion': {'tn': int(tn), 'fp':int(fp), 'fn':int(fn), 'tp':int(tp)},
    }


def evaluate(df: pd.DataFrame, probabilities: np.ndarray):
    mandatory = {'period','defaulted','utilization','dti','income_k','late_payments_12m','simulated_audit_group'}
    if missing := mandatory.difference(df.columns):
        raise ValueError('Missing validation columns: ' + ', '.join(sorted(missing)))
    if set(df.period.unique()) != {'reference','current'}:
        raise ValueError('Two simulation periods required')
    y = df.defaulted.to_numpy()
    p = np.asarray(probabilities, dtype=float)
    ref = (df.period == 'reference').to_numpy()
    cur = ~ref
    overall = _metrics(y,p)
    ref_m = _metrics(y[ref],p[ref]); cur_m = _metrics(y[cur],p[cur])
    stability = {
        feature + '_psi': psi(df.loc[ref,feature],df.loc[cur,feature])
        for feature in ['utilization','dti','income_k','late_payments_12m']
    }
    stability.update({'predicted_pd_psi':psi(p[ref],p[cur]),
                      'reference_mean_utilization':float(df.loc[ref,'utilization'].mean()),
                      'current_mean_utilization':float(df.loc[cur,'utilization'].mean())})
    # Explicitly fictional grouping. Diagnostic tests the code path only; NOT a real fairness audit.
    groups = {}
    for group in sorted(df.simulated_audit_group.unique()):
        mask = (df.simulated_audit_group == group).to_numpy()
        groups[str(group)] = _metrics(y[mask],p[mask])
        groups[str(group)]['group_is_fictional'] = True
    gkeys = list(groups)
    diagnostic_gaps = {}
    for attr in ['tpr','fpr','brier','mean_predicted_pd']:
        vals=[groups[k][attr] for k in gkeys]
        diagnostic_gaps[attr+'_max_min_gap'] = float(max(vals)-min(vals)) if vals and all(x is not None for x in vals) else None
    flags = []
    if overall['auc'] is not None and overall['auc'] < .70:
        flags.append({'severity':'REVIEW','check':'low_synthetic_auc', 'reason':'AUC < 0.70 heuristic, not EXL or bank threshold'})
    if stability['utilization_psi'] is not None and stability['utilization_psi'] > .25:
        flags.append({'severity':'REVIEW','check':'utilization_shift','reason':'PSI > .25 exploratory heuristic, not a bank policy'})
    if abs(overall['prevalence'] - overall['mean_predicted_pd']) > .05:
        flags.append({'severity':'REVIEW','check':'calibration_gap','reason':'Observed vs predicted mean differs >5pp synthetic heuristic'})
    flags.append({'severity':'LIMITATION','check':'fictional_groups',
                  'reason':'SIM_A/SIM_B are randomly assigned and NOT protected traits; no fairness conclusion possible'})
    return {
        'provenance':{
            'synthetic_only':True,'assumed_coefficients':True,'seed':2026,
            'n':len(df),'n_reference':int(ref.sum()),'n_current':int(cur.sum()),
            'scenario_only':True,'review_thresholds_not_approved':True,
        },
        'performance':{'overall':overall,'reference':ref_m,'current':cur_m},
        'stability':stability,
        'fairness_method_demonstration':{
            'disclaimer':'SIM_A/SIM_B are arbitrary fictional labels (NOT protected groups). Disparities are NOT an actual fairness audit.',
            'groups':groups,'diagnostic_gaps':diagnostic_gaps,'classification_threshold':.18,
            'additional_data_needed':'lawful, representative protected-group data, decision policies, observed outcomes and qualified independent reviewers',
        },
        'review_flags':flags,
        'final_approval':'NOT APPROVED: demonstration and human review only',
    }
