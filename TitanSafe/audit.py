"""Tamper-evident, hash-chained audit log: every request, decision and disclosure (including denials)."""
import hashlib, json, datetime as dt

class AuditLog:
    def __init__(self): self.entries = []
    def add(self, actor, action, detail):
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        e = {"seq": len(self.entries) + 1, "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "actor": actor, "action": action, "detail": detail, "prev": prev}
        e["hash"] = self._h(e); self.entries.append(e); return e
    @staticmethod
    def _h(e):
        b = {k: e[k] for k in ("seq", "ts", "actor", "action", "detail", "prev")}
        return hashlib.sha3_256(json.dumps(b, sort_keys=True).encode()).hexdigest()

def verify_chain(entries):
    prev = "0" * 64
    for e in entries:
        if e["prev"] != prev or AuditLog._h(e) != e["hash"]: return False
        prev = e["hash"]
    return True
