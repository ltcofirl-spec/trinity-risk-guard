# Trinity Risk Guard — EXL × Trinity Challenge 04

**Agentic Model Risk Factory | Technical Review Package v3 | 13 November 2026**

> **Not an official EXL model or real customer data.** Source models, coefficients, simulated credit records and labels were created for this hackathon with ChatGPT assistance; the team must independently review them. **Trinity Risk Guard** is a self-chosen team project name, not an EXL/TCD endorsed product.

## What is implemented?

| EXL task | Demonstration evidence | Current status (in distributed ZIP) |
|---|---|---|
| 1. Inventory of 3–5 models | `models/model_inventory.json`: credit, fraud, pricing; real tool-calling Documentation Agent source | Inventory **PREPARED**, real Agent **NOT RUN** |
| 2. R/SAS → Python migration of ONE model + parity | Base-R scorecard, Python NumPy/Pandas port, 1600-record ID-matched validator, original R execution hashes in pipeline | Code **DONE**, true cross-language parity **NOT RUN** here (no Rscript) |
| 3. Automatic performance, stability and fairness report | AUC, AP, Brier, temporal PSI, illustrative fictional-group TPR/FPR, report + review flags | Synthetic performance/stability **RUN**; fictional-group *method demonstration only*, not real fairness certification |

## Quick setup (local or Colab)

Python 3.10+ and **Rscript** (base R) needed for *real* parity. No R packages are needed. `notebooks/Trinity_Risk_Guard_Colab.ipynb` includes installation and all steps in order.

```bash
python -m pip install -r requirements.txt
python run_pipeline.py
python -m pytest tests -q
```

`run_pipeline.py` regenerates synthetic data with `seed=2026`, looks up **the real Rscript binary**, executes R **as an independent process**, computes Python predictions, runs ID-linked reconciliation, records R source/data/output SHA256 and updates metrics. If Rscript is unavailable, it reports `NOT_RUN` rather than producing fake parity. If R exists but outputs differ it fails. To **require** R:

```bash
python run_pipeline.py --require-r
```

Expected review files:

- `outputs/parity_report.json`: **PASS only after actual R execution, all 1,600 rows matched, probabilities within 1e-10 and identical risk bands/version**. The report also stores SHA256 references.
- `outputs/r_execution_provenance.json`: R binary and execution return code, source and data hashes.
- `outputs/parity_comparison.csv`: per-row predicted probabilities and absolute difference.
- `outputs/metrics.json`: model validation results and documented limitations.
- `outputs/validation_report.md`: plain-English report with caveats and human review flags.
- `outputs/model_inventory.csv`, `outputs/audit_log.json`: model inventory and deterministic process log.

### Run the actual LLM tool-calling Agent

A Python `documentation_agent.py` is implemented. It is **not just a prompt**: the LLM must select approved tools to read inventory, read the **R** model source, inspect computed metrics, then submit a structured **DRAFT**. It cannot approve or deploy a model, run arbitrary commands, or access other files. It logs its chosen tools to `outputs/agent_trace.json` and the draft to `outputs/agent_documentation_draft.json` with `reviewer_decision=PENDING`.

For an OpenAI-compatible **hosted** endpoint:

```bash
export TRG_API_KEY="YOUR_OWN_API_KEY"  # do not commit the key
export TRG_MODEL="gpt-4.1-mini"        # or an available tool-calling model
python run_pipeline.py --agent
```

Or provide `TRG_BASE_URL=https://your-provider.example/v1` with your compatible key, or for a local tool-calling model, `TRG_BASE_URL=http://localhost:11434/v1` and `TRG_MODEL=YOUR_MODEL_NAME` (requires local server). Remote HTTP is rejected; only HTTPS remote or local HTTP is allowed. **The team must verify the provider actually supports `chat/completions` function/tool calling.** Keyed API usage may incur charges. Run `python documentation_agent.py` separately after `python run_pipeline.py` if you want only the Agent.

**No live LLM call was possible in the build environment.** Its 15 Python tests include a **simulated LLM tool-call unit test** for control flow, not a live result. `outputs/agent_status.json` and trace files are intentionally absent until a genuine Agent run. Missing credentials cause an explicit failure. Never describe the simulated test as a completed Agent run.

## Input and statistical assumptions

The legacy R source is `models/legacy_credit_score.R` (self-authored), with an identical port `scorecard_port.py`:

```
z = -2.98 + 1.65*utilization + 1.13*dti - 0.0041*income_k + 0.62*late_payments_12m
PD = 1/(1+exp(-z))
LOW <8%; MEDIUM 8–18%; HIGH ≥18%    (illustrative, not lending policy)
```

**Coefficients and cutoffs are assumed; they were not fitted or validated on real bank defaults.** `generate_data.py` makes 1,600 invented cases (800 reference, 800 current); two periods intentionally differ. `age_years_audit_only` and random `simulated_audit_group` **do not enter the score**. See `docs/MODEL_AND_TEST_EXPLANATION_CN.pdf` for full explanation.

### Validation interpretation

- `ROC-AUC`, Average Precision and `Brier` measure performance **only against synthetic generated labels**. Under the illustrative fixed scorecard, AUC is about **0.6295**, which is not strong predictive evidence for production.
- `PSI` measures designed shifts between simulated periods; thresholds are heuristics only.
- `SIM_A`/`SIM_B` are arbitrary labels, **not protected classes**. The group calculations demonstrate the fairness-testing *method*, not an actual fairness assessment. No legal, ethical or regulatory clearance can be inferred.
- **Cross-language parity ≠ model predictive validity.** Even perfect R/Python numerical parity would not validate model quality.

## Reproducibility and team review

1. One member with R installed runs `python run_pipeline.py --require-r`, archives the parity/provenance output and checks `status=PASS`, `n_rows=1600`.
2. A member configures a real model provider then runs `python documentation_agent.py`, checks the trace contains `read_model_source`, `get_validation_evidence` and `submit_documentation_draft` and reviews every generated claim.
3. Review metrics and their synthetic limits; do **not** represent AUC, time savings or fairness as real banking performance.
4. Use `notebooks/Trinity_Risk_Guard_Colab.ipynb` for a shareable Colab walkthrough and live demo.
5. Edit slides, architecture diagram, Responsible AI note and video **only after actual evidence exists**. These are separate official submission artifacts and are not duplicated in this technical-only ZIP.

## Repository structure

- `models/`: three invented models; only CRD-001 uses legacy R. Inventory includes authorship disclaimer.
- `generate_data.py`, `synthetic_credit_data.csv`: 1600 reproducible invented credit scenarios.
- `scorecard_port.py`: independent Python score port.
- `validate_parity.py`: strict CSV comparator (without R provenance it is **not** evidence); `run_pipeline.py` executes R and hashes inputs.
- `validation_engine.py`, `run_demo.py`: deterministic metrics and human-review flags.
- `documentation_agent.py`: true LLM function-calling agent source, pending live invocation.
- `tests/`: 15 offline unit tests (including deliberately fake comparator / agent fixtures, **never** submitted as live proof).
- `outputs/`: current verified Python metrics and status `NOT_RUN` for parity/LLM until real execution.
- `docs/`: group guide, assumptions, exact commands and review checklist.

## Governance and AI disclosure

All source code and explanatory materials have been generated/revised using ChatGPT (GPT-6) and require review before submission. No bank customer data or genuine model was accessed. Never enter sensitive records or private credentials into public Colab notebooks or LLM messages. Model documentation remains draft until a human reviewer signs off. Model use for real credit decisions is prohibited.

**Challenge source:** EXL × Trinity Hackathon 2026, Challenge 04, page 9; official submission requirements, page 13. Project name and model definitions are the team's own.
