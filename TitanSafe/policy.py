"""DPDP-aligned disclosure policy: purpose limitation, data minimisation, proportionality, dual control, retention."""
TIERS = {0: "T0 Signals & proofs (no personal data)",
         1: "T1 Pseudonymous evidence (redacted, per-case pseudonyms)",
         2: "T2 Identity reveal (court/legal order + dual approval)"}
FIELDS = {0: ["cluster_id", "threat_type", "severity", "confidence", "cib_score", "signals", "time_window", "evidence_terms",
              "flags", "zk_min_accounts"],
          1: ["pseudonym", "account_age_band", "followers_band", "post_id", "ts", "text_redacted", "hashtags", "pii_flags", "merkle"],
          2: ["pseudonym", "user_id", "handle", "account_created", "registration_region", "identity_salt"]}
NEVER = ["phone number", "e-mail", "IP / device data", "private messages", "contacts / graph", "posts outside the flagged clusters"]
RETENTION_DAYS = {0: 365, 1: 30, 2: 15}
MIN_SCORE_T1 = 0.60      # proportionality: only well-evidenced clusters may be pulled to T1
MAX_T2 = 15              # cap on identities per request

def check(tier, req, clusters, t1_pseudonyms, approvers):
    """Returns list of reasons the request must be denied (empty = allowed)."""
    why = []
    if not req.get("purpose"): why.append("purpose statement missing (purpose limitation)")
    if tier >= 1:
        if not req.get("legal_basis"): why.append("legal basis missing")
        if not approvers: why.append("no platform nodal-officer approval")
    if tier == 1:
        ids = req.get("clusters") or []
        if not ids: why.append("no clusters named (data minimisation)")
        for cid in ids:
            c = clusters.get(cid)
            if not c: why.append(f"unknown cluster {cid}")
            elif c["cib_score"] < MIN_SCORE_T1: why.append(f"{cid}: CIB score below proportionality bar {MIN_SCORE_T1}")
    if tier == 2:
        ps = req.get("pseudonyms") or []
        if not req.get("order_ref"): why.append("court/magistrate order reference missing")
        if len(set(approvers)) < 2: why.append("dual approval required (2 distinct officers)")
        if not ps: why.append("no pseudonyms named")
        if len(ps) > MAX_T2: why.append(f"more than {MAX_T2} identities requested")
        if not set(ps) <= set(t1_pseudonyms): why.append("pseudonym not previously disclosed at T1 in this case")
    return why
