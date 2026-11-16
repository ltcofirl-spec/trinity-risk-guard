import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generate_data import make_data
from scorecard_port import predict_probability, score_frame, COEFFICIENTS, VERSION, classify_risk
from validate_parity import compare

def test_equal_periods_and_reproducibility():
    a,b=make_data(200,2026),make_data(200,2026)
    pd.testing.assert_frame_equal(a,b)
    assert (a.period=='reference').sum()==100
    assert (a.period=='current').sum()==100

def test_scoring_in_bounds_and_monotonicity():
    df=make_data(200)
    p=predict_probability(df)
    assert np.isfinite(p).all() and ((p>0)&(p<1)).all()
    bigger=df.copy()
    bigger['utilization']=np.minimum(.99,bigger['utilization']+.01)
    assert (predict_probability(bigger)>p).all()

def test_fixed_baseline_odds_and_risk_bands():
    ref=pd.DataFrame([{'utilization':.30,'dti':.32,'income_k':50.,'late_payments_12m':0}])
    z=-2.98+1.65*.30+1.13*.32-.0041*50
    p=float(predict_probability(ref)[0])
    assert p==pytest.approx(1/(1+np.exp(-z)),rel=1e-13)
    assert .085<p<.095
    assert list(classify_risk(np.array([.0799999,.08,.18])))==['LOW','MEDIUM','HIGH']

def test_reject_bad_inputs():
    df=make_data(100)
    bad=df.copy();bad.loc[0,'dti']=np.nan
    with pytest.raises(ValueError):predict_probability(bad)
    bad=df.copy();bad.loc[1,'late_payments_12m']=10
    with pytest.raises(ValueError):predict_probability(bad)
    bad=df.copy();bad.loc[0,'customer_id']=bad.loc[1,'customer_id']
    with pytest.raises(ValueError):predict_probability(bad)

def test_python_outputs_have_unique_ids_and_versions():
    scored=score_frame(make_data(200))
    assert scored.customer_id.is_unique
    assert (scored.model_version==VERSION).all()

def test_parity_fails_closed_without_r_output(tmp_path):
    with pytest.raises(FileNotFoundError):compare(r_csv=tmp_path/'nonexistent.csv',write_outputs=False)

def test_parity_rejects_fake_or_malformed_reference(tmp_path):
    df=make_data(100)
    data_csv=tmp_path/'data.csv'; df.to_csv(data_csv,index=False)
    r_csv=tmp_path/'reference.csv'
    pd.DataFrame({'customer_id':df.customer_id[:99], 'r_probability':np.zeros(99),
                  'r_risk_band':['LOW']*99,'model_version':[VERSION]*99}).to_csv(r_csv,index=False)
    with pytest.raises(ValueError):compare(r_csv=r_csv,data_csv=data_csv,write_outputs=False)
