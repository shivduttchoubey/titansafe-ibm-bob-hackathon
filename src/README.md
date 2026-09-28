# Source Code

All TitanSafe source code lives in the `TitanSafe/` package at the repo root.

## Package layout

```
TitanSafe/              # Python package (importable as `TitanSafe`)
├── __init__.py
├── cli.py               # CLI: demo / verify / datasets subcommands
├── mock.py              # 4 named mock datasets with organic false-positive traps
├── detect.py            # CIB detection (union-find + burst/similarity/youth signals)
├── classify.py          # Phrase-weighted threat classifier (incitement/harassment/misinfo)
├── abstraction.py       # Vault: T0/T1/T2 disclosure, pseudonyms, ZK proofs, Merkle tree
├── workflow.py          # Case lifecycle: request loop, policy dispatch, retention
├── policy.py            # DPDP-aligned gate checks (purpose, legal basis, approvers)
├── audit.py             # Tamper-evident SHA-256 hash-chained audit log
├── legal.py             # Indicative IPC → BNS mapping + BNSS/IT-Act process references
├── brief.py             # Threat brief generator (Markdown + JSON, LEA view only)
├── dashboard.py         # Single-page scrollable HTML dashboard
├── pdf.py               # Print-ready A4 HTML report
└── zt/                  # Zero-knowledge crypto primitives (from QBOM-ZT)
    ├── ec.py            # NIST P-256 curve arithmetic
    ├── zk.py            # Pedersen commitments, Schnorr range/linkage proofs
    └── merkle.py        # Sorted Merkle tree + inclusion proofs
```

## Running from source

```bash
# From the repo root
pip install -e .
python -m TitanSafe.cli demo --out out --pdf
python -m TitanSafe.cli verify out
pytest tests/ -v
```

## No `.env` required

TitanSafe has zero runtime dependencies and no required environment variables.
All cryptographic keys are generated in-memory per run.
See `.env.example` if you want to extend the system to use IBM watsonx.ai or a database.
