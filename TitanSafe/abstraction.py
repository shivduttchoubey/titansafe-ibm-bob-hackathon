"""The abstraction layer. Platform-side Vault holds raw data + secrets; everything leaving it is one of 3 tiers.

Reused from qbom-zt: Pedersen commitments, range/linkage ZK proofs, sorted Merkle tree.
New: per-case HMAC pseudonyms, identity-binding leaves, redaction, k-anonymity floor, 'at least k' proof."""
from __future__ import annotations
import hashlib, hmac, re, secrets, datetime as dt
from .zt import zk, merkle
from .zt.ec import N
from .classify import PHONE
from . import legal

THRESHOLDS = (5, 10, 20, 40); NBITS = 10
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"); MENT = re.compile(r"@(\w+)")
h3 = lambda *p: hashlib.sha3_256(b"|".join(p)).digest()

# ---- 'count >= k' proof (mirror of qbom-zt's below-threshold proof) ---------------------------------
def prove_at_least(count, r, C, k, ctx):
    slack = count - k
    if slack < 0: raise ValueError("count below k")
    rs = zk.rand_scalar(); sc = zk.commit(slack, rs)
    rp = zk.prove_range(slack, rs, sc, NBITS, ctx)
    D = zk.Commitment(zk._sub(C.point, sc.point))
    return {"k": k, "slack_commitment": sc.to_hex(), "range": rp.to_dict(),
            "linkage": zk.prove_public_value(k, (r - rs) % N, D, ctx).to_dict()}

def verify_at_least(C, p, ctx):
    sc = zk.commitment_from_hex(p["slack_commitment"])
    lk = zk.PublicValueProof.from_dict(p["linkage"])
    D = zk.Commitment(zk._sub(C.point, sc.point))
    return (lk.public_value == p["k"] and zk.verify_public_value(D, lk, ctx)
            and zk.verify_range(sc, zk.RangeProof.from_dict(p["range"]), ctx))

def _band(v, cuts, labels): return labels[sum(v >= c for c in cuts)]

class Vault:
    """Platform trust boundary. Nothing here is ever serialised to the LEA except via attest()/t1()/t2()."""
    def __init__(self, case_id, posts, clusters):
        self.case_id, self.posts, self.clusters = case_id, posts, clusters
        self._key = secrets.token_bytes(32)
        self._salt_u, self._salt_p, self._idc = {}, {}, {}
        self.users = {p.user_id: p for p in posts}
        self._r = {}; self._C = {}
        self.leaf = {}
        for c in clusters:
            for i in c["post_idx"]:
                p = posts[i]; ps = self.pseudo(p.user_id)
                self._salt_u.setdefault(p.user_id, secrets.token_bytes(16))
                self._idc[p.user_id] = h3(ps.encode(), p.user_id.encode(), self._salt_u[p.user_id]).hex()
                self._salt_p[p.post_id] = secrets.token_bytes(16)
                self.leaf[p.post_id] = h3(bytes.fromhex(self._idc[p.user_id]), p.post_id.encode(), self._salt_p[p.post_id])
        self.tree = merkle.build_tree(list(self.leaf.values()))
        for c in clusters:
            C, r = zk.commit_random(c["n_accounts"]); self._C[c["cluster_id"]], self._r[c["cluster_id"]] = C, r

    def pseudo(self, uid):   # per-case: same user gets a DIFFERENT pseudonym in another case (no cross-case linking)
        return "PSN-" + hmac.new(self._key, f"{self.case_id}:{uid}".encode(), "sha256").hexdigest()[:10]

    # ---------------- Tier 0 ----------------
    def attest(self):
        cl = []
        for c in self.clusters:
            cid = c["cluster_id"]; ctx = f"{self.case_id}:{cid}".encode()
            proofs = [prove_at_least(c["n_accounts"], self._r[cid], self._C[cid], k, ctx) for k in THRESHOLDS if c["n_accounts"] >= k]
            cl.append({"cluster_id": cid, "threat_type": c["threat_type"], "severity": c["severity"], "confidence": c["confidence"],
                       "cib_score": c["cib_score"], "signals": c["signals"], "evidence_terms": c["evidence_terms"], "flags": c["flags"],
                       "explain": [e for e in c["explain"] if "distinct accounts" not in e],
                       "time_window": {"first": c["first_ts"], "last": c["last_ts"], "span_min": c["span_min"]},
                       "top_hashtags": c["top_hashtags"], "target_handle": c["top_mention"],
                       "accounts_commitment": self._C[cid].to_hex(), "zk_min_accounts": proofs,
                       "legal": legal.sections(c["threat_type"], c["flags"])})
        return {"case_id": self.case_id, "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "merkle_root": self.tree.root_hex(), "clusters": cl}

    # ---------------- Tier 1 ----------------
    def redact(self, text, keep_handle=None):
        text = EMAIL.sub("[EMAIL]", text); text = PHONE.sub("[PHONE]", text)
        return MENT.sub(lambda m: m.group(0) if keep_handle and m.group(1).lower() == keep_handle else "@[USER]", text)

    def t1(self, cluster_ids, max_posts=25):
        out = []
        for c in self.clusters:
            if c["cluster_id"] not in cluster_ids: continue
            accts, posts = {}, []
            for i in c["post_idx"]:
                p = self.posts[i]; ps = self.pseudo(p.user_id)
                age = (p.dt - p.created_dt).days
                a = accts.setdefault(ps, {"pseudonym": ps, "identity_commitment": self._idc[p.user_id], "posts": 0,
                    "account_age_band": _band(age, (7, 30, 180), ["<7d", "7-30d", "30-180d", ">180d"]),
                    "followers_band": _band(p.followers, (50, 500), ["<50", "50-500", "500+"])})
                a["posts"] += 1
                if len(posts) < max_posts:
                    pr = self.tree.prove_inclusion(self.leaf[p.post_id])
                    posts.append({"post_id": p.post_id, "pseudonym": ps, "ts": p.ts, "hashtags": p.hashtags,
                        "text_redacted": self.redact(p.text, c["top_mention"]),
                        "pii_flags": [k for k, rx in (("phone_in_text", PHONE), ("email_in_text", EMAIL)) if rx.search(p.text)],
                        "merkle": {"post_salt": self._salt_p[p.post_id].hex(), "index": pr.leaf_index,
                                   "siblings": [[s.hex(), r] for s, r in pr.siblings]}})
            out.append({"cluster_id": c["cluster_id"], "n_accounts_disclosed": len(accts), "accounts": list(accts.values()), "posts": posts})
        return out

    # ---------------- Tier 2 ----------------
    def t2(self, pseudonyms):
        rev = {self.pseudo(u): u for u in self._salt_u}; out = []
        for ps in pseudonyms:
            p = self.users[rev[ps]]
            out.append({"pseudonym": ps, "user_id": p.user_id, "handle": p.handle, "account_created": p.account_created,
                        "registration_region": p.region, "identity_salt": self._salt_u[p.user_id].hex()})
        return out

# ---------------- LEA-side verification (needs no vault access) ----------------
def verify_attestation(att):
    res = []
    for c in att["clusters"]:
        C = zk.commitment_from_hex(c["accounts_commitment"]); ctx = f"{att['case_id']}:{c['cluster_id']}".encode()
        for p in c["zk_min_accounts"]: res.append((c["cluster_id"], p["k"], verify_at_least(C, p, ctx)))
    return res

def verify_t1(att, t1):
    root = bytes.fromhex(att["merkle_root"]); bad = 0; n = 0
    for c in t1:
        idc = {a["pseudonym"]: a["identity_commitment"] for a in c["accounts"]}
        for p in c["posts"]:
            n += 1; m = p["merkle"]
            leaf = h3(bytes.fromhex(idc[p["pseudonym"]]), p["post_id"].encode(), bytes.fromhex(m["post_salt"]))
            pr = merkle.MerkleProof(m["index"], [(bytes.fromhex(s), r) for s, r in m["siblings"]], leaf)
            bad += not merkle.verify_inclusion(root, pr)
    return n, bad

def verify_t2(t1, t2):
    idc = {a["pseudonym"]: a["identity_commitment"] for c in t1 for a in c["accounts"]}; bad = 0
    for r in t2:
        bad += h3(r["pseudonym"].encode(), r["user_id"].encode(), bytes.fromhex(r["identity_salt"])).hex() != idc.get(r["pseudonym"])
    return len(t2), bad
