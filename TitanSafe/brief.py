"""Threat brief generator. Consumes ONLY the LEA view (never the vault) -> cannot leak what it never saw."""
from __future__ import annotations
import datetime as dt
from . import legal
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ESC = {
 "incitement": ["IMMEDIATE (0-1h): alert District SP / Control Room and local law-and-order units for the named location and time",
                "Send takedown notice to platform under IT Act s.79(3)(b); request preservation of the flagged cluster",
                "Request T1 evidence for the cluster (redacted posts + pseudonyms) if not already held",
                "Seek magistrate order, then request T2 identity reveal for ORGANISERS only (earliest-active pseudonyms)",
                "Coordinate with State Cyber Cell; prepare FIR under the mapped BNS sections"],
 "targeted_harassment": ["Contact the targeted person; advise on safety and preservation of screenshots",
                "Request platform takedown of doxxed content; register complaint / FIR (BNS s.351, s.78)",
                "Request T1 evidence, then T2 for the smallest set of pseudonyms that drive the campaign",
                "Consider protective measures (beat patrol) if a home address was exposed"],
 "organized_misinformation": ["Verify the claim with the responsible authority (e.g. water board / district admin) and publish a rebuttal",
                "Issue takedown / labelling request to platform; monitor spread for community-directed framing",
                "Request T1 evidence to assess origin pattern; T2 only if the claim escalates to incitement"]}
RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}

def build(view):
    att = view["attestation"]; now = dt.datetime.now(dt.timezone.utc)
    cl = sorted(att["clusters"], key=lambda c: RANK[c["severity"]]); items = []
    for c in cl:
        k = max((p["k"] for p in c["zk_min_accounts"]), default=0)
        items.append({**c, "min_accounts_proven": k, "steps": ESC[c["threat_type"]]})
    brief = {"brief_id": f"TB-{att['case_id']}", "case_id": att["case_id"], "generated_utc": now.isoformat(timespec="seconds"),
             "generated_ist": now.astimezone(IST).isoformat(timespec="seconds"), "merkle_root": att["merkle_root"],
             "overall_severity": cl[0]["severity"] if cl else "NONE", "threats": items, "ledger": view["ledger"]}
    L = [f"# THREAT BRIEF {brief['brief_id']}", f"**Generated:** {brief['generated_ist']} IST / {brief['generated_utc']} UTC  ",
         f"**Overall severity:** {brief['overall_severity']}  |  **Evidence anchor (Merkle root):** `{att['merkle_root'][:24]}...`", "",
         "> Built from the privacy-preserving LEA view only. No raw user data, identities or contact details were available to this tool.", ""]
    for c in items:
        w = c["time_window"]
        L += [f"## {c['cluster_id']} - {c['threat_type'].replace('_', ' ').upper()} [{c['severity']}]",
              f"- **Confidence:** {c['confidence']}  |  **CIB score:** {c['cib_score']}  |  **Accounts (ZK-proven):** at least {c['min_accounts_proven']}",
              f"- **Active window:** {w['first']} -> {w['last']} ({w['span_min']} min)",
              f"- **Why flagged:** {'; '.join(c['explain'])}; key phrases: {', '.join(c['evidence_terms'])}",
              f"- **Flags:** " + (", ".join(k for k, v in c["flags"].items() if v) or "none")
              + (f"  |  **Target:** @{c['target_handle']}" if c["target_handle"] else ""),
              "", "**Indicative legal provisions (IPC -> BNS)**", ""]
        L += [f"- {r['title']}: IPC {r['ipc']} -> **BNS {r['bns']}**" for r in c["legal"]]
        L += ["", "**Recommended escalation**", ""] + [f"{i}. {s}" for i, s in enumerate(c["steps"], 1)] + [""]
    L += ["## Process references", ""] + [f"- {p}" for p in legal.PROCESS]
    lg = view["ledger"]
    L += ["", "## Privacy ledger (what this investigation has seen)", "",
          f"- Pseudonyms seen: {lg['pseudonyms_seen_by_lea']} of {lg['users_on_platform_dataset']} users in dataset",
          f"- Identities revealed: {lg['identities_revealed']} ({lg['identity_exposure_pct']}%)",
          f"- Never disclosed: {', '.join(lg['never_disclosed'])}", "",
          "_Legal mapping is indicative decision support; confirm with the investigating officer and public prosecutor._"]
    return brief, "\n".join(L)
