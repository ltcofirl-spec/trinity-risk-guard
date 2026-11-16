"""One-command local/Colab demo. Never fabricate R reference or LLM calls."""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from generate_data import make_data
from validate_parity import compare
from run_demo import run
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def execute(with_agent=False, require_r=False):
    OUT.mkdir(exist_ok=True)
    data=ROOT/'synthetic_credit_data.csv'
    rsrc=ROOT/'models/legacy_credit_score.R'
    rfile=OUT/'legacy_R_predictions.csv'
    parity_evidence=OUT/'parity_report.json'
    for stale in [rfile,parity_evidence,OUT/'parity_comparison.csv',OUT/'r_execution_provenance.json',
                  OUT/'agent_status.json',OUT/'agent_trace.json',OUT/'agent_documentation_draft.json']:
        stale.unlink(missing_ok=True)
    make_data(1600,2026).to_csv(data,index=False)
    print('Generated synthetic data (1600 cases).')
    rscript=shutil.which('Rscript')
    status={'status':'NOT_RUN','reason':'Rscript not available. Install base R in Colab/local and rerun pipeline.'}
    if rscript:
        command=[rscript,str(rsrc),str(data),str(rfile)]
        # Capturing stdout and stderr avoids accidental false proof; nonzero is failure.
        p=subprocess.run(command,capture_output=True,text=True,timeout=90,check=False)
        record={'executed_utc':datetime.now(timezone.utc).isoformat(),
                'executable':rscript,'command':['Rscript','models/legacy_credit_score.R',
                                                'synthetic_credit_data.csv','outputs/legacy_R_predictions.csv'],
                'returncode':p.returncode,'stdout':p.stdout[-3000:], 'stderr':p.stderr[-3000:],
                'r_source_sha256':sha(rsrc),'input_data_sha256':sha(data)}
        if p.returncode!=0 or not rfile.exists():
            status={'status':'FAIL','reason':'Rscript execution failed; see outputs/r_execution_provenance.json'}
        else:
            record['r_output_sha256']=sha(rfile)
            try:
                result=compare(r_csv=rfile,data_csv=data)
                status=result
                status['r_source_sha256']=record['r_source_sha256']
                status['input_data_sha256']=record['input_data_sha256']
                status['r_output_sha256']=record['r_output_sha256']
                parity_evidence.write_text(json.dumps(status,indent=2),encoding='utf-8')
            except Exception as ex:
                status={'status':'FAIL','reason':str(ex)}
            record['parity_status']=status['status']
        (OUT/'r_execution_provenance.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    else:
        print('Rscript not installed: cross-language parity remains NOT_RUN (not PASS).')
        if require_r:
            run(parity_status=status)
            raise RuntimeError('Cross-language evidence required, but Rscript unavailable')
    if status['status']=='FAIL':
        run(parity_status=status)
        raise RuntimeError('R parity FAILED: '+status.get('reason','see outputs'))
    result=run(parity_status=status)
    if with_agent:
        from documentation_agent import run_agent
        outcome=run_agent()
        print('LLM documentation Agent:',outcome['status'])
        result=run(parity_status=status)  # refresh report with actual LLM status
    print('Pipeline complete; parity status:', status['status'])
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--agent',action='store_true',help='Run actual model tool-calling; requires credentials')
    parser.add_argument('--require-r',action='store_true',help='Fail if Rscript unavailable')
    args=parser.parse_args()
    try:execute(with_agent=args.agent,require_r=args.require_r)
    except Exception as exc:
        print('ERROR:',str(exc),file=sys.stderr)
        raise SystemExit(1)
