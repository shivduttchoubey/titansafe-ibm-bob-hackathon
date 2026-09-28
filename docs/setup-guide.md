# Setup Guide

> **This file is read by the automated evaluation pipeline. Follow these steps exactly.**

## Prerequisites

- [ ] Python 3.10 or higher (`python --version`)
- [ ] pip (`pip --version`)
- [ ] pytest for running the test suite (`pip install pytest`)
- [ ] A modern browser (Chrome, Firefox, Edge) to view the dashboard and PDF report
- [ ] **No IBM Cloud account required** — TitanSafe is zero-dependency, pure Python

## Environment Variables

TitanSafe has **no required environment variables** — all cryptographic keys are
generated in-memory per run (as they would be on a real platform).

There is no `.env` file needed to run the demo or tests.

If you wish to integrate the detection or ZK modules into a larger system that uses
IBM watsonx.ai or a database, copy and adapt `src/.env.example`:

```bash
cp src/.env.example .env
# Edit .env with your values
```

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/[your-org]/TitanSafe.git
cd TitanSafe

# 2. Install the package in editable mode (no external deps — installs only pytest extras)
pip install -e ".[dev]"

# --- OR --- install only the runtime (no test deps)
pip install -e .
```

> **Note:** `pyproject.toml` declares zero runtime dependencies.
> The only optional dependency is `pytest` for the test suite.

## Running the Demo

```bash
# Run the default dataset (incitement + harassment + misinfo)
python -m TitanSafe.cli demo --out out

# Also generate the A4 print-ready PDF report
python -m TitanSafe.cli demo --out out --pdf

# Verify all ZK proofs, Merkle anchors, identity bindings and audit chain
python -m TitanSafe.cli verify out
```

Open `out/dashboard.html` in any browser for the full LEA dashboard.
Open `out/threat_report.html` in any browser and use **Print → Save as PDF**.

## Mock Datasets

```bash
# List all available datasets
python -m TitanSafe.cli datasets

# Election day misinformation (EVM tampering + voter suppression)
python -m TitanSafe.cli demo --dataset election_disinfo --out out_election --pdf

# Communal riot incitement (imminent weapons + religious misinfo)
python -m TitanSafe.cli demo --dataset communal_riot --out out_riot --pdf

# Journalist doxxing (address/phone leak + brigading campaign)
python -m TitanSafe.cli demo --dataset journalist_doxxing --out out_doxxing --pdf

# Override random seed for reproducibility
python -m TitanSafe.cli demo --dataset default --seed 42
```

## Running Tests

```bash
# Full test suite (6 tests, ~30 s — pure-Python EC proofs are slow by design)
pytest tests/ -v

# Quick smoke test
pytest tests/test_TitanSafe.py::test_demo_end_to_end -v
```

Expected output: `6 passed` with no warnings.

## Output Files Reference

After running `demo`, the output directory contains:

| File | Description |
|---|---|
| `dashboard.html` | Single-page scrollable LEA dashboard — open in browser |
| `threat_report.html` | A4 print-ready PDF report — open in browser, use Print → Save as PDF |
| `threat_brief.md` | Markdown threat brief with escalation steps and BNS legal provisions |
| `attestation.json` | Public T0: Merkle root, cluster metadata, ZK proofs (no personal data) |
| `tier1_evidence.json` | T1 pseudonymous redacted evidence with Merkle inclusion proofs |
| `tier2_identities.json` | T2 real identities revealed under simulated court order |
| `audit.json` | Tamper-evident hash-chained audit log |
| `requests.json` | All disclosure requests with approval/denial decisions |
| `threat_brief.json` | Machine-readable threat brief |

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'TitanSafe'` | Run `pip install -e .` from the repo root |
| `UnicodeEncodeError` on Windows | Ensure your terminal uses UTF-8: `chcp 65001` in cmd, or use PowerShell |
| Tests timeout | The EC proofs are intentionally slow in pure Python — this is expected (~30 s) |
| Dashboard shows blank page | Open `dashboard.html` directly in browser (file://) — no server needed |
| `python -m TitanSafe demo` fails | Use `python -m TitanSafe.cli demo` (note the `.cli` suffix) |
