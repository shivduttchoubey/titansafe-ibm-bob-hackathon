# Solution Overview

## What We Built

TitanSafe is a **privacy-preserving threat intelligence layer** that sits inside a
social media platform's trust boundary. It detects coordinated-inauthentic-behaviour
(CIB) clusters in real time, then releases evidence to law enforcement through three
cryptographically gated tiers — giving LEAs exactly what they need to act, and nothing
more, with mathematical proof that the evidence is authentic.

Zero external dependencies. Pure Python 3.10+. Deployable as a library alongside any
platform's existing data pipeline.

## How It Works

1. **Detection (inside platform boundary):** `detect.py` clusters posts by near-duplicate
   text, burst timing, account youth, and target convergence. `classify.py` applies a
   transparent lexicon + structure classifier to label each cluster as *incitement*,
   *targeted harassment*, or *organised misinformation* — with key phrases as evidence.

2. **Tier 0 — Attestation (no personal data leaves):** The `Vault` in `abstraction.py`
   commits each cluster's account count as a Pedersen commitment, generates
   Schnorr-based ZK range proofs ("at least 5/10/20/40 accounts"), and anchors all
   post evidence in a sorted Merkle tree. The Merkle root, ZK proofs, threat metadata
   and indicative legal sections are published to the LEA. No identity, no content,
   no phone number.

3. **Tier 1 — Pseudonymous Evidence (gated):** After LEA supplies a legal basis and
   nodal-officer approval, the platform releases per-case HMAC pseudonyms, age/follower
   *bands* (not exact values), and up to 25 redacted posts per cluster (PII stripped,
   third-party mentions masked). Each post includes a Merkle inclusion proof so the
   LEA can independently verify authenticity against the T0 root.

4. **Tier 2 — Identity Reveal (gated):** After a court/magistrate order reference and
   **two distinct approvers**, named pseudonyms are resolved to real user IDs and
   handles. Each revealed identity is cryptographically bound to its T1 pseudonym via
   a salted identity commitment in the Merkle tree — the LEA can verify the platform
   revealed the *true* identity, not a substitute.

5. **Dashboard & Report:** A single-page scrollable dark-terminal LEA dashboard
   (`dashboard.html`) with signal heatmaps, collapsible cluster cards, a live
   evidence search filter, and a timeline. A print-ready A4 HTML report
   (`threat_report.html`) for formal submissions.

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Pedersen commitments + ZK range/linkage proofs** | Prove "≥ k accounts" without revealing the exact count. Reused from QBOM-ZT — proven correct against the same curve parameters. |
| **Per-case HMAC pseudonyms** | `HMAC(case_key, case_id:user_id)` — the same user looks different in every case, preventing cross-case identity linking even if a LEA has multiple case files. |
| **Sorted Merkle tree with identity-binding leaves** | Each leaf commits to `hash(identity_commitment, post_id, salt)`. The Merkle root is published at T0; post evidence revealed at T1 is verifiable against it; identity revealed at T2 is verifiable against T1. The platform cannot alter evidence after attestation. |
| **Tamper-evident hash-chained audit log** | Every request, denial, approval and disclosure is SHA-256 chained. The LEA can verify the full audit trail without any platform access. |
| **Zero external dependencies** | Deployable inside any platform environment without supply-chain risk. All crypto is hand-rolled Python over a standard NIST P-256 equivalent curve (same as QBOM-ZT). |
| **Explainable, deterministic classifier** | A phrase-weighted lexicon with structural signals (burst, youth, hashtag sync). No black-box ML — every flag has a human-readable reason that can be presented in court. |

## IBM Technologies Used

- **IBM Bob (AI-assisted development):** Used throughout the development cycle for
  code review, architecture reasoning, refactoring the dashboard from tabbed to
  single-page scrollable layout, generating the four mock datasets, and writing the
  PDF report module. Bob's codebase understanding tools were used to navigate the
  QBOM-ZT cryptographic primitives and safely adapt them to the TitanSafe context.
