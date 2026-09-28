"""Coordinated-inauthentic-behaviour (CIB) detection. Runs INSIDE the platform boundary on raw data."""
from __future__ import annotations
import itertools
from collections import Counter, defaultdict
from .classify import classify, hostile_share

W = {"similarity": .25, "burst": .25, "youth": .20, "hashtag_sync": .15, "low_reach": .15}
WINDOW_MIN = 90

def _tok(t):
    import re
    t = re.sub(r"https?://\S+|@\w+|#\w+", " ", t.lower()); return re.findall(r"[a-z0-9]+", t)
def _sh(tk, n): return {tuple(tk[i:i+n]) for i in range(max(1, len(tk)-n+1))}
def _jac(a, b): return len(a & b) / len(a | b) if a and b else 0.0
def _sim(x, y):
    return max(_jac(set(x[0]), set(y[0])) * .9, _jac(x[1], y[1]))

def detect(posts, min_accounts=5, min_score=0.5):
    n = len(posts); par = list(range(n))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def u(i, j): par[f(i)] = f(j)
    feats = [(_tok(p.text), _sh(_tok(p.text), 2)) for p in posts]
    for i, j in itertools.combinations(range(n), 2):       # near-duplicate text within a time window
        if abs((posts[i].dt - posts[j].dt).total_seconds()) <= WINDOW_MIN * 60 and _sim(feats[i], feats[j]) >= .30:
            u(i, j)
    by_m = defaultdict(list)                                # hostile convergence on one target
    for i, p in enumerate(posts):
        for m in set(p.mentions): by_m[m].append(i)
    for m, idx in by_m.items():
        us = {posts[i].user_id for i in idx}
        span = (max(posts[i].dt for i in idx) - min(posts[i].dt for i in idx)).total_seconds() / 60
        if len(us) >= min_accounts and span <= WINDOW_MIN and hostile_share([posts[i].text for i in idx]) >= .5:
            for a, b in zip(idx, idx[1:]): u(a, b)
    groups = defaultdict(list)
    for i in range(n): groups[f(i)].append(i)
    out = []
    for idx in groups.values():
        ps = [posts[i] for i in idx]; accts = {p.user_id for p in ps}
        if len(accts) < min_accounts: continue
        ts = sorted(p.dt for p in ps); span = (ts[-1] - ts[0]).total_seconds() / 60
        sample = idx[:40]; pairs = list(itertools.combinations(sample, 2))
        sim = sum(_sim(feats[a], feats[b]) for a, b in pairs) / max(1, len(pairs))
        first = {}
        for p in ps: first.setdefault(p.user_id, p)
        youth = sum((p.dt - p.created_dt).days < 30 for p in first.values()) / len(first)
        low = sum(p.followers < 50 for p in first.values()) / len(first)
        tags = Counter(h for p in ps for h in set(p.hashtags)); hs = (tags.most_common(1)[0][1] / len(ps)) if tags else 0
        ms = Counter(m for p in ps for m in set(p.mentions)); top_m, top_c = ms.most_common(1)[0] if ms else (None, 0)
        conv = top_c / len(ps)
        sig = {"similarity": round(max(sim, conv), 2), "burst": round(max(0, 1 - span / WINDOW_MIN), 2),
               "youth": round(youth, 2), "hashtag_sync": round(hs, 2), "low_reach": round(low, 2)}
        score = round(sum(W[k] * sig[k] for k in W), 2)
        if score < min_score: continue
        c = classify([p.text for p in ps], conv if top_m else 0)
        if max(c['class_scores'].values()) < 0.25: continue   # coordinated but benign (e.g. organic trend)
        expl = [f"{len(accts)} distinct accounts in one cluster", f"active window {span:.0f} min",
                f"{youth:.0%} of accounts <30 days old at first post", f"text/target similarity {sig['similarity']:.2f}"]
        out.append({"post_idx": idx, "n_accounts": len(accts), "n_posts": len(ps), "cib_score": score, "signals": sig,
                    "first_ts": ts[0].isoformat(), "last_ts": ts[-1].isoformat(), "span_min": round(span, 1),
                    "top_hashtags": [h for h, _ in tags.most_common(3)],
                    "top_mention": top_m if c["threat_type"] == "targeted_harassment" else None,
                    "explain": expl, **c})
    out.sort(key=lambda c: ({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}[c["severity"]], -c["cib_score"]))
    for k, c in enumerate(out, 1): c["cluster_id"] = f"CL-{k:02d}"
    return out
