# Trinity Risk Guard

**Team 4 Monkeys · EXL × Trinity Data & AI Hackathon 2026 · Challenge 04: Agentic model risk factory**

We built a working slice of an agentic model-risk factory: it inventories a bank's models, rebuilds one of them from R into Python with a parity proof, and drafts a validation report on performance, stability and fairness. The point is to take the 8–12 week manual validation cycle and turn the first pass into something that takes minutes, with a human still holding the pen.

Everything here runs on synthetic data we generated ourselves. There is no EXL client data, no real customer record, and nothing in this repo is approved for a credit decision.

---

## The problem we picked

A Tier-1 UK bank runs around 250 credit, fraud and pricing models built in SAS, R and Python. Under PRA SS1/23 each one needs current documentation and independent validation. In practice the documentation drifts out of date, a single validation takes 8–12 weeks, and the backlog grows faster than a team can clear it.

EXL's brief for Challenge 04 is concrete:

1. Document 3–5 sample models and build their inventory records.
2. Rebuild one SAS or R model in Python, with a parity proof.
3. Auto-generate a validation report covering performance, stability and fairness.

That is exactly the shape of this repository.

## What we built

| EXL ask | What's in this repo | Where it stands |
|---|---|---|
| Document 3–5 models and build inventory | 3 models in `models/model_inventory.json` — credit `CRD-001` (R), fraud `FRD-002`, pricing `PRC-003` — plus `documentation_agent.py`, a real tool-calling agent that reads them and drafts the documentation | Inventory: 3 records, written by hand. Agent: code complete, live run **not done** |
| Rebuild one R model in Python with parity proof | `models/legacy_credit_score.R` run as a separate process, `scorecard_port.py` as the Python port, `validate_parity.py` matching all 1,600 records by ID | Code: done. Real cross-language run: **NOT_RUN** — no `Rscript` on the build machine |
| Auto-generate a validation report | `validation_engine.py` writes `outputs/metrics.json` and `outputs/validation_report.md`: AUC / AP / Brier, PSI stability, group diagnostics, review flags | **Run** on synthetic data. The fairness part is a method demonstration only |

EXL also suggested a five-stage flow — discover, document, redevelop, validate, monitor. We only claim the stages we have code and output for:

| Stage | Here | Status |
|---|---|---|
| Discover | model inventory JSON, agent `list_inventory` tool | partial, done by hand |
| Document | `documentation_agent.py`: methodology, inputs, limitations, human-review questions | code ready, live run pending |
| Redevelop | R source → Python port → strict row-by-row comparator | done |
| Validate | metrics, stability, fictional-group diagnostics, review flags | done on synthetic data |
| Monitor | not built | see "What we would do next" |

## The part we want to be judged on: we don't fake a PASS

Most demos in this space quietly ship a green tick. We went the other way, because a model risk tool that lies about its own evidence is useless to a bank.

`run_pipeline.py` deletes stale parity artefacts before every run, looks up the real `Rscript` binary, executes the R file as an independent process against the generated CSV, and records its return code plus SHA256 hashes of source, input and output. No R installed means the status is `NOT_RUN`, not `PASS`. R installed but rows disagree means `FAIL` and a non-zero exit. The same rule applies to the agent: no credentials, no trace file, and the script fails loudly instead of inventing a call.

`outputs/parity_report.json` and `outputs/agent_trace.json` are therefore deliberately absent — they only appear after a genuine run, and we have not had one yet.

## Run it

```bash
python -m pip install -r requirements.txt
python run_pipeline.py        # data, Python score, metrics, report
python -m pytest tests -q     # 15 tests, all offline
```

You should see `AUC= 0.6295 Brier= 0.1039 Parity= NOT_RUN`, and `outputs/` fills with `metrics.json`, `validation_report.md`, `model_inventory.csv` and `audit_log.json`.

To attempt the parity run — the one that turns `NOT_RUN` into `PASS` — you need base R (no R packages):

```bash
python run_pipeline.py --require-r
```

`PASS` means all 1,600 IDs matched, predicted probabilities within `1e-10`, and identical risk bands and model version. If `Rscript` is missing the pipeline stops and tells you, rather than quietly producing a Python-only "reference".

To run the documentation agent you need a real OpenAI-compatible endpoint:

```bash
export TRG_API_KEY="your-key"        # never commit this
export TRG_MODEL="gpt-4.1-mini"
python documentation_agent.py
```

For a local model, set `TRG_BASE_URL=http://localhost:11434/v1` with your Ollama model name. Only HTTPS remotes or local HTTP are accepted, and the provider must genuinely support tool calling — the agent needs it, it is not a prompt in a trench coat.

## Reading the numbers

- **Performance:** AUC 0.6295, AP 0.1983, Brier 0.1039 over 1,600 synthetic cases (194 defaults, 12.1%).
- That AUC is weak, and it is weak by construction: the scorecard is a fixed formula we wrote rather than a fitted model, so the labels only partly track it. We report it anyway — a hidden mediocre number is worse than a visible one.
- **Stability:** PSI 0.269 utilisation, 0.146 DTI, 0.032 income, 0.008 late payments, 0.234 on predicted PD. The two simulated periods were designed to differ, so this shows the PSI machinery works; it does not mean any real book is drifting.
- **Fairness:** `SIM_A` and `SIM_B` are randomly assigned labels, not protected traits. The TPR / FPR gaps demonstrate the testing method and nothing else. A real fairness assessment needs lawful representative data, decision policies and independent review.
- **Parity is not quality.** Matching R to ten decimal places proves the migration is faithful. It says nothing about whether the model is any good.

## Data, privacy and Responsible AI

- **Data:** all 1,600 records come from `generate_data.py` (seed 2026), split 800 reference / 800 current. Invented customers, no personal data, no client data. `synthetic_credit_data.csv` is the shipped copy.
- **Coefficients are assumptions**, not fitted estimates: `z = -2.98 + 1.65·utilisation + 1.13·DTI − 0.0041·income_k + 0.62·late_payments_12m`, `PD = 1/(1+e^(−z))`, bands at 8% and 18%. They encode plausible odds ratios, nothing more.
- `age_years_audit_only` and `simulated_audit_group` never enter the score. They exist to prove the pipeline carries sensitive fields through without using them.
- **Agent safeguards:** only four read-only allowlisted tools; the model cannot approve, retrain, deploy or execute generated code; its output is a structured DRAFT whose reviewer decision stays `PENDING`; source comments are treated as data, not instructions.
- **AI tools used, declared:** code and documentation were drafted with ChatGPT assistance, and one offline documentation draft was generated with Ollama `qwen2.5:7b` (`outputs/llm_doc_proposal.json`) — a single generation, not the tool-calling agent flow. The base-R scorecard and its Python port are our own code; no licensed third-party model code is included.
- **Scope:** demonstration and human review only. Not approved for credit decisions, not regulatory sign-off, not an EXL-endorsed product.

## Repo map

```
run_pipeline.py            one command: data → score → metrics → report, with R parity when available
documentation_agent.py     LLM tool-calling agent that drafts model documentation for review
validation_engine.py       metrics, PSI, group diagnostics, review flags
validate_parity.py         strict comparator for R vs Python predictions
scorecard_port.py          Python port of the R scorecard
generate_data.py           seeded synthetic dataset (1,600 cases)
run_demo.py                runs the validation pass and writes the report
models/                    three illustrative models + inventory JSON
outputs/                   metrics, validation report, inventory CSV, audit log, one LLM draft
tests/                     15 offline tests (including a simulated tool-call control-flow test)
notebooks/                 Colab walkthrough for a shareable demo
docs/                      group guide, assumptions, review checklist
```

## What we would do next

1. Run `--require-r` on a machine with R and publish the real `PASS` artefact.
2. Point the agent at a real tool-calling model, review its draft line by line, then extend the flow to `FRD-002` and `PRC-003`.
3. Build the monitoring stage: drift tracking that triggers re-validation automatically.
4. Measure the business case properly — time to first draft and reviewer hours saved against the 8–12 week baseline. We have not measured that yet, so we are not claiming it.

## Submission pack

Per the official requirements, this repository is the code and reproducibility evidence. The solution deck, the ≤3 minute demo video, the one-page architecture diagram and the one-page Responsible AI note are submitted alongside it as separate materials.
