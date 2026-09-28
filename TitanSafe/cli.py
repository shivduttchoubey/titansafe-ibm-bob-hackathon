"""TitanSafe demo | TitanSafe verify <outdir> | TitanSafe datasets"""
from __future__ import annotations
import argparse, json, os
from . import mock, detect as det, brief as br, dashboard as dash, pdf as pdfmod
from .workflow import Case
from .abstraction import verify_attestation, verify_t1, verify_t2
from .audit import verify_chain
G, C, R, X = "\033[92m", "\033[96m", "\033[91m", "\033[0m"
say = lambda s, c=G: print(f"{c}{s}{X}")

def run_demo(out="out", seed=None, dataset="default", pdf=False, quiet=False):
    p = (lambda *a, **k: None) if quiet else say
    os.makedirs(out, exist_ok=True)

    posts = mock.load(dataset, seed)
    p(f"[platform] ingested {len(posts)} mock posts from {len({x.user_id for x in posts})} accounts  (dataset: {dataset})", C)

    clusters = det.detect(posts); p(f"[platform] CIB detection inside trust boundary: {len(clusters)} coordinated threat clusters")
    case_id = f"CASE-{dataset.upper()[:8]}-2026"
    case = Case(case_id, posts, clusters)
    p(f"[platform] T0 attestation published (commitments + ZK proofs + Merkle root); raw data stays in vault")

    LEA, NO = "LEA:Cyber-Cell-Gandhinagar", "Nodal-Officer-A"
    r = case.request(0, LEA, purpose="Situational awareness"); p(f"[LEA] T0 request -> {r['status']}")

    top = [c["cluster_id"] for c in clusters if c["cib_score"] >= 0.6]
    if not top:
        top = [clusters[0]["cluster_id"]] if clusters else []

    if top:
        r = case.request(1, LEA, [NO], clusters=top, purpose="Investigate coordinated threat",
                         legal_basis="BNS 196/351; BNSS 94 notice ref N/26/0917")
        p(f"[LEA] T1 for {top} with legal basis + nodal approval -> {r['status']}")

        early = sorted((x for c in case.t1 for x in c["posts"] if c["cluster_id"] == top[0]), key=lambda x: x["ts"])
        organisers = list(dict.fromkeys(x["pseudonym"] for x in early))[:3]

        if organisers:
            r = case.request(2, LEA, [NO, "Grievance-Officer-B"], pseudonyms=organisers, purpose="Identify organisers",
                             legal_basis="BNS 196", order_ref="CJM-GNR/2026/4471")
            p(f"[LEA] T2 for {len(organisers)} pseudonyms with order + dual approval -> {r['status']}")

    view = case.lea_view(); brief, md = br.build(view)
    files = {"attestation.json": case.att, "tier1_evidence.json": case.t1, "tier2_identities.json": case.t2,
             "audit.json": case.audit.entries, "requests.json": case.log, "threat_brief.json": brief}
    for n, d in files.items(): json.dump(d, open(f"{out}/{n}", "w"), indent=1)
    open(f"{out}/threat_brief.md", "w", encoding="utf-8").write(md)
    open(f"{out}/dashboard.html", "w", encoding="utf-8").write(dash.render(view, brief))
    if pdf:
        open(f"{out}/threat_report.html", "w", encoding="utf-8").write(pdfmod.build_pdf(view, brief))
        p(f"[done] wrote {out}/threat_report.html — open in browser and use Print > Save as PDF")

    lg = case.ledger()
    p(f"[ledger] LEA saw {lg['pseudonyms_seen_by_lea']} pseudonyms and {lg['identities_revealed']} identities of {lg['users_on_platform_dataset']} users ({lg['identity_exposure_pct']}%)", C)
    p(f"[done] wrote {out}/ (dashboard.html{', threat_report.html' if pdf else ''}, threat_brief.md, ...)  next: threatlens verify {out}")
    return case

def run_verify(out):
    ld = lambda n: json.load(open(f"{out}/{n}"))
    att, t1, t2, au = ld("attestation.json"), ld("tier1_evidence.json"), ld("tier2_identities.json"), ld("audit.json")
    zk = verify_attestation(att); n, bad = verify_t1(att, t1); m, bad2 = verify_t2(t1, t2); ok = verify_chain(au)
    rows = [(f"ZK proofs 'accounts >= k' ({sum(x[2] for x in zk)}/{len(zk)})", all(x[2] for x in zk)),
            (f"T1 posts anchored to Merkle root ({n - bad}/{n})", bad == 0),
            (f"T2 identities bound to pseudonym commitments ({m - bad2}/{m})", bad2 == 0), ("audit hash chain intact", ok)]
    for t, v in rows: say(f"[{'PASS' if v else 'FAIL'}] {t}", G if v else R)
    return all(v for _, v in rows)

def run_datasets():
    for ds in mock.list_datasets():
        print(f"  {ds['name']:<22}  seed={ds['default_seed']}  —  {ds['description']}")

def main():
    ap = argparse.ArgumentParser("TitanSafe"); sp = ap.add_subparsers(dest="cmd", required=True)

    d = sp.add_parser("demo", help="Run a demo case and generate outputs")
    d.add_argument("--out", default="out", help="Output directory (default: out)")
    d.add_argument("--seed", type=int, default=None, help="Override the dataset's default random seed")
    d.add_argument("--dataset", default="default",
                   choices=list(mock.DATASETS.keys()),
                   metavar="DATASET",
                   help=("Named mock dataset to use (default: default). "
                         "Available: " + ", ".join(mock.DATASETS.keys())))
    d.add_argument("--pdf", action="store_true", help="Also generate threat_report.html (print-to-PDF)")

    v = sp.add_parser("verify", help="Verify ZK proofs, Merkle anchors and audit chain")
    v.add_argument("out", nargs="?", default="out")

    sp.add_parser("datasets", help="List available mock datasets")

    a = ap.parse_args()
    if a.cmd == "demo":
        run_demo(a.out, a.seed, a.dataset, a.pdf)
    elif a.cmd == "datasets":
        run_datasets()
    else:
        raise SystemExit(0 if run_verify(a.out) else 1)

if __name__ == "__main__": main()
