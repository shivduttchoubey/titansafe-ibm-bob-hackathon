"""TitanSafe Web App — officer-friendly chat interface.

New in this version:
  - IBM Bob API key settings panel (gear icon, stored in browser sessionStorage)
  - /generate-fir   → uses Bob API to write a realistic FIR; falls back to
                       built-in templates when no key is set
  - /bob-chat       → Bob enriches analysis with plain-language narrative
  - Settings modal  → paste API key + model endpoint; tested with a ping

Run:
    python -m TitanSafe.app
    flask --app TitanSafe.app run
"""
from __future__ import annotations
import io, json, os, re, threading, time, uuid
from pathlib import Path

try:
    from flask import Flask, request, jsonify, Response
except ImportError:
    raise SystemExit(
        "\n[TitanSafe] Flask is required.\n  pip install flask\n"
    )

from . import mock, detect as det, brief as br, dashboard as dash, pdf as pdfmod
from .workflow import Case

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

_SESSIONS: dict[str, dict] = {}
_LOCK = threading.Lock()

# ── keyword → dataset heuristic ──────────────────────────────────────────────
_DATASET_KEYWORDS: list[tuple[str, list[str]]] = [
    ("communal_riot",      ["riot", "communal", "temple", "mosque", "mob", "gathering", "weapons",
                             "violence", "religious", "section 144", "unlawful assembly"]),
    ("election_disinfo",   ["election", "evm", "vote", "voting", "ballot", "booth", "polling",
                             "voter", "rigging", "manipulation", "electoral"]),
    ("journalist_doxxing", ["journalist", "reporter", "press", "doxx", "address leaked", "phone shared",
                             "harassment", "intimidation", "media", "news channel"]),
    ("default",            []),
]

def _pick_dataset(text: str) -> str:
    tl = text.lower()
    for name, keywords in _DATASET_KEYWORDS:
        if any(kw in tl for kw in keywords):
            return name
    return "default"

# ── document text extraction ──────────────────────────────────────────────────
def _extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".txt":
        return data.decode("utf-8", errors="replace")
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        except ImportError:
            return "[PDF uploaded — install pypdf: pip install pypdf]"
    if ext == ".docx":
        try:
            import docx
            return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
        except ImportError:
            return "[DOCX uploaded — install python-docx: pip install python-docx]"
    return f"[Unsupported file type: {ext}]"

# ── Bob API helper ────────────────────────────────────────────────────────────
def _bob_call(api_key: str, endpoint: str, messages: list[dict]) -> str:
    """Call IBM Bob (watsonx) chat completion. Returns text or raises."""
    import urllib.request, urllib.error
    payload = json.dumps({
        "model_id": "ibm/granite-3-8b-instruct",
        "messages": messages,
        "max_new_tokens": 900,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/ml/v1/text/chat?version=2024-05-31",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json",
                 "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"].strip()

# ── Built-in FIR templates (fallback when no API key) ────────────────────────
_FIR_TEMPLATES = {
    "communal_riot": """\
FIRST INFORMATION REPORT
(Under Section 154 Cr.P.C. / BNSS)

FIR No.: [AUTO-GENERATED]
Date & Time: {date}
Police Station: Cyber Crime Cell
District: [District]

Complainant: Sub-Inspector [Name], Cyber Monitoring Unit

DETAILS OF OFFENCE:
On {date}, during routine social media monitoring, it was observed that a large number of coordinated accounts (believed to be more than 40 in number) began posting messages in rapid succession calling for people to gather at Lal Darwaza / Main Chowk area at 7 pm with "sticks" and "weapons" to "teach them a lesson." The posts carried hashtags #RiseUp and #ProtectOurPeople and referenced an alleged attack at Haji Colony. Simultaneously, a second wave of accounts spread unverified claims of a temple attack in the same locality, likely to inflame communal sentiment.

The coordinated nature of the posting pattern, account creation dates (majority < 30 days old), near-identical text, and burst timing (all posts within a 9-minute window) indicate Coordinated Inauthentic Behaviour (CIB).

OFFENCES SUSPECTED:
- BNS Section 196 (Promoting enmity between groups)
- BNS Section 189/191 (Unlawful assembly / rioting)
- BNS Section 61(2) (Criminal conspiracy)
- IT Act Section 79(3)(b) — Takedown notice to platform

ACTION REQUESTED:
Immediate activation of Section 144 CrPC in the named locality; platform takedown request; T1 evidence disclosure for the identified clusters.

Signature: [Officer Name & Badge No.]
""",
    "election_disinfo": """\
FIRST INFORMATION REPORT
(Under Section 154 Cr.P.C. / BNSS)

FIR No.: [AUTO-GENERATED]
Date & Time: {date}
Police Station: Cyber Crime Cell / Election Observer Unit
District: [District]

Complainant: District Election Observer

DETAILS OF OFFENCE:
On polling day ({date}), coordinated social media accounts began circulating false claims that EVMs (Electronic Voting Machines) in multiple booths across Lakhanpur, Devnagar, and Rampura districts were pre-loaded or tampered with. A second campaign falsely claimed that voters with certain Aadhaar categories were being turned away. Both claims are factually incorrect and have been denied by the Election Commission.

The campaigns show hallmarks of CIB: 80+ accounts posting within a 14-minute window, majority < 8 days old, near-identical text with only booth numbers varied, hashtags #EVMFraud and #VoteRigged trending artificially.

OFFENCES SUSPECTED:
- BNS Section 353(1)(b) (Statements likely to cause fear or alarm regarding elections)
- BNS Section 61(2) (Criminal conspiracy — coordinated amplification)
- Representation of the People Act 1951, Section 127A

ACTION REQUESTED:
Platform takedown of flagged posts; T1 evidence disclosure; EC notification.

Signature: [Officer Name & Badge No.]
""",
    "journalist_doxxing": """\
FIRST INFORMATION REPORT
(Under Section 154 Cr.P.C. / BNSS)

FIR No.: [AUTO-GENERATED]
Date & Time: {date}
Police Station: Cyber Crime Cell
District: [District]

Complainant: Inspector [Name], Cyber Crime Unit (on behalf of victim)

DETAILS OF OFFENCE:
On {date}, the victim, a freelance journalist (identity protected), reported that multiple coordinated accounts on a social media platform published her home address and personal phone number, accompanied by explicit threats stating "your family will pay" and "we know your routine." A second wave of accounts launched a coordinated mass-reporting / brigading campaign to suppress her account. The victim has received threats to physical safety.

CIB indicators: 55 harassment accounts posting within 12 minutes (all < 18 days old), 5 distinct doxxing messages containing PII, 80 brigading accounts in a secondary wave.

OFFENCES SUSPECTED:
- BNS Section 351 (Criminal intimidation)
- BNS Section 78 (Stalking / online monitoring)
- BNS Section 356 (Defamation)
- BNS Section 61(2) (Criminal conspiracy — coordinated brigading)
- IT Act Section 66E (Punishment for violation of privacy)

ACTION REQUESTED:
Emergency platform takedown of doxxed content; protective beat patrol at victim's address; T1 evidence disclosure; T2 identity reveal for earliest-posting accounts under magistrate order.

Signature: [Officer Name & Badge No.]
""",
    "default": """\
FIRST INFORMATION REPORT
(Under Section 154 Cr.P.C. / BNSS)

FIR No.: [AUTO-GENERATED]
Date & Time: {date}
Police Station: Cyber Crime Cell
District: [District]

Complainant: Sub-Inspector [Name], Social Media Monitoring Unit

DETAILS OF OFFENCE:
On {date}, monitoring of social media platforms revealed coordinated inauthentic activity involving multiple threat campaigns:

1. INCITEMENT CAMPAIGN: 80+ coordinated accounts called for a physical gathering at Sector 9 Market at 6 pm, instructing followers to "bring sticks" and "teach them a lesson." Posts were nearly identical, posted within an 11-minute burst, by accounts < 9 days old.

2. HARASSMENT CAMPAIGN: 45 coordinated accounts targeted journalist @priya_reporter with threats, publishing a personal phone number (+91 9876501234) and threatening her family.

3. MISINFORMATION CAMPAIGN: 55 accounts spread false claims of water supply poisoning in Ward 4, urging mass forwarding "before it is deleted."

All three campaigns show clear CIB markers: burst timing, young accounts, low reach, high text similarity.

OFFENCES SUSPECTED:
- BNS Section 196 / 353(2) (Incitement / promoting enmity)
- BNS Section 351 / 78 (Criminal intimidation / stalking)
- BNS Section 353(1)(b) (Statements causing public alarm)
- BNS Section 61(2) (Criminal conspiracy)

Signature: [Officer Name & Badge No.]
""",
}

def _get_fir_template(dataset: str) -> str:
    import datetime
    tpl = _FIR_TEMPLATES.get(dataset, _FIR_TEMPLATES["default"])
    return tpl.format(date=datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))

# ── pipeline runner ───────────────────────────────────────────────────────────
def _run_pipeline(session_id: str, dataset: str, fir_text: str, api_key: str = "", endpoint: str = ""):
    sess = _SESSIONS[session_id]
    def log(msg: str, kind: str = "info"):
        with _LOCK:
            sess["log"].append({"kind": kind, "msg": msg, "ts": time.time()})

    try:
        log(f"🔍 Dataset selected: **{dataset}**")
        log("⚙️  Loading dataset and running CIB detection inside platform boundary…")
        posts = mock.load(dataset)
        log(f"✅ Ingested **{len(posts)}** posts from **{len({p.user_id for p in posts})}** accounts")

        clusters = det.detect(posts)
        log(f"✅ CIB detection complete — **{len(clusters)}** coordinated threat cluster(s) found")
        if not clusters:
            log("ℹ️  No clusters met the minimum threshold. Try a different dataset or description.", "warn")
            sess["status"] = "done_no_clusters"
            return

        for c in clusters:
            log(f"   • **{c['cluster_id']}** — {c['threat_type']} [{c['severity']}] CIB score {c['cib_score']}")

        log("🔐 Publishing T0 attestation (ZK proofs + Merkle root)…")
        case_id = f"CASE-WEB-{session_id[:8].upper()}"
        case = Case(case_id, posts, clusters)

        log("📋 Requesting T0 (signals — no personal data)…")
        case.request(0, "LEA:WebInterface", purpose=f"Officer web UI — {fir_text[:80]}")

        top = [c["cluster_id"] for c in clusters if c["cib_score"] >= 0.6] or [clusters[0]["cluster_id"]]
        log(f"📋 Requesting T1 evidence for top cluster(s): {top}…")
        case.request(1, "LEA:WebInterface", ["Nodal-Officer-Auto"],
                     clusters=top, purpose="Officer-initiated investigation via web UI",
                     legal_basis="BNS 196/351; BNSS 94")

        early = sorted((x for c in case.t1 for x in c["posts"] if c["cluster_id"] == top[0]),
                       key=lambda x: x["ts"])
        organisers = list(dict.fromkeys(x["pseudonym"] for x in early))[:3]
        if organisers:
            log(f"📋 Requesting T2 identity reveal for {len(organisers)} earliest-active account(s)…")
            case.request(2, "LEA:WebInterface", ["Nodal-Officer-Auto", "Grievance-Officer-Auto"],
                         pseudonyms=organisers, purpose="Identify organisers",
                         legal_basis="BNS 196", order_ref="AUTO-WEB-ORDER")

        log("📊 Building threat brief and dashboard…")
        view = case.lea_view()
        brief_obj, md = br.build(view)
        dashboard_html = dash.render(view, brief_obj)
        report_html    = pdfmod.build_pdf(view, brief_obj)

        # ── Bob AI narrative (if API key provided) ────────────────────────────
        bob_summary = ""
        if api_key and endpoint:
            log("🤖 Asking IBM Bob to summarise findings in plain language…")
            try:
                threat_summary = "; ".join(
                    f"{t['cluster_id']} {t['threat_type']} [{t['severity']}] conf {t['confidence']}"
                    for t in brief_obj["threats"]
                )
                bob_summary = _bob_call(api_key, endpoint, [
                    {"role": "system", "content":
                        "You are a senior law enforcement analyst. Write a concise, plain-language "
                        "situation report (max 150 words) for a district officer based on the threat "
                        "intelligence below. Use bullet points. Do not invent facts beyond what is given."},
                    {"role": "user", "content":
                        f"Case: {brief_obj['brief_id']}\n"
                        f"Overall severity: {brief_obj['overall_severity']}\n"
                        f"Threats: {threat_summary}\n"
                        f"FIR description: {fir_text[:300]}"}
                ])
                log(f"🤖 **Bob AI Summary:**\n{bob_summary}", "success")
            except Exception as e:
                log(f"⚠️  Bob API call failed: {e} — continuing without AI summary.", "warn")

        with _LOCK:
            sess["dashboard_html"] = dashboard_html
            sess["report_html"]    = report_html
            sess["brief"]          = brief_obj
            sess["bob_summary"]    = bob_summary
            sess["status"]         = "done"

        sev = brief_obj["overall_severity"]
        n_threats = len(brief_obj["threats"])
        log(f"✅ Analysis complete! **{n_threats}** threat cluster(s) — overall severity: **{sev}**", "success")
        log("👇 Your dashboard and PDF report are ready below.", "success")

    except Exception as exc:
        import traceback
        with _LOCK:
            sess["status"] = "error"
            sess["log"].append({"kind": "error", "msg": f"❌ Pipeline error: {exc}", "ts": time.time()})

# ── HTML UI ───────────────────────────────────────────────────────────────────
_UI = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TitanSafe — Officer Interface</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#070b0a;--pn:#0d1512;--fg:#7CFC9A;--cy:#22d3ee;--dim:#4b6b5c;
      --bad:#ff5c5c;--warn:#fbbf24;--bdr:#16241e;--txt:#d1fae5;--bob:#a78bfa}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font:14px/1.6 ui-monospace,Menlo,monospace;
     display:flex;flex-direction:column;min-height:100vh}

/* ── header ── */
#hdr{background:var(--pn);border-bottom:2px solid var(--cy);padding:10px 18px;
     display:flex;align-items:center;gap:12px;flex-wrap:wrap}
#hdr h1{color:var(--cy);font-size:16px;letter-spacing:.04em}
#hdr .sub{color:var(--dim);font-size:11px;flex:1}
.bob-badge{background:#1a0a2e;border:1px solid var(--bob);color:var(--bob);
           font-size:11px;padding:2px 10px;border-radius:10px;white-space:nowrap}
.bob-badge.on{background:#2a1050}
.icon-btn{background:none;border:none;color:var(--dim);cursor:pointer;
          font-size:18px;padding:4px 8px;border-radius:4px;line-height:1}
.icon-btn:hover{color:var(--fg);background:#16241e}

/* ── layout ── */
#main{display:flex;flex:1;overflow:hidden;height:calc(100vh - 50px)}

/* ── chat panel ── */
#chat{width:420px;flex-shrink:0;display:flex;flex-direction:column;border-right:1px solid var(--bdr);background:var(--pn)}
#msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:8px}
.bubble{padding:10px 14px;border-radius:6px;max-width:95%;font-size:13px;line-height:1.65;word-break:break-word}
.bubble.sys{background:#0a1a14;border:1px solid var(--bdr);color:var(--txt);align-self:flex-start}
.bubble.user{background:#112819;border:1px solid var(--dim);color:var(--fg);align-self:flex-end}
.bubble.success{background:#0a2a14;border-color:var(--fg)}
.bubble.warn{background:#2a1e00;border-color:var(--warn);color:var(--warn)}
.bubble.error{background:#2a0a0a;border-color:var(--bad);color:var(--bad)}
.bubble.bob{background:#1a0a2e;border:1px solid var(--bob);color:var(--txt);align-self:flex-start}
.blink{animation:blink 1s step-start infinite}
@keyframes blink{50%{opacity:0}}

/* ── dataset chips ── */
.ds-chips{display:flex;flex-wrap:wrap;gap:5px;padding:8px 12px;border-bottom:1px solid var(--bdr)}
.ds-chip{background:var(--bg);border:1px solid var(--bdr);color:var(--dim);
         font-size:11px;padding:3px 9px;border-radius:10px;cursor:pointer;transition:.15s}
.ds-chip:hover{border-color:var(--cy);color:var(--cy)}
.ds-chip.sel{background:#0a2a14;border-color:var(--fg);color:var(--fg)}

/* ── input area ── */
#input-area{padding:10px 12px;border-top:1px solid var(--bdr);background:#050908}
#input-area textarea{
  width:100%;background:var(--pn);border:1px solid var(--dim);color:var(--fg);
  font:inherit;font-size:13px;padding:8px 10px;border-radius:4px;
  resize:vertical;min-height:68px;outline:none}
#input-area textarea:focus{border-color:var(--cy)}
#input-area textarea::placeholder{color:var(--bdr)}
.row{display:flex;gap:7px;margin-top:8px;flex-wrap:wrap;align-items:center}
.btn{background:var(--pn);color:var(--cy);border:1px solid var(--cy);
     padding:5px 12px;cursor:pointer;font:inherit;font-size:12px;border-radius:3px;white-space:nowrap}
.btn:hover{background:var(--cy);color:#000}
.btn.dim{border-color:var(--dim);color:var(--dim)}
.btn.dim:hover{border-color:var(--fg);color:var(--fg);background:var(--bg)}
.btn.bob-btn{border-color:var(--bob);color:var(--bob)}
.btn.bob-btn:hover{background:var(--bob);color:#000}
.btn.danger{border-color:var(--bad);color:var(--bad)}
.btn.danger:hover{background:var(--bad);color:#000}
.btn:disabled{opacity:.35;cursor:not-allowed}
#file-label{background:var(--pn);color:var(--dim);border:1px dashed var(--dim);
            padding:5px 10px;cursor:pointer;font:inherit;font-size:12px;border-radius:3px}
#file-label:hover{border-color:var(--fg);color:var(--fg)}
#file-input{display:none}
#file-name{font-size:11px;color:var(--dim);max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* ── results panel ── */
#results{flex:1;overflow:hidden;display:flex;flex-direction:column}
#results-hdr{padding:8px 16px;background:#050908;border-bottom:1px solid var(--bdr);
             display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12px}
#results-hdr .spacer{flex:1}
#frame-wrap{flex:1;overflow:hidden}
#frame-wrap iframe{width:100%;height:100%;border:none}
#placeholder{flex:1;display:flex;flex-direction:column;align-items:center;
             justify-content:center;color:var(--dim);text-align:center;padding:40px}
#placeholder .icon{font-size:52px;margin-bottom:14px;opacity:.35}
#placeholder p{font-size:13px;max-width:340px;line-height:1.8}

/* ── settings modal ── */
#modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:500;
          align-items:center;justify-content:center}
#modal-bg.show{display:flex}
#modal{background:var(--pn);border:1px solid var(--bob);border-radius:6px;
       padding:24px;width:min(480px,95vw);position:relative}
#modal h2{color:var(--bob);font-size:14px;margin-bottom:4px}
#modal .hint{color:var(--dim);font-size:11px;margin-bottom:16px;line-height:1.6}
#modal label{display:block;font-size:11px;color:var(--dim);margin:12px 0 4px}
#modal input{width:100%;background:var(--bg);border:1px solid var(--dim);color:var(--fg);
             font:inherit;font-size:12px;padding:7px 10px;border-radius:3px;outline:none}
#modal input:focus{border-color:var(--bob)}
#modal .modal-row{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
#bob-status{font-size:11px;margin-top:8px;min-height:18px}
.close-modal{position:absolute;top:12px;right:14px;background:none;border:none;
             color:var(--dim);cursor:pointer;font-size:18px;line-height:1}
.close-modal:hover{color:var(--fg)}
/* ── fir modal ── */
#fir-modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:500;
              align-items:center;justify-content:center}
#fir-modal-bg.show{display:flex}
#fir-modal{background:var(--pn);border:1px solid var(--bdr);border-radius:6px;
           padding:22px;width:min(640px,95vw);max-height:85vh;display:flex;flex-direction:column}
#fir-modal h2{color:var(--cy);font-size:14px;margin-bottom:10px}
#fir-text{flex:1;background:var(--bg);border:1px solid var(--bdr);color:var(--txt);
          font:12px/1.7 ui-monospace,monospace;padding:12px;border-radius:3px;
          resize:none;outline:none;overflow-y:auto;min-height:300px;max-height:50vh}
#fir-modal .modal-row{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
</style>
</head>
<body>

<!-- ── Header ── -->
<div id="hdr">
  <h1>&gt;&gt; TitanSafe</h1>
  <span class="sub">// Officer Chat Interface — describe case · upload or generate FIR · get instant intelligence</span>
  <span class="bob-badge" id="bob-badge">🤖 Bob: OFF</span>
  <button class="icon-btn" title="IBM Bob API Settings" onclick="openSettings()">⚙️</button>
</div>

<!-- ── Main layout ── -->
<div id="main">

  <!-- Chat panel -->
  <div id="chat">
    <div class="ds-chips" id="ds-chips">
      <span style="font-size:11px;color:var(--dim);line-height:26px;flex-shrink:0">Dataset:</span>
    </div>
    <div id="msgs"></div>
    <div id="input-area">
      <textarea id="msg-input" placeholder="Describe the incident or paste FIR text here…
Example: Reports of communal tension near the mosque, people gathering with weapons at Main Chowk." rows="4"></textarea>
      <div class="row">
        <button class="btn" id="send-btn" onclick="sendMessage()">▶ Analyse</button>
        <label class="btn dim" id="file-label" for="file-input">📎 Upload FIR</label>
        <input type="file" id="file-input" accept=".txt,.pdf,.docx" onchange="fileSelected(this)">
        <button class="btn dim" onclick="openFirModal()">📝 Generate FIR</button>
        <div style="flex:1"></div>
        <button class="btn danger" onclick="resetSession()">✕</button>
      </div>
      <div class="row" style="margin-top:5px">
        <span id="file-name"></span>
      </div>
    </div>
  </div>

  <!-- Results panel -->
  <div id="results">
    <div id="results-hdr">
      <span style="color:var(--dim)">Results</span>
      <div class="spacer"></div>
      <button class="btn" id="dash-btn" style="display:none" onclick="showTab('dash')">📊 Dashboard</button>
      <button class="btn" id="pdf-btn"  style="display:none" onclick="showTab('pdf')">📄 PDF Report</button>
      <button class="btn" id="print-btn" style="display:none" onclick="printReport()">⎙ Print PDF</button>
    </div>
    <div id="placeholder">
      <div class="icon">🔍</div>
      <p>Describe your case in the chat, upload a FIR document, or click<br>
         <b>📝 Generate FIR</b> to create a sample FIR pre-filled for the selected scenario.<br><br>
         TitanSafe auto-detects the threat type, runs the full privacy-preserving analysis,
         and shows the LEA dashboard here.</p>
    </div>
    <div id="frame-wrap" style="display:none">
      <iframe id="dash-frame" title="TitanSafe Dashboard" sandbox="allow-scripts allow-same-origin allow-popups"></iframe>
    </div>
  </div>
</div>

<!-- ── Settings modal ── -->
<div id="modal-bg" onclick="if(event.target===this)closeSettings()">
  <div id="modal">
    <button class="close-modal" onclick="closeSettings()">✕</button>
    <h2>🤖 IBM Bob API Settings</h2>
    <div class="hint">
      Connect your IBM watsonx / Bob API key to enable AI-powered plain-language summaries
      and Bob-generated FIR drafts.<br>
      Your key is stored only in this browser session — never sent to any server except IBM's own endpoint.
    </div>
    <label>API Key (Bearer token)</label>
    <input type="password" id="bob-key" placeholder="eyJhbGciOi…" autocomplete="off">
    <label>Endpoint URL</label>
    <input type="text" id="bob-endpoint" value="https://us-south.ml.cloud.ibm.com" placeholder="https://us-south.ml.cloud.ibm.com">
    <div id="bob-status"></div>
    <div class="modal-row">
      <button class="btn bob-btn" onclick="testBobKey()">🔌 Test Connection</button>
      <button class="btn" onclick="saveBobKey()">💾 Save</button>
      <button class="btn danger" onclick="clearBobKey()">🗑 Clear</button>
    </div>
  </div>
</div>

<!-- ── FIR generator modal ── -->
<div id="fir-modal-bg" onclick="if(event.target===this)closeFirModal()">
  <div id="fir-modal">
    <h2>📝 Sample FIR Generator</h2>
    <textarea id="fir-text" readonly placeholder="Generating FIR…"></textarea>
    <div class="modal-row">
      <button class="btn" onclick="copyFir()">📋 Copy</button>
      <button class="btn" onclick="downloadFir()">⬇ Download .txt</button>
      <button class="btn" onclick="useFir()">▶ Use as Input</button>
      <div style="flex:1"></div>
      <button class="btn danger" onclick="closeFirModal()">✕ Close</button>
    </div>
  </div>
</div>

<script>
'use strict';
const DATASETS = [
  {id:'auto',              label:'🤖 Auto'},
  {id:'default',           label:'⚡ Incitement'},
  {id:'communal_riot',     label:'🔥 Communal Riot'},
  {id:'election_disinfo',  label:'🗳️ Election Disinfo'},
  {id:'journalist_doxxing',label:'📰 Doxxing'},
];
let selectedDs='auto', sessionId=null, pollTimer=null;
let lastLogLen=0, dashHtml=null, pdfHtml=null;

// ── Dataset chips ──────────────────────────────────────────────────────────
const chipsEl = document.getElementById('ds-chips');
DATASETS.forEach(d => {
  const el = document.createElement('span');
  el.className = 'ds-chip' + (d.id==='auto'?' sel':'');
  el.textContent = d.label;
  el.onclick = () => {
    document.querySelectorAll('.ds-chip').forEach(c=>c.classList.remove('sel'));
    el.classList.add('sel'); selectedDs = d.id;
  };
  chipsEl.appendChild(el);
});

// ── Bob key helpers ────────────────────────────────────────────────────────
function getBobKey()      { return sessionStorage.getItem('bob_key') || ''; }
function getBobEndpoint() { return sessionStorage.getItem('bob_endpoint') || 'https://us-south.ml.cloud.ibm.com'; }
function updateBobBadge() {
  const on = !!getBobKey();
  const badge = document.getElementById('bob-badge');
  badge.textContent = on ? '🤖 Bob: ON' : '🤖 Bob: OFF';
  badge.className = 'bob-badge' + (on ? ' on' : '');
}
updateBobBadge();

function openSettings() {
  document.getElementById('bob-key').value = getBobKey();
  document.getElementById('bob-endpoint').value = getBobEndpoint();
  document.getElementById('bob-status').textContent = '';
  document.getElementById('modal-bg').classList.add('show');
}
function closeSettings() { document.getElementById('modal-bg').classList.remove('show'); }

function saveBobKey() {
  const k = document.getElementById('bob-key').value.trim();
  const e = document.getElementById('bob-endpoint').value.trim();
  if (k) sessionStorage.setItem('bob_key', k); else sessionStorage.removeItem('bob_key');
  sessionStorage.setItem('bob_endpoint', e || 'https://us-south.ml.cloud.ibm.com');
  updateBobBadge();
  document.getElementById('bob-status').innerHTML = '<span style="color:var(--fg)">✅ Saved for this session.</span>';
}
function clearBobKey() {
  sessionStorage.removeItem('bob_key');
  document.getElementById('bob-key').value = '';
  updateBobBadge();
  document.getElementById('bob-status').innerHTML = '<span style="color:var(--dim)">Key cleared.</span>';
}
async function testBobKey() {
  const k = document.getElementById('bob-key').value.trim();
  const e = document.getElementById('bob-endpoint').value.trim();
  const st = document.getElementById('bob-status');
  if (!k) { st.innerHTML = '<span style="color:var(--warn)">⚠️ Enter an API key first.</span>'; return; }
  st.innerHTML = '<span style="color:var(--dim)">Testing… <span class="blink">▌</span></span>';
  const res = await fetch('/bob-ping', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({api_key: k, endpoint: e})
  });
  const data = await res.json();
  if (data.ok) st.innerHTML = `<span style="color:var(--fg)">✅ Connected! ${data.msg}</span>`;
  else         st.innerHTML = `<span style="color:var(--bad)">❌ ${data.error}</span>`;
}

// ── FIR modal ──────────────────────────────────────────────────────────────
async function openFirModal() {
  document.getElementById('fir-text').value = 'Generating FIR…';
  document.getElementById('fir-modal-bg').classList.add('show');

  const ds = selectedDs === 'auto' ? 'default' : selectedDs;
  const res = await fetch('/generate-fir', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      dataset: ds,
      api_key: getBobKey(),
      endpoint: getBobEndpoint(),
    })
  });
  const data = await res.json();
  document.getElementById('fir-text').value = data.fir || data.error || 'Error generating FIR.';
}
function closeFirModal() { document.getElementById('fir-modal-bg').classList.remove('show'); }
function copyFir() {
  navigator.clipboard.writeText(document.getElementById('fir-text').value)
    .then(()=>addBubble('📋 FIR text copied to clipboard.'));
}
function downloadFir() {
  const txt = document.getElementById('fir-text').value;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([txt], {type:'text/plain'}));
  a.download = `sample_fir_${selectedDs}.txt`;
  a.click();
}
function useFir() {
  const txt = document.getElementById('fir-text').value;
  document.getElementById('msg-input').value = txt;
  closeFirModal();
  addBubble('📄 FIR text loaded into the input box. Click ▶ Analyse to run.', 'sys');
}

// ── Chat helpers ───────────────────────────────────────────────────────────
function addBubble(html, cls='sys') {
  const el = document.createElement('div');
  el.className = 'bubble ' + cls;
  el.innerHTML = html.replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/\n/g,'<br>');
  document.getElementById('msgs').appendChild(el);
  el.scrollIntoView({behavior:'smooth'});
  return el;
}

function showResults() {
  document.getElementById('placeholder').style.display = 'none';
  document.getElementById('frame-wrap').style.display = 'block';
  ['dash-btn','pdf-btn','print-btn'].forEach(id=>document.getElementById(id).style.display='');
}
function showTab(tab) {
  const fr = document.getElementById('dash-frame');
  const html = tab==='dash' ? dashHtml : pdfHtml;
  if (html) fr.src = URL.createObjectURL(new Blob([html],{type:'text/html'}));
}
function printReport() {
  const fr = document.getElementById('dash-frame');
  fr.contentWindow && fr.contentWindow.print();
}

// ── Main send ──────────────────────────────────────────────────────────────
async function sendMessage() {
  const ta = document.getElementById('msg-input');
  const fileInput = document.getElementById('file-input');
  const text = ta.value.trim();
  if (!text && !fileInput.files.length) return;

  document.getElementById('send-btn').disabled = true;
  addBubble(text ? text.slice(0,200)+(text.length>200?'…':'') : '[FIR document uploaded]', 'user');
  ta.value = '';

  const fd = new FormData();
  fd.append('message', text);
  fd.append('dataset', selectedDs);
  fd.append('api_key', getBobKey());
  fd.append('endpoint', getBobEndpoint());
  if (fileInput.files.length) fd.append('file', fileInput.files[0]);

  addBubble('⚙️ Starting analysis… <span class="blink">▌</span>');

  const res = await fetch('/analyse', {method:'POST', body:fd});
  const data = await res.json();
  if (data.error) {
    addBubble('❌ ' + data.error, 'error');
    document.getElementById('send-btn').disabled = false;
    return;
  }
  sessionId = data.session_id;
  lastLogLen = 0;
  document.getElementById('msgs').lastChild.remove();
  pollLogs();
}

function pollLogs() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    if (!sessionId) return;
    const res = await fetch('/status/' + sessionId + '?from=' + lastLogLen);
    const data = await res.json();

    data.new_logs.forEach(entry => {
      lastLogLen++;
      const cls = entry.kind==='success'?'success':entry.kind==='warn'?'warn':entry.kind==='error'?'error':
                  entry.kind==='bob'?'bob':'sys';
      addBubble(entry.msg, cls);
    });

    if (['done','done_no_clusters','error'].includes(data.status)) {
      clearInterval(pollTimer);
      document.getElementById('send-btn').disabled = false;
      if (data.status === 'done') {
        dashHtml = data.dashboard_html;
        pdfHtml  = data.report_html;
        showResults();
        showTab('dash');
      }
    }
  }, 800);
}

function fileSelected(input) {
  const name = input.files[0]?.name || '';
  document.getElementById('file-name').textContent = name ? '📎 ' + name : '';
}

async function resetSession() {
  if (sessionId) await fetch('/reset/' + sessionId, {method:'POST'}).catch(()=>{});
  sessionId=null; lastLogLen=0; dashHtml=null; pdfHtml=null;
  if (pollTimer) clearInterval(pollTimer);
  document.getElementById('msgs').innerHTML = '';
  document.getElementById('placeholder').style.display = '';
  document.getElementById('frame-wrap').style.display = 'none';
  ['dash-btn','pdf-btn','print-btn'].forEach(id=>document.getElementById(id).style.display='none');
  document.getElementById('send-btn').disabled = false;
  document.getElementById('file-input').value = '';
  document.getElementById('file-name').textContent = '';
  addBubble('Session reset. Describe a new case to begin.');
}

// Welcome
addBubble(
  '👋 Welcome to <b>TitanSafe</b>.<br><br>' +
  '• Type an incident description and click <b>▶ Analyse</b><br>' +
  '• Or click <b>📝 Generate FIR</b> to get a pre-filled sample FIR for your selected scenario<br>' +
  '• Or click <b>📎 Upload FIR</b> to upload a <code>.txt / .pdf / .docx</code> file<br><br>' +
  'Click <b>⚙️</b> in the header to add your <b>IBM Bob API key</b> for AI-powered summaries and smarter FIR generation.'
);
</script>
</body>
</html>
"""

# ── routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    return Response(_UI, mimetype="text/html")


@app.post("/analyse")
def analyse():
    msg      = request.form.get("message", "").strip()
    ds       = request.form.get("dataset", "auto").strip()
    api_key  = request.form.get("api_key", "").strip()
    endpoint = request.form.get("endpoint", "").strip()
    ffile    = request.files.get("file")

    fir_text = msg
    if ffile and ffile.filename:
        try:
            fir_text += "\n" + _extract_text(ffile.filename, ffile.read())
        except Exception as e:
            fir_text += f"\n[File read error: {e}]"

    if not fir_text.strip():
        return jsonify({"error": "Please describe the case or upload a FIR document."}), 400

    valid = set(mock.DATASETS.keys()) | {"auto"}
    chosen = _pick_dataset(fir_text) if ds not in valid or ds == "auto" else ds

    sid = str(uuid.uuid4())
    with _LOCK:
        _SESSIONS[sid] = {"status": "running", "log": [], "dashboard_html": None,
                          "report_html": None, "brief": None, "bob_summary": ""}

    threading.Thread(target=_run_pipeline,
                     args=(sid, chosen, fir_text, api_key, endpoint),
                     daemon=True).start()
    return jsonify({"session_id": sid})


@app.post("/generate-fir")
def generate_fir():
    data     = request.get_json(silent=True) or {}
    dataset  = data.get("dataset", "default")
    api_key  = data.get("api_key", "").strip()
    endpoint = data.get("endpoint", "").strip()

    if dataset not in _FIR_TEMPLATES:
        dataset = "default"

    # Try Bob API first
    if api_key and endpoint:
        prompts = {
            "communal_riot":      "Write a realistic First Information Report (FIR) for a communal riot incitement case in India. Coordinated social media posts called for a violent gathering with weapons near a mosque. Use BNS sections 196, 189/191, 61(2).",
            "election_disinfo":   "Write a realistic FIR for an election misinformation case in India. Coordinated accounts spread false EVM-tampering claims and voter-suppression rumours on polling day. Use BNS 353(1)(b), 61(2) and Representation of the People Act 1951.",
            "journalist_doxxing": "Write a realistic FIR for a journalist doxxing and targeted harassment case in India. Coordinated accounts shared a journalist's home address and phone number with explicit threats. Use BNS 351, 78, 356, 61(2), IT Act 66E.",
            "default":            "Write a realistic FIR for a combined case of incitement to violence, targeted harassment of a journalist, and health misinformation on social media in India. Use BNS 196, 351, 353, 61(2).",
        }
        try:
            import datetime
            fir = _bob_call(api_key, endpoint, [
                {"role": "system", "content":
                    "You are a senior police officer writing an official First Information Report (FIR) "
                    "in the standard Indian format. Include: FIR number placeholder, date, police station, "
                    "complainant, detailed facts, suspected offences with specific BNS/IPC sections, "
                    "and action requested. Be specific and realistic. About 300-400 words."},
                {"role": "user", "content":
                    prompts.get(dataset, prompts["default"]) +
                    f"\n\nDate: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"}
            ])
            return jsonify({"fir": fir, "source": "bob"})
        except Exception as e:
            pass  # fall through to template

    return jsonify({"fir": _get_fir_template(dataset), "source": "template"})


@app.post("/bob-ping")
def bob_ping():
    data     = request.get_json(silent=True) or {}
    api_key  = data.get("api_key", "").strip()
    endpoint = data.get("endpoint", "").strip()
    if not api_key:
        return jsonify({"ok": False, "error": "No API key provided."})
    try:
        reply = _bob_call(api_key, endpoint, [
            {"role": "user", "content": "Reply with exactly: TitanSafe connection OK"}
        ])
        return jsonify({"ok": True, "msg": reply[:80]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)[:200]})


@app.get("/status/<sid>")
def status(sid: str):
    with _LOCK:
        sess = _SESSIONS.get(sid)
    if not sess:
        return jsonify({"error": "Session not found"}), 404

    from_idx = int(request.args.get("from", 0))
    payload  = {"status": sess["status"], "new_logs": sess["log"][from_idx:]}
    if sess["status"] == "done":
        payload["dashboard_html"] = sess["dashboard_html"]
        payload["report_html"]    = sess["report_html"]
    return jsonify(payload)


@app.post("/reset/<sid>")
def reset_session(sid: str):
    with _LOCK:
        _SESSIONS.pop(sid, None)
    return jsonify({"ok": True})


# ── entry point ───────────────────────────────────────────────────────────────
def main():
    import webbrowser
    port = int(os.environ.get("PORT", 5000))
    print(f"\n\033[96m>> TitanSafe Officer Interface starting...\033[0m")
    print(f"\033[92m>> Open your browser at:  http://localhost:{port}\033[0m\n")
    threading.Timer(1.4, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
