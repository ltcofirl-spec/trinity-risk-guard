"""Strict CSV comparison engine; by itself CANNOT certify R provenance.

Use run_pipeline.py for actual Rscript execution, file hashes, and provenance.
Never create fake R predictions from Python to claim cross-language parity.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scorecard_port import score_frame, VERSION

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'

def compare(r_csv=None, data_csv=None, tol=1e-10, write_outputs=True):
    r_csv=Path(r_csv) if r_csv is not None else OUT/'legacy_R_predictions.csv'
    data_csv=Path(data_csv) if data_csv is not None else ROOT/'synthetic_credit_data.csv'
    if not r_csv.is_file():
        raise FileNotFoundError('Real R output not found. First run: Rscript models/legacy_credit_score.R synthetic_credit_data.csv outputs/legacy_R_predictions.csv')
    data=pd.read_csv(data_csv,dtype={'customer_id':str})
    r=pd.read_csv(r_csv,dtype={'customer_id':str})
    expected={'customer_id','r_probability','r_risk_band','model_version'}
    if not expected.issubset(r.columns):
        raise ValueError('R reference CSV missing required columns: '+repr(sorted(expected-set(r.columns))))
    py=score_frame(data)
    if r['customer_id'].isna().any() or r['customer_id'].duplicated().any():
        raise ValueError('R references contain duplicate/missing IDs')
    if len(r)!=len(data) or set(r.customer_id)!=set(data.customer_id):
        raise ValueError('R and Python data contain different sets of IDs or counts')
    merged=py.merge(r,on='customer_id',how='inner',validate='one_to_one',suffixes=('_python','_r'))
    if len(merged)!=len(data):raise AssertionError('Not all cases matched')
    if merged['r_probability'].isna().any() or (~np.isfinite(merged['r_probability'])).any():
        raise ValueError('R output probabilities contain invalid numbers')
    delta=np.abs(merged['python_probability']-merged['r_probability'])
    version_ok=bool((merged['model_version_python']==VERSION).all() and (merged['model_version_r']==VERSION).all())
    band_ok=bool((merged['python_risk_band']==merged['r_risk_band']).all())
    prob_ok=bool((delta<=tol).all())
    report={
        'status':'PASS' if prob_ok and band_ok and version_ok else 'FAIL',
        'source':'CSV comparison only; independently executed Rscript provenance is recorded only by run_pipeline.py',
        'r_reference_file':str(r_csv.name),
        'n_rows':int(len(merged)),
        'tolerance':tol,
        'max_abs_difference':float(delta.max()),
        'mean_abs_difference':float(delta.mean()),
        'probabilities_within_tolerance':prob_ok,
        'risk_bands_equal':band_ok,
        'model_version_equal':version_ok,
    }
    if write_outputs:
        OUT.mkdir(exist_ok=True)
        (OUT/'parity_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        merged.assign(abs_difference=delta).to_csv(OUT/'parity_comparison.csv',index=False,float_format='%.17g')
    return report

if __name__=='__main__':
    rpt=compare()
    print(json.dumps(rpt,indent=2))
    if rpt['status']!='PASS':
        raise SystemExit('PARITY FAIL: examine outputs/parity_comparison.csv')
