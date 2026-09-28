"""Case lifecycle: LEA request -> policy check -> platform approval -> tiered disclosure -> audit."""
from __future__ import annotations
import datetime as dt
from .abstraction import Vault
from .audit import AuditLog
from . import policy

class Case:
    def __init__(self, case_id, posts, clusters):
        self.case_id, self.audit = case_id, AuditLog()
        self.vault = Vault(case_id, posts, clusters); self.clusters = {c["cluster_id"]: c for c in clusters}
        self.att = self.vault.attest(); self.t1, self.t2, self.log = [], [], []
        self.audit.add("PLATFORM", "ATTESTATION_PUBLISHED", {"merkle_root": self.att["merkle_root"], "clusters": len(clusters)})

    def request(self, tier, requester, approvers=(), **req):
        rid = f"REQ-{len(self.log)+1:03d}"
        self.audit.add(requester, "REQUEST", {"id": rid, "tier": tier, **{k: v for k, v in req.items() if v}})
        approvers = list(approvers) or (["auto-policy"] if tier == 0 else [])
        t1_ps = [a["pseudonym"] for c in self.t1 for a in c["accounts"]]
        why = policy.check(tier, req, self.clusters, t1_ps, approvers)
        rec = {"id": rid, "tier": tier, "requester": requester, "status": "DENIED" if why else "DISCLOSED", "reasons": why}
        if why:
            self.audit.add(",".join(approvers) or "policy-engine", "DENIED", {"id": rid, "reasons": why})
        else:
            exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=policy.RETENTION_DAYS[tier])).date().isoformat()
            if tier == 1: self.t1 += self.vault.t1(req["clusters"])
            if tier == 2: self.t2 += self.vault.t2(req["pseudonyms"])
            rec["expires"] = exp
            self.audit.add(",".join(approvers), "APPROVED_AND_DISCLOSED", {"id": rid, "tier": tier, "expires": exp,
                           "scope": req.get("clusters") or req.get("pseudonyms") or "signals-only"})
        self.log.append(rec); return rec

    def ledger(self):
        total = len({p.user_id for p in self.vault.posts}); flagged = len(self.vault._salt_u)
        t1 = len({a["pseudonym"] for c in self.t1 for a in c["accounts"]}); t2 = len(self.t2)
        return {"users_on_platform_dataset": total, "users_in_flagged_clusters": flagged, "pseudonyms_seen_by_lea": t1,
                "identities_revealed": t2, "identity_exposure_pct": round(100 * t2 / total, 2),
                "never_disclosed": policy.NEVER}

    def lea_view(self):
        """The ONLY object the LEA-side code (brief/dashboard) may consume."""
        return {"attestation": self.att, "t1": self.t1, "t2": self.t2, "requests": self.log,
                "audit": self.audit.entries, "ledger": self.ledger()}
