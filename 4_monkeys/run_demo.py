"""Refresh synthetic data & validation evidence; no fabricated R/LLM status."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from generate_data import make_data
from scorecard_port import score_frame
from validation_engine import evaluate
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'


def run(parity_status=None):
    OUT.mkdir(exist_ok=True)
    df=make_data(n=1600,seed=2026)
    df.to_csv(ROOT/'synthetic_credit_data.csv',index=False)
    scored=score_frame(df)
    m=evaluate(df,scored.python_probability.to_numpy())
    m['model_version']=str(scored.model_version.iloc[0])
    inv=json.loads((ROOT/'models/model_inventory.json').read_text(encoding='utf-8'))
    pd.DataFrame(inv).to_csv(OUT/'model_inventory.csv',index=False)
    if parity_status is None:
        evidence=OUT/'parity_report.json'
        if evidence.exists():
            p=json.loads(evidence.read_text(encoding='utf-8'))
            # A prior result could be stale; don't silently promote it to a current success.
            parity_status={'status':'NOT_VERIFIED_THIS_RUN','historical_report':p.get('status')}
        else:
            parity_status={'status':'NOT_RUN','reason':'No independently executed R reference in this run'}
    m['cross_language_parity']=parity_status
    agent_status=OUT/'agent_status.json'
    m['llm_agent']=(json.loads(agent_status.read_text(encoding='utf-8')) if agent_status.exists()
                     else {'status':'NOT_RUN','reason':'LLM tool-calling requires API configuration and a live run'})
    (OUT/'metrics.json').write_text(json.dumps(m,indent=2,ensure_ascii=False),encoding='utf-8')
    logs=[{'step':'inventory','status':'PREPARED','detail':'3 authored simulation records; automatic LLM extraction depends on Agent run'},
          {'step':'python_score','status':'DONE','detail':'Fixed illustrative logistic scorecard'},
          {'step':'parity','status':parity_status.get('status'),'detail':'Real Rscript reference required for PASS'},
          {'step':'validation','status':'DONE','detail':'Synthetic performance/stability and fictional group diagnostics'},
          {'step':'approval','status':'HUMAN_REVIEW_REQUIRED','detail':'No production or regulatory sign-off'}]
    (OUT/'audit_log.json').write_text(json.dumps(logs,indent=2,ensure_ascii=False),encoding='utf-8')
    perf=m['performance']['overall']; stability=m['stability']
    lines=[
        '# Trinity Risk Guard — Model Validation Evidence (Synthetic Demo)',
        '> NOT independent validation, model approval, EXL sample data or real banking evidence.',
        '', '## Data and documentation',
        '- 3 author-generated model inventory entries (Credit / Fraud / Pricing); only Credit migrated.',
        '- 1,600 fabricated loan records, seed 2026, 800 reference and 800 current.',
        '- Four coefficients and risk bands are disclosed scenario assumptions, not fitted or approved.',
        '', '## R → Python migration',
        '- **Current parity status:** '+parity_status.get('status','UNKNOWN'),
        '- A PASS requires actual Rscript execution and 1,600 matched IDs and probabilities/bands.',
        '', '## Predictive performance (synthetic labels)',
        f'- ROC-AUC: {perf["auc"]:.4f}' if perf['auc'] is not None else '- ROC-AUC: undefined',
        f'- Average Precision: {perf["average_precision"]:.4f}' if perf['average_precision'] is not None else '- Average Precision: undefined',
        f'- Brier score: {perf["brier"]:.4f}',
        f'- Observed default rate: {perf["prevalence"]:.2%}; mean predicted PD: {perf["mean_predicted_pd"]:.2%}',
        f'- AUC reference: {m["performance"]["reference"]["auc"]:.4f}; current: {m["performance"]["current"]["auc"]:.4f}',
        '', '## Stability (two designed simulation periods)',
        *[f'- {k}: {v:.4f}' if v is not None else f'- {k}: unavailable' for k,v in stability.items() if k.endswith('_psi')],
        '', '## Fairness diagnostics (NOT a real fairness audit)',
        '- Fictional labels SIM_A and SIM_B are random group identifiers, not protected traits.',
        '- TPR, FPR, Brier and predicted-PD gaps illustrate validation methodology only.',
        '- No real-world fairness conclusion is possible; representative protected-group information and independent review are needed.',
        '', '## Automatic review flags',
        *[f'- {x["severity"]}: {x["check"]} — {x["reason"]}' for x in m['review_flags']],
        '', '## Governance',
        '- Human review required before accepting any documentation or migration as validated.',
        '- Parity does NOT prove statistical validity; synthetic testing does NOT establish regulatory compliance.',
        '- LLM Agent status: '+str(m['llm_agent'].get('status')),
    ]
    (OUT/'validation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Saved outputs/metrics.json and outputs/validation_report.md')
    print('AUC=',round(perf['auc'],4),'Brier=',round(perf['brier'],4),'Parity=',parity_status.get('status'))
    return m

if __name__=='__main__':run()
