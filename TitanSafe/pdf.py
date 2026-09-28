"""Generates a print-ready HTML file that renders as a clean PDF when opened in any browser
and printed (Ctrl+P / Cmd+P) or saved with 'Print to PDF'.

Produces a self-contained single-file report: no external dependencies required.
The --pdf CLI flag writes <out>/threat_report.html alongside the dashboard.

Enhanced in this version:
  - SVG donut chart + horizontal bar charts embedded inline
  - Risk gauge arc per cluster
  - Signal heatmap table with colour-coded cells
  - Activity summary panel
  - Improved cover page with coloured severity badge
  - Cluster mini-summary grid on executive summary page
"""
from __future__ import annotations
import json, datetime as dt, math

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
SEV_COL = {"CRITICAL": "#c0392b", "HIGH": "#e67e22", "MEDIUM": "#2980b9"}
SEV_BG  = {"CRITICAL": "#fdf0f0", "HIGH": "#fef9f0", "MEDIUM": "#f0f6fd"}
SEV_BORDER = {"CRITICAL": "#c0392b", "HIGH": "#e67e22", "MEDIUM": "#2980b9"}


def _sev_badge(sev: str) -> str:
    col = SEV_COL.get(sev, "#555")
    bg  = SEV_BG.get(sev, "#f5f5f5")
    brd = SEV_BORDER.get(sev, "#999")
    return (f'<span style="background:{bg};color:{col};border:1px solid {brd};'
            f'padding:2px 9px;border-radius:2px;font-size:9.5pt;font-weight:700;'
            f'letter-spacing:.03em">{sev}</span>')


def _progress(val: float, col: str = "#2980b9", height: int = 6) -> str:
    w = min(100, max(0, val * 100))
    return (f'<div style="background:#e8e8e8;border-radius:3px;height:{height}px;'
            f'overflow:hidden;margin:3px 0;flex:1">'
            f'<div style="width:{w:.1f}%;background:{col};height:{height}px;border-radius:3px"></div></div>')


def _signal_col(v: float) -> str:
    return "#c0392b" if v >= 0.7 else "#e67e22" if v >= 0.4 else "#27ae60"


def _donut_svg(threats: list, size: int = 90) -> str:
    counts: dict[str, int] = {}
    for t in threats:
        counts[t["severity"]] = counts.get(t["severity"], 0) + 1
    total = len(threats) or 1
    slices = [
        ("CRITICAL", counts.get("CRITICAL", 0), "#c0392b"),
        ("HIGH",     counts.get("HIGH", 0),     "#e67e22"),
        ("MEDIUM",   counts.get("MEDIUM", 0),   "#2980b9"),
    ]
    r = size / 2 - 5
    cx = cy = size / 2
    angle = -math.pi / 2
    paths = []
    for _sev, n, col in slices:
        if not n:
            continue
        a = 2 * math.pi * (n / total)
        x1 = cx + r * math.cos(angle)
        y1 = cy + r * math.sin(angle)
        angle += a
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        large = 1 if a > math.pi else 0
        paths.append(f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z" fill="{col}" opacity=".85"/>')
    inner = r * 0.54
    paths.append(f'<circle cx="{cx}" cy="{cy}" r="{inner:.1f}" fill="white"/>')
    paths.append(f'<text x="{cx}" y="{cy + 5:.1f}" text-anchor="middle" fill="#333" font-size="{size * 0.18:.0f}" font-weight="700" font-family="Arial">{total}</text>')
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block">{"".join(paths)}</svg>'


def _hbar_svg(items: list[dict], width: int = 240, row_h: int = 18) -> str:
    """items: [{label, val, col}]"""
    max_val = max((x["val"] for x in items), default=1) or 1
    h = len(items) * row_h + 6
    parts = [f'<svg width="{width}" height="{h}" style="display:block;overflow:visible">']
    for i, it in enumerate(items):
        bw = (it["val"] / max_val) * (width - 80)
        y_text = i * row_h + row_h - 4
        parts.append(f'<text x="0" y="{y_text}" fill="#666" font-size="9" font-family="Arial">{str(it["label"])[:14]}</text>')
        parts.append(f'<rect x="76" y="{i * row_h + 2}" width="{bw:.1f}" height="{row_h - 6}" fill="{it["col"]}" rx="2" opacity=".85"/>')
        parts.append(f'<text x="{78 + bw + 3:.0f}" y="{y_text}" fill="#333" font-size="9" font-family="Arial">{it["val"]}</text>')
    parts.append('</svg>')
    return "".join(parts)


def _risk_gauge_svg(score: float, size: int = 60) -> str:
    norm = max(0.0, min(1.0, float(score)))
    r = size / 2 - 5
    cx = cy = size / 2
    start_a = -math.pi * 0.82
    end_a   =  math.pi * 0.82
    span_a  = end_a - start_a
    px, py = cx + r * math.cos(start_a), cy + r * math.sin(start_a)
    ex, ey = cx + r * math.cos(end_a),   cy + r * math.sin(end_a)
    fill_a = start_a + span_a * norm
    fx, fy = cx + r * math.cos(fill_a), cy + r * math.sin(fill_a)
    col = "#c0392b" if norm >= 0.7 else "#e67e22" if norm >= 0.4 else "#27ae60"
    large = 1 if norm > 0.5 else 0
    return (f'<svg width="{size}" height="{size}" style="display:inline-block;vertical-align:middle">'
            f'<path d="M{px:.1f},{py:.1f} A{r},{r} 0 1,1 {ex:.1f},{ey:.1f}" fill="none" stroke="#e0e0e0" stroke-width="5" stroke-linecap="round"/>'
            f'<path d="M{px:.1f},{py:.1f} A{r},{r} 0 {large},1 {fx:.1f},{fy:.1f}" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round"/>'
            f'<text x="{cx}" y="{cy + 4:.0f}" text-anchor="middle" fill="{col}" font-size="{size * 0.22:.0f}" font-weight="700" font-family="Arial">{norm * 100:.0f}</text>'
            f'</svg>')


def _signal_heatmap(threats: list) -> str:
    if not threats:
        return "<p>No signal data.</p>"
    sig_keys = list(threats[0].get("signals", {}).keys())
    header = "<tr><th>Cluster</th>" + "".join(f"<th>{k.replace('_', ' ')}</th>" for k in sig_keys) + "<th>CIB</th><th>Sev</th></tr>"
    rows = []
    for t in threats:
        cells = []
        for k in sig_keys:
            v = t["signals"].get(k, 0)
            col = "#fdf0f0" if v >= 0.7 else "#fef9f0" if v >= 0.4 else "#f5f9f5"
            tc  = "#c0392b" if v >= 0.7 else "#e67e22" if v >= 0.4 else "#27ae60"
            fw  = "700" if v >= 0.6 else "400"
            cells.append(f'<td style="background:{col};color:{tc};font-weight:{fw};text-align:center">{v*100:.0f}%</td>')
        rows.append(f'<tr><td><b>{t["cluster_id"]}</b></td>{"".join(cells)}<td style="font-weight:700;text-align:center">{t["cib_score"]}</td><td>{_sev_badge(t["severity"])}</td></tr>')
    return f'<table style="font-size:8.5pt">{header}{"".join(rows)}</table>'


def build_pdf(view: dict, brief: dict) -> str:
    """Return a self-contained HTML string suitable for print-to-PDF."""
    now_str = brief["generated_ist"].replace("T", " ")[:19] + " IST"
    overall  = brief["overall_severity"]
    lg       = view["ledger"]
    threats  = brief["threats"]
    t1       = view["t1"]
    t2       = view["t2"]
    requests = view["requests"]
    audit    = view["audit"]

    # ── section helpers ──────────────────────────────────────────────────────
    def section(title: str, body: str, page_break: bool = True) -> str:
        pb = '<div class="page-break"></div>' if page_break else ""
        return (f'{pb}<div class="section">'
                f'<div class="sec-title">{title}</div>'
                f'{body}</div>')

    def table(headers: list[str], rows: list[list[str]], small: bool = False) -> str:
        fs = "8.5pt" if small else "9.5pt"
        hdr = "".join(f"<th>{h}</th>" for h in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
            for row in rows
        )
        return f'<table style="font-size:{fs}">{hdr}{body}</table>'

    # ── cover ────────────────────────────────────────────────────────────────
    sev_col_cover = SEV_COL.get(overall, "#0d3b6e")
    sev_bg_cover  = SEV_BG.get(overall, "#f0f6fd")
    cover = f"""
<div class="cover">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px">
    <div>
      <div class="cover-logo">TITANSAFE</div>
      <div class="cover-sub">Privacy-Preserving Threat Intelligence — LEA Report</div>
    </div>
    <div style="background:{sev_bg_cover};border:2px solid {sev_col_cover};padding:10px 18px;border-radius:3px;text-align:center">
      <div style="font-size:9pt;color:{sev_col_cover};font-weight:600;letter-spacing:.04em">OVERALL SEVERITY</div>
      <div style="font-size:20pt;font-weight:900;color:{sev_col_cover}">{overall}</div>
    </div>
  </div>
  <div class="cover-rule"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
    <table class="cover-meta">
      <tr><td>Brief ID</td><td><b>{brief['brief_id']}</b></td></tr>
      <tr><td>Case ID</td><td><b>{brief['case_id']}</b></td></tr>
      <tr><td>Generated</td><td><b>{now_str}</b></td></tr>
      <tr><td>Merkle Root</td><td><code>{brief['merkle_root'][:32]}…</code></td></tr>
    </table>
    <table class="cover-meta">
      <tr><td>Threat Clusters</td><td><b>{len(threats)}</b></td></tr>
      <tr><td>Identities Revealed</td><td><b>{lg['identities_revealed']} of {lg['users_on_platform_dataset']} ({lg['identity_exposure_pct']}%)</b></td></tr>
      <tr><td>Pseudonyms Seen</td><td><b>{lg['pseudonyms_seen_by_lea']}</b></td></tr>
      <tr><td>Dataset Users</td><td><b>{lg['users_on_platform_dataset']}</b></td></tr>
    </table>
  </div>
  <div class="cover-notice">
    This report was generated from the privacy-preserving LEA view only. No raw user data,
    phone numbers, emails or cryptographic secrets were available to this tool.
    All evidence is anchored to a Merkle tree whose root is recorded above.
    Legal mapping is indicative decision support only — confirm with the investigating
    officer and public prosecutor before filing.
  </div>
</div>
<div class="page-break"></div>
"""

    # ── executive summary ────────────────────────────────────────────────────
    sev_counts: dict[str, int] = {}
    for t in threats:
        sev_counts[t["severity"]] = sev_counts.get(t["severity"], 0) + 1

    # Cluster overview mini-cards
    mini_cards = "".join(
        f'<div style="border:1px solid {SEV_BORDER.get(t["severity"],"#ccc")};'
        f'background:{SEV_BG.get(t["severity"],"#fff")};padding:8px 10px;border-radius:3px">'
        f'{_sev_badge(t["severity"])} <b style="font-size:10pt;margin-left:4px">{t["cluster_id"]}</b>'
        f'<div style="font-size:8.5pt;color:#555;margin-top:3px">{t["threat_type"].replace("_"," ").title()}</div>'
        f'<div style="font-size:8.5pt;margin-top:2px">Conf: <b>{t["confidence"]*100:.0f}%</b> · CIB: <b>{t["cib_score"]}</b> · Accts: <b>≥{t["min_accounts_proven"]}</b></div>'
        f'</div>'
        for t in threats
    )

    # Severity donut + hbar
    donut = _donut_svg(threats, 90)
    sev_hbar = _hbar_svg([
        {"label": "CRITICAL", "val": sev_counts.get("CRITICAL", 0), "col": "#c0392b"},
        {"label": "HIGH",     "val": sev_counts.get("HIGH", 0),     "col": "#e67e22"},
        {"label": "MEDIUM",   "val": sev_counts.get("MEDIUM", 0),   "col": "#2980b9"},
    ], width=200)

    cib_hbar = _hbar_svg([
        {"label": t["cluster_id"] + " " + t["threat_type"][:8],
         "val":   t["cib_score"],
         "col":   SEV_COL.get(t["severity"], "#2980b9")}
        for t in threats
    ], width=220)

    cluster_rows = [
        [t["cluster_id"],
         t["threat_type"].replace("_", " ").title(),
         _sev_badge(t["severity"]),
         f"{t['confidence']*100:.0f}%",
         str(t["cib_score"]),
         f"≥ {t['min_accounts_proven']}",
         t["time_window"]["first"][11:19] + " → " + t["time_window"]["last"][11:19],
         (", ".join(k for k, v in (t.get("flags") or {}).items() if v)) or "—"]
        for t in threats
    ]
    cluster_table = table(
        ["Cluster", "Type", "Severity", "Conf", "CIB", "Accounts", "Window", "Flags"],
        cluster_rows
    )

    exec_summary = section("1. Executive Summary", f"""
<p>The TitanSafe platform analysed the ingested dataset for coordinated-inauthentic-behaviour (CIB)
signals. <b>{len(threats)} threat cluster(s)</b> were identified. The highest severity is
{_sev_badge(overall)}.</p>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:12px 0">
  <div>
    <h4>Severity Distribution</h4>
    <div style="display:flex;align-items:center;gap:12px">
      {donut}
      {sev_hbar}
    </div>
  </div>
  <div>
    <h4>CIB Score by Cluster</h4>
    {cib_hbar}
  </div>
  <div>
    <h4>Privacy Ledger</h4>
    <p style="font-size:9pt">
      Identities revealed: <b>{lg['identities_revealed']}</b> of {lg['users_on_platform_dataset']} ({lg['identity_exposure_pct']}%)<br>
      Pseudonyms seen by LEA: <b>{lg['pseudonyms_seen_by_lea']}</b><br>
      <b>Never disclosed:</b> {', '.join(lg['never_disclosed'])}
    </p>
  </div>
</div>

<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin:14px 0">
{mini_cards}
</div>

<h4>All Clusters — Detail Summary</h4>
{cluster_table}
""", page_break=False)

    # ── signal heatmap section ────────────────────────────────────────────────
    sig_heatmap_section = section("2. Signal Analysis", f"""
<p>Signal heatmap showing all CIB indicators across clusters. Red = HIGH (≥70%) · Amber = MEDIUM (≥40%) · Green = LOW.</p>
{_signal_heatmap(threats)}
<p style="font-size:8.5pt;color:#666;margin-top:8px">
  Signal weights: similarity ×0.25 · burst ×0.25 · youth ×0.20 · hashtag_sync ×0.15 · low_reach ×0.15
</p>
""")

    # ── threat detail ────────────────────────────────────────────────────────
    threat_sections = []
    for i, t in enumerate(threats, 3):
        tw = t["time_window"]
        flags_str = ", ".join(k for k, v in (t.get("flags") or {}).items() if v) or "none"
        sig_html = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0;font-size:8.5pt">'
            f'<span style="width:100px;color:#666;flex-shrink:0">{k.replace("_", " ")}</span>'
            f'{_progress(v, _signal_col(v))}'
            f'<span style="width:30px;text-align:right;color:{_signal_col(v)};font-weight:{"700" if v>=0.6 else "400"}">{v*100:.0f}%</span>'
            f'</div>'
            for k, v in t["signals"].items()
        )
        score_html = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0;font-size:8.5pt">'
            f'<span style="width:150px;color:#666;flex-shrink:0">{k.replace("_", " ")}</span>'
            f'{_progress(v, _signal_col(v))}'
            f'<span style="width:30px;text-align:right">{v*100:.0f}%</span>'
            f'</div>'
            for k, v in (t.get("class_scores") or {}).items()
        )
        phrases = " &nbsp;·&nbsp; ".join(t.get("evidence_terms", []))
        legal_rows = [[r["ipc"], r["bns"], r["title"]] for r in t.get("legal", [])]
        legal_table = table(["IPC", "BNS", "Offence"], legal_rows, small=True)
        steps_html = "".join(f"<li>{s}</li>" for s in t.get("steps", []))
        explain_html = "".join(f"<li>{e}</li>" for e in t.get("explain", []))
        gauge = _risk_gauge_svg(t["cib_score"], 56)

        body = f"""
<div class="threat-header">
  {_sev_badge(t['severity'])}
  <b style="font-size:12pt;margin-left:8px">{t['cluster_id']}</b>
  <span style="color:#555;margin-left:8px">{t['threat_type'].replace('_', ' ').upper()}</span>
  <span style="margin-left:auto">{gauge}</span>
</div>
<table class="kv-table">
  <tr><td>Confidence</td><td><b>{t['confidence']*100:.0f}%</b></td>
      <td>CIB Score</td><td><b>{t['cib_score']}</b></td>
      <td>Accounts proven</td><td><b>≥ {t['min_accounts_proven']}</b></td></tr>
  <tr><td>Active window</td><td colspan="3">{tw['first'].replace('T',' ')[:19]} → {tw['last'].replace('T',' ')[:19]} UTC ({tw['span_min']} min)</td>
      <td>Flags</td><td><b>{flags_str}</b></td></tr>
  {('<tr><td>Target handle</td><td colspan="5"><b>@' + str(t['target_handle']) + '</b></td></tr>') if t.get('target_handle') else ''}
</table>
<div class="two-col">
  <div>
    <h5>CIB Signals</h5>{sig_html}
    <h5 style="margin-top:10px">Classification Scores</h5>{score_html}
  </div>
  <div>
    <h5>Why Flagged</h5><ul style="font-size:8.5pt;margin:0;padding-left:16px">{explain_html}</ul>
    <h5 style="margin-top:10px">Key Phrases</h5>
    <p style="font-size:8.5pt">{phrases}</p>
  </div>
</div>
<h5>Indicative Legal Provisions</h5>{legal_table}
<h5 style="margin-top:10px">Recommended Escalation</h5>
<ol style="font-size:8.5pt;padding-left:18px">{steps_html}</ol>
"""
        threat_sections.append(section(f"{i}. Cluster {t['cluster_id']} Detail", body))

    # ── T1 evidence ──────────────────────────────────────────────────────────
    if t1:
        ev_parts = []
        for c in t1:
            post_rows = [
                [p["pseudonym"][:16] + "…",
                 p["ts"][11:19],
                 p["text_redacted"][:80] + ("…" if len(p["text_redacted"]) > 80 else ""),
                 " ".join(p["hashtags"])[:30],
                 ", ".join(p["pii_flags"]) or "—"]
                for p in c["posts"][:10]
            ]
            ev_parts.append(
                f"<h4>{c['cluster_id']} — {c['n_accounts_disclosed']} pseudonymous accounts</h4>" +
                table(["Pseudonym", "Time", "Redacted Text", "Hashtags", "PII Flags"], post_rows, small=True)
            )
        n_threat = len(threats)
        t1_section = section(f"{n_threat+3}. Tier-1 Evidence (Redacted Posts)", "".join(ev_parts))
    else:
        t1_section = section(f"{len(threats)+3}. Tier-1 Evidence", "<p>No T1 evidence was requested in this session.</p>")

    # ── T2 identities ────────────────────────────────────────────────────────
    if t2:
        id_rows = [
            [r["pseudonym"][:16] + "…", r["handle"], r["user_id"], r["registration_region"], r["account_created"][:10]]
            for r in t2
        ]
        t2_section = section(
            f"{len(threats)+4}. Tier-2 Identities (Disclosed Under Court Order)",
            f"<p>{len(t2)} identities disclosed. All bound to Merkle-anchored identity commitments.</p>" +
            table(["Pseudonym", "Handle", "User ID", "Region", "Created"], id_rows)
        )
    else:
        t2_section = section(
            f"{len(threats)+4}. Tier-2 Identities",
            "<p>No identities were revealed in this session. Court order and dual approval required.</p>"
        )

    # ── disclosure requests ──────────────────────────────────────────────────
    req_rows = [
        [r["id"], f"T{r['tier']}", r["status"], r.get("requester", ""), r.get("purpose", "")[:50],
         "; ".join(r.get("reasons", [])) or r.get("expires", "")]
        for r in requests
    ]
    req_section = section(
        f"{len(threats)+5}. Disclosure Requests Log",
        table(["ID", "Tier", "Status", "Requester", "Purpose", "Reasons / Expires"], req_rows)
    )

    # ── audit chain ─────────────────────────────────────────────────────────
    audit_rows = [
        [str(a["seq"]), a["ts"].replace("T", " ")[:19], a["actor"][:30], a["action"],
         a["hash"][:16] + "…"]
        for a in audit
    ]
    audit_section = section(
        f"{len(threats)+6}. Tamper-Evident Audit Chain",
        f"<p>{len(audit)} entries. Verify integrity with <code>TitanSafe verify &lt;out&gt;</code>.</p>" +
        table(["#", "Time (UTC)", "Actor", "Action", "Hash"], audit_rows, small=True)
    )

    # ── process references ───────────────────────────────────────────────────
    proc_items = [
        "BNSS s.94 (CrPC s.91): notice for production of documents/records",
        "IT Act s.79(3)(b) + IT Rules 2021 r.3(1)(d): takedown notice to intermediary",
        "IT Act s.69A: blocking order via MeitY (only if content is severe and persistent)",
    ]
    proc_section = section(
        f"{len(threats)+7}. Process References",
        "<ul>" + "".join(f"<li>{p}</li>" for p in proc_items) + "</ul>"
        + "<p style='font-size:8.5pt;color:#888;margin-top:8px'>Legal mapping is indicative decision support only. "
          "Confirm all provisions with the investigating officer and public prosecutor before filing.</p>"
    )

    # ── assemble ─────────────────────────────────────────────────────────────
    body_html = (cover + exec_summary + sig_heatmap_section +
                 "".join(threat_sections) + t1_section + t2_section +
                 req_section + audit_section + proc_section)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TitanSafe Report — {brief['brief_id']}</title>
<style>
@page {{ size: A4; margin: 16mm 14mm; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 9.5pt;
  color: #1a1a1a;
  background: #fff;
  line-height: 1.55;
}}
/* cover */
.cover {{ padding: 32px 0 24px; }}
.cover-logo {{ font-size: 26pt; font-weight: 900; color: #0d3b6e; letter-spacing: .06em; }}
.cover-sub {{ font-size: 11pt; color: #555; margin-top: 4px; }}
.cover-rule {{ border-top: 3px solid #0d3b6e; margin: 14px 0; }}
.cover-meta {{ border-collapse: collapse; width: 100%; margin-bottom: 12px; }}
.cover-meta td {{ padding: 4px 10px 4px 0; vertical-align: top; font-size: 9.5pt; }}
.cover-meta td:first-child {{ color: #666; width: 140px; font-weight: 600; }}
.cover-notice {{ font-size: 8.5pt; color: #666; border-top: 1px solid #ddd; padding-top: 10px; line-height: 1.5; }}
/* sections */
.section {{ margin: 0 0 20px; }}
.sec-title {{
  font-size: 12.5pt; font-weight: 700; color: #0d3b6e;
  border-bottom: 2px solid #0d3b6e; padding-bottom: 4px; margin-bottom: 10px;
}}
.section p {{ margin: 5px 0; font-size: 9.5pt; }}
.section h4 {{ font-size: 9.5pt; color: #0d3b6e; margin: 10px 0 4px; font-weight: 700; }}
.section h5 {{ font-size: 8.5pt; color: #333; margin: 7px 0 3px; font-weight: 600; }}
.section ul, .section ol {{ padding-left: 16px; margin: 4px 0; }}
.section li {{ margin: 2px 0; font-size: 8.5pt; }}
/* tables */
table {{ border-collapse: collapse; width: 100%; margin: 5px 0; }}
th {{ background: #0d3b6e; color: #fff; padding: 4px 7px; font-size: 8.5pt; text-align: left; font-weight: 600; }}
td {{ padding: 3px 7px; font-size: 8.5pt; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
tr:nth-child(even) td {{ background: #f7f9fc; }}
code {{ font-family: "Courier New", monospace; font-size: 8.5pt; color: #555; }}
/* threat block */
.threat-header {{ display: flex; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px; }}
.kv-table {{ font-size: 8.5pt; margin-bottom: 10px; }}
.kv-table td:nth-child(odd) {{ color: #666; width: 100px; font-weight: 600; }}
.kv-table td:nth-child(even) {{ width: 110px; }}
/* two-col */
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 8px 0; }}
/* page break */
.page-break {{ page-break-after: always; }}
/* print trigger hint */
@media screen {{
  body {{ background: #eef0f3; }}
  .page {{ background: #fff; max-width: 800px; margin: 20px auto; padding: 28px 32px; box-shadow: 0 2px 10px rgba(0,0,0,.15); }}
  #print-hint {{
    position: fixed; top: 12px; right: 16px; z-index: 999;
    background: #0d3b6e; color: #fff; border: none; padding: 8px 18px;
    font-size: 11pt; cursor: pointer; border-radius: 3px; font-family: inherit;
  }}
  #print-hint:hover {{ background: #1556a0; }}
}}
@media print {{ body {{ background: #fff; }} .page {{ padding: 0; box-shadow: none; }} #print-hint {{ display: none; }} }}
</style>
</head>
<body>
<button id="print-hint" onclick="window.print()">⎙ Print / Save as PDF</button>
<div class="page">
{body_html}
</div>
</body>
</html>
"""
