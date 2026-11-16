"""
ModelGuard — AI-Assisted Documentation Agent (Ollama Local Edition)
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

ALLOWLISTED_R_FILE = ROOT / "models" / "legacy_credit_score.R"
INVENTORY_FILE = ROOT / "models" / "model_inventory.json"

SYSTEM_INSTRUCTION = (
    "You are a model risk documentation assistant. Use only the supplied source code and metadata. "
    "Produce JSON with `model_name`, `inputs`, `outputs`, `methodology`, `assumptions`, `limitations`, "
    "`test_plan`, `unknowns`, and `evidence_lines`. Never invent model performance, owners or approvals. "
    "If facts are missing, write `unknown` and flag for review. Never execute code or suggest production promotion. "
    "Return valid JSON only."
)

REQUIRED_KEYS = [
    "model_name", "inputs", "outputs", "methodology",
    "assumptions", "limitations", "test_plan", "unknowns", "evidence_lines"
]

def deterministic_r_check(r_code: str) -> dict:
    extracted_vars = sorted(set(re.findall(r"df\$([a-zA-Z0-9_]+)", r_code)))
    formula_match = re.search(r"z\s*<-\s*(.+?)\n\s*1\s*/", r_code, re.DOTALL)
    formula_str = " ".join(formula_match.group(1).split()) if formula_match else "unknown"
    return {
        "deterministic_inputs": extracted_vars,
        "deterministic_formula": formula_str,
        "expected_coefficients": ["-2.6", "2.5", "1.6", "-0.010", "0.004", "45"]
    }

def run_documentation_agent(model_name: str = "qwen2.5:7b") -> dict:
    if not ALLOWLISTED_R_FILE.exists():
        raise FileNotFoundError(f"Allowlisted R source missing: {ALLOWLISTED_R_FILE}")

    r_bytes = ALLOWLISTED_R_FILE.read_bytes()
    r_hash = hashlib.sha256(r_bytes).hexdigest()
    r_source_text = r_bytes.decode("utf-8")

    inventory_data = json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))
    crd_record = next((m for m in inventory_data if m["model_id"] == "CRD-001"), {})

    numbered_r_source = "\n".join(
        f"L{idx}: {line}" for idx, line in enumerate(r_source_text.splitlines(), start=1)
    )

    user_prompt = (
        f"Source File: models/legacy_credit_score.R (SHA-256: {r_hash})\n"
        f"Existing Inventory Metadata for CRD-001:\n{json.dumps(crd_record, indent=2)}\n\n"
        f"Numbered R Source Code:\n{numbered_r_source}\n\n"
        "Generate the structured model risk documentation and validation test plan JSON."
    )

    client = OpenAI(
        api_key="ollama-local-key",
        base_url="http://localhost:11434/v1"
    )

    response = client.chat.completions.create(
        model=model_name,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_output = response.choices[0].message.content
    proposal_json = json.loads(raw_output)

    missing_keys = [k for k in REQUIRED_KEYS if k not in proposal_json]
    if missing_keys:
        raise ValueError(f"Ollama output missing required schema keys: {missing_keys}")

    det_check = deterministic_r_check(r_source_text)
    llm_inputs_str = json.dumps(proposal_json.get("inputs", [])).lower()
    recovered_vars = [v for v in det_check["deterministic_inputs"] if v.lower() in llm_inputs_str]
    recall_rate = len(recovered_vars) / len(det_check["deterministic_inputs"])

    methodology_str = json.dumps(proposal_json.get("methodology", ""))
    matched_coeffs = [c for c in det_check["expected_coefficients"] if c in methodology_str]

    verification_result = {
        "input_variable_recall": f"{len(recovered_vars)}/{len(det_check['deterministic_inputs'])} ({recall_rate*100:.0f}%)",
        "recovered_variables": recovered_vars,
        "matched_coefficients": matched_coeffs,
        "deterministic_reference_formula": det_check["deterministic_formula"],
        "verification_status": "PASS" if recall_rate == 1.0 else "NEEDS_REVIEW"
    }

    timestamp = datetime.now(timezone.utc).isoformat()
    audit_package = {
        "governance_status": "HUMAN-REVIEW-REQUIRED",
        "auto_overwrite_inventory": False,
        "production_promotion_allowed": False,
        "timestamp_utc": timestamp,
        "llm_provider": "Ollama (Local)",
        "llm_provider_model": model_name,
        "remote_api_used": False,
        "source_file": "models/legacy_credit_score.R",
        "source_sha256": r_hash,
        "independent_verification": verification_result,
        "proposed_inventory_and_test_plan": proposal_json,
    }

    out_file = OUT / "llm_doc_proposal.json"
    out_file.write_text(json.dumps(audit_package, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Governance Gate] Status: {audit_package['governance_status']}")
    print(f"[Verification] Input Recall: {verification_result['input_variable_recall']}")
    print(f"[Saved] {out_file}")
    return audit_package

if __name__ == "__main__":
    run_documentation_agent()