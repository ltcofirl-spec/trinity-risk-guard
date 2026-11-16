"""Offline unit tests: no real LLM call and no claim of R parity."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generate_data import make_data
from scorecard_port import predict_probability, score_frame
from validation_engine import evaluate, psi
from validate_parity import compare
from documentation_agent import run_agent, tool_executor


def test_full_metrics_schema_and_synthetic_disclosure():
    d=make_data(200,2026)
    metrics=evaluate(d,predict_probability(d))
    assert metrics['provenance']['synthetic_only'] is True
    assert len(metrics['fairness_method_demonstration']['groups'])==2
    assert 'NOT an actual fairness audit' in metrics['fairness_method_demonstration']['disclaimer']
    assert 'predicted_pd_psi' in metrics['stability']
    assert metrics['performance']['overall']['n']==200


def test_psi_same_distribution_zero():
    a=np.linspace(.01,.95,100)
    assert abs(psi(a,a)) < 1e-10


def test_psi_invalid_and_constant_handled():
    assert psi(np.ones(20),np.ones(20)) is None
    with pytest.raises(ValueError):psi(np.array([np.nan]),np.array([1]))


def test_parity_detects_probability_and_band_error(tmp_path):
    d=make_data(100,2026)
    csv=tmp_path/'data.csv'; d.to_csv(csv,index=False)
    scored=score_frame(d)
    # Fabricated REFERENCE FOR TESTING THE COMPARATOR ONLY, NOT R evidence.
    r=scored.rename(columns={'python_probability':'r_probability','python_risk_band':'r_risk_band'})
    r.loc[0,'r_probability']+=.02
    r.loc[1,'r_risk_band']='WRONG'
    rcsv=tmp_path/'fixture.csv';r.to_csv(rcsv,index=False)
    report=compare(rcsv,csv,write_outputs=False)
    assert report['status']=='FAIL'
    assert report['probabilities_within_tolerance'] is False
    assert report['risk_bands_equal'] is False


def test_strict_tool_access_blocks_other_models():
    with pytest.raises(ValueError):tool_executor('read_model_source',{'model_id':'FRD-002'},{},'CRD-001')
    with pytest.raises(ValueError):tool_executor('unknown_tool',{}, {}, 'CRD-001')


def test_agent_no_credentials_fails_closed(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.delenv('TRG_API_KEY',raising=False)
    monkeypatch.delenv('TRG_BASE_URL',raising=False)
    with pytest.raises(RuntimeError,match='Agent NOT RUN'):
        run_agent()


def test_agent_tool_selection_and_human_review_gate_with_fake_llm(tmp_path,monkeypatch):
    # This is a FAKE MODEL UNIT TEST, not a successful real LLM run.
    import documentation_agent as da
    monkeypatch.setattr(da,'OUT',tmp_path)
    (tmp_path/'metrics.json').write_text(json.dumps({'provenance':{'synthetic_only':True}}))
    def call(name,args,i):
        return SimpleNamespace(id='call_'+str(i),function=SimpleNamespace(name=name,arguments=json.dumps(args)))
    draft={'model_id':'CRD-001','summary':'This scorecard estimates synthetic probability of default only.',
           'methodology':'A fixed-coefficient logistic model not trained on bank data.',
           'inputs':['utilization','dti','income_k','late_payments_12m'],
           'model_limitations':['Not calibrated','Synthetic only'],
           'validation_findings':['The metrics are synthetic; parity is not demonstrated here'],
           'human_review_questions':['Check assumed coefficients'],
           'evidence_files':['models/legacy_credit_score.R','outputs/metrics.json']}
    replies=[
      [call('list_inventory',{},1),call('read_model_source',{'model_id':'CRD-001'},2),call('get_validation_evidence',{},3)],
      [call('submit_documentation_draft',draft,4)]
    ]
    class Chat:
        def __init__(self):self.i=0
        def create(self,**kwargs):
            calls=replies[self.i];self.i+=1
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None,tool_calls=calls))])
    fake=SimpleNamespace(chat=SimpleNamespace(completions=Chat()))
    status=run_agent(client=fake,model='FAKE_UNIT_TEST_MODEL')
    assert status['status']=='SIMULATED_TEST_ONLY' # fake tool-calling fixture, never actual proof
    assert json.loads((tmp_path/'agent_documentation_draft.json').read_text())['reviewer_decision']=='PENDING'
    trace=json.loads((tmp_path/'agent_trace.json').read_text())
    assert len(trace['tool_events'])==4


def test_missing_rscript_does_not_mark_parity_pass(monkeypatch,tmp_path):
    import run_pipeline as rp
    import run_demo as demo
    import generate_data as gd
    import validate_parity as val
    # Run in an isolated project copy to avoid mutating pack outputs.
    import shutil
    for d in ['models','outputs']: (tmp_path/d).mkdir(exist_ok=True)
    shutil.copy(ROOT/'models/legacy_credit_score.R',tmp_path/'models/legacy_credit_score.R')
    shutil.copy(ROOT/'models/model_inventory.json',tmp_path/'models/model_inventory.json')
    monkeypatch.setattr(rp,'ROOT',tmp_path)
    monkeypatch.setattr(rp,'OUT',tmp_path/'outputs')
    monkeypatch.setattr(demo,'ROOT',tmp_path)
    monkeypatch.setattr(demo,'OUT',tmp_path/'outputs')
    monkeypatch.setattr(rp.shutil,'which',lambda _:'')
    result=rp.execute()
    assert result['cross_language_parity']['status']=='NOT_RUN'
