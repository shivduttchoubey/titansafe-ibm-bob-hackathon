"""Explainable lexicon + structure classifier (deterministic, no black box). Runs INSIDE the platform boundary."""
from __future__ import annotations
import re

LEX = {
 "incitement": {"gather": 2, "bring sticks": 3, "sticks": 2, "teach them a lesson": 3, "finish this": 2,
                "come to": 1, "attack": 3, "burn": 3, "kill": 3, "weapons": 3, "they must pay": 2},
 "targeted_harassment": {"we know where you live": 4, "your family": 3, "watch your back": 3, "you will be found": 3,
                         "report and hound": 2, "deserves what": 2, "stop writing": 2},
 "organized_misinformation": {"breaking": 2, "forward to all": 3, "before it is deleted": 3, "poisoned": 2,
                              "hospitalised": 1, "outsiders": 1, "urgent": 1},
}
HOSTILE = {k for c in ("incitement", "targeted_harassment") for k in LEX[c]}
PHONE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")
WHEN = re.compile(r"\b(tomorrow|tonight|today|\d{1,2}\s?(am|pm))\b")

def hostile_share(texts):
    return sum(any(k in t.lower() for k in HOSTILE) for t in texts) / max(1, len(texts))

def classify(texts, target_convergence=0.0):
    low = [t.lower() for t in texts]; scores = {}; ev = {}
    for cls, terms in LEX.items():
        per, hits = [], {}
        for t in low:
            s = 0
            for k, w in terms.items():
                if k in t: s += w; hits[k] = hits.get(k, 0) + 1
            per.append(min(s / 6, 1))
        scores[cls] = sum(per) / len(per); ev[cls] = sorted(hits, key=hits.get, reverse=True)[:5]
    share = lambda rx: sum(bool(rx.search(t)) for t in low) / len(low)
    imminent = share(WHEN) > 0.5 and scores["incitement"] > 0.3
    doxx = share(PHONE) > 0.1
    if imminent: scores["incitement"] += 0.2
    if target_convergence > 0.6 and scores["targeted_harassment"] > 0.2: scores["targeted_harassment"] += 0.3
    if doxx: scores["targeted_harassment"] += 0.2
    if scores["organized_misinformation"] > 0.3 and not any("http" in t for t in low): scores["organized_misinformation"] += 0.2
    top, second = sorted(scores.values(), reverse=True)[:2]
    label = max(scores, key=scores.get)
    conf = round(min(1.0, top / (top + second + 1e-9) * min(1, top + 0.4)), 2)
    sev = {"incitement": "HIGH", "targeted_harassment": "MEDIUM", "organized_misinformation": "MEDIUM"}[label]
    if (label == "incitement" and imminent) or (label == "targeted_harassment" and doxx): sev = "CRITICAL" if imminent else "HIGH"
    return {"threat_type": label, "confidence": conf, "severity": sev, "evidence_terms": ev[label],
            "class_scores": {k: round(v, 2) for k, v in scores.items()},
            "flags": {"imminent_offline_action": bool(imminent), "doxxing": bool(doxx)}}
