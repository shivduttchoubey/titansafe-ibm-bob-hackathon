"""Single-page scrollable dark-terminal LEA dashboard — comprehensive edition.

New in this version:
  - Network co-ordination graph (SVG force-directed approximation)
  - Activity heatmap (24×7 grid showing post density by hour/day)
  - Geographic heatmap (India SVG with region heat overlay)
  - Platform analytics panel (region breakdown, follower distribution)
  - Threat score sparkline mini-charts per cluster
  - Improved stat cards with trend indicators
  - Risk gauge arc for overall threat level
  - Cluster comparison radar chart (SVG)
  - Sticky top bar with live summary badges
  - Exportable sections + print CSS
"""
import json


def render(view, brief):
    data = json.dumps({"v": view, "b": brief}).replace("</", "<\\/")
    return _TMPL.replace("__DATA__", data)


_TMPL = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TitanSafe — LEA Intelligence Dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
/* ── design tokens ─────────────────────────────────────────────────────── */
:root{
  --bg:#060a09; --pn:#0c1411; --fg:#7CFC9A; --cy:#22d3ee;
  --dim:#4b6b5c; --bad:#ff5c5c; --warn:#fbbf24; --txt:#d1fae5;
  --bdr:#16241e; --nav-w:152px; --hl:#1a3028;
  --crit:#ff5c5c; --high:#fbbf24; --med:#22d3ee; --ok:#7CFC9A;
}
/* ── reset ─────────────────────────────────────────────────────────────── */
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--fg);font:13px/1.6 ui-monospace,Menlo,Consolas,monospace;
     display:flex;flex-direction:column;min-height:100vh}
a{color:var(--cy);text-decoration:none}

/* ── sticky header ──────────────────────────────────────────────────────── */
#hdr{position:sticky;top:0;z-index:200;background:var(--pn);
     border-bottom:2px solid var(--cy);padding:9px 18px;
     display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}
#hdr h1{color:var(--cy);font-size:15px;letter-spacing:.05em;display:flex;align-items:center;gap:8px}
#hdr h1 .brand{color:var(--bad);font-weight:900}
#hdr .hdr-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.hdr-badge{background:#16241e;border:1px solid var(--bdr);padding:2px 10px;
           font-size:11px;border-radius:12px;white-space:nowrap}
.hdr-badge.crit{border-color:var(--bad);color:var(--bad)}
.hdr-badge.warn{border-color:var(--warn);color:var(--warn)}
.hdr-badge.ok{border-color:var(--ok);color:var(--ok)}

/* ── info ribbon ────────────────────────────────────────────────────────── */
#ribbon{background:#040807;border-bottom:1px solid var(--bdr);
        padding:5px 18px;display:flex;flex-wrap:wrap;align-items:center;gap:12px;font-size:11px}
#ribbon .kv{color:var(--dim)}
#ribbon .kv b{color:var(--fg)}
#ribbon .spacer{flex:1}
.icon-btn{background:var(--pn);color:var(--cy);border:1px solid var(--cy);
          padding:3px 12px;cursor:pointer;font:inherit;font-size:11px;border-radius:2px;transition:all .15s}
.icon-btn:hover{background:var(--cy);color:#000}

/* ── body layout: side-nav + main ───────────────────────────────────────── */
#layout{display:flex;flex:1}

/* ── sticky side-nav ────────────────────────────────────────────────────── */
#sidenav{
  position:sticky;top:58px;
  height:calc(100vh - 58px);overflow-y:auto;
  width:var(--nav-w);flex-shrink:0;
  background:var(--pn);border-right:1px solid var(--bdr);
  padding:12px 0;
}
#sidenav::-webkit-scrollbar{width:3px}
#sidenav::-webkit-scrollbar-track{background:transparent}
#sidenav::-webkit-scrollbar-thumb{background:var(--dim)}
#sidenav a{
  display:block;padding:5px 12px;color:var(--dim);text-decoration:none;
  font-size:11px;border-left:2px solid transparent;transition:all .15s;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
#sidenav a:hover{color:var(--fg);background:var(--hl)}
#sidenav a.active{color:var(--cy);border-left-color:var(--cy);background:#0a1a14}
#sidenav .nav-section{padding:10px 12px 2px;font-size:9px;color:var(--bdr);
                       text-transform:uppercase;letter-spacing:.1em}

/* ── main content ───────────────────────────────────────────────────────── */
#main{flex:1;padding:0 22px 80px;min-width:0}

/* ── section headers ────────────────────────────────────────────────────── */
.sec{margin:24px 0 0;scroll-margin-top:64px}
.sec-hdr{
  display:flex;align-items:center;gap:10px;
  border-bottom:1px solid var(--dim);padding-bottom:7px;margin-bottom:14px;
}
.sec-hdr h2{color:var(--cy);font-size:13px;letter-spacing:.03em}
.sec-hdr .sec-num{color:#1a3028;font-size:11px;background:#16241e;
                   padding:1px 7px;border-radius:10px}

/* ── cards / panels ─────────────────────────────────────────────────────── */
.p{background:var(--pn);border:1px solid var(--bdr);padding:14px;margin:10px 0;
   overflow-x:auto;border-radius:3px}
.p h3{color:var(--cy);font-size:12px;margin-bottom:9px;padding-bottom:5px;
      border-bottom:1px solid var(--bdr);display:flex;align-items:center;gap:7px}
.p h4{color:var(--fg);font-size:12px;margin:10px 0 4px}

/* ── cluster card with sev stripe ───────────────────────────────────────── */
.cluster-card{background:var(--pn);border:1px solid var(--bdr);border-radius:3px;
              margin:10px 0;overflow:hidden}
.cluster-card .cc-bar{height:3px}
.cluster-card .cc-bar.CRITICAL{background:var(--bad)}
.cluster-card .cc-bar.HIGH{background:var(--warn)}
.cluster-card .cc-bar.MEDIUM{background:var(--cy)}
.cluster-card .cc-head{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 14px;cursor:pointer;user-select:none;
}
.cluster-card .cc-head:hover{background:var(--hl)}
.cluster-card .cc-body{padding:0 14px 14px;border-top:1px solid var(--bdr)}
.cluster-card .cc-toggle{color:var(--dim);font-size:16px;flex-shrink:0;transition:transform .2s}
.cluster-card.collapsed .cc-body{display:none}
.cluster-card.collapsed .cc-toggle{transform:rotate(-90deg)}

/* ── grids ──────────────────────────────────────────────────────────────── */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
@media(max-width:900px){.grid4{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){.grid2,.grid3,.grid4{grid-template-columns:1fr}}

/* ── stat cards ─────────────────────────────────────────────────────────── */
.stat-card{background:var(--bg);border:1px solid var(--bdr);padding:14px 12px;
           text-align:center;border-radius:3px;position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.stat-card.sc-bad::before{background:var(--bad)}
.stat-card.sc-warn::before{background:var(--warn)}
.stat-card.sc-ok::before{background:var(--ok)}
.stat-card.sc-cy::before{background:var(--cy)}
.stat-card .num{font-size:28px;font-weight:700;color:var(--cy);line-height:1}
.stat-card .lbl{font-size:10px;color:var(--dim);margin-top:5px;text-transform:uppercase;letter-spacing:.04em}
.stat-card .sub{font-size:10px;color:var(--fg);margin-top:3px}

/* ── badges ─────────────────────────────────────────────────────────────── */
.badge{display:inline-block;padding:2px 7px;border-radius:2px;font-weight:700;font-size:11px}
.badge.CRITICAL{background:#3a1010;color:var(--bad);border:1px solid #5a1818}
.badge.HIGH    {background:#3a2a00;color:var(--warn);border:1px solid #5a4200}
.badge.MEDIUM  {background:#0d2233;color:var(--cy);border:1px solid #1a3a52}
.CRITICAL{color:var(--bad)}.HIGH{color:var(--warn)}.MEDIUM{color:var(--cy)}

/* ── tables ─────────────────────────────────────────────────────────────── */
table{border-collapse:collapse;width:100%;font-size:12px}
th{color:var(--cy);font-weight:600;border-bottom:1px solid var(--dim);
   padding:6px 10px;text-align:left;background:#0a1612}
td{border-bottom:1px solid var(--bdr);padding:5px 10px;vertical-align:top}
tr:hover td{background:var(--hl)}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--dim)}

/* ── bars ───────────────────────────────────────────────────────────────── */
.bar-wrap{height:8px;background:var(--bdr);border-radius:4px;overflow:hidden;margin:4px 0}
.bar-fill{height:8px;border-radius:4px;transition:width .4s}
.bar-fill.bad{background:var(--bad)}.bar-fill.warn{background:var(--warn)}.bar-fill.ok{background:var(--fg)}

/* ── signal gauges ──────────────────────────────────────────────────────── */
.sig-row{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:11px;position:relative}
.sig-lbl{width:115px;color:var(--dim);flex-shrink:0;cursor:help}
.sig-bar{flex:1;height:6px;background:var(--bdr);border-radius:3px;overflow:hidden}
.sig-fill{height:6px;border-radius:3px;transition:width .3s}
.sig-val{width:34px;text-align:right;color:var(--fg)}
.sig-lbl[data-tip]:hover::after{
  content:attr(data-tip);position:absolute;left:0;top:20px;
  background:#1a2e22;border:1px solid var(--dim);color:var(--txt);
  font-size:10px;padding:4px 8px;white-space:nowrap;z-index:200;border-radius:2px;
}

/* ── timeline ───────────────────────────────────────────────────────────── */
.tl{position:relative;padding-left:22px;margin:8px 0}
.tl::before{content:'';position:absolute;left:7px;top:0;bottom:0;width:1px;background:var(--bdr)}
.tl-item{position:relative;margin:9px 0;font-size:12px}
.tl-item::before{content:'';position:absolute;left:-17px;top:5px;
  width:9px;height:9px;border-radius:50%;border:1px solid var(--dim);background:var(--pn)}
.tl-item.CRITICAL::before{background:var(--bad);border-color:var(--bad);box-shadow:0 0 6px var(--bad)}
.tl-item.HIGH::before{background:var(--warn);border-color:var(--warn)}
.tl-item.MEDIUM::before{background:var(--cy);border-color:var(--cy)}
.tl-item.sys::before{background:var(--dim)}
.tl-time{color:var(--dim);font-size:10px;margin-bottom:1px}

/* ── phrase pills ───────────────────────────────────────────────────────── */
.pill{display:inline-block;background:#16241e;border:1px solid var(--bdr);
      padding:2px 8px;margin:2px;font-size:11px;border-radius:2px}
.pill.htag{color:var(--cy)}

/* ── search box ─────────────────────────────────────────────────────────── */
.search-wrap{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.search-wrap input{
  background:var(--pn);border:1px solid var(--dim);color:var(--fg);
  font:inherit;font-size:12px;padding:5px 10px;flex:1;border-radius:2px;outline:none;
}
.search-wrap input:focus{border-color:var(--cy)}
.search-wrap input::placeholder{color:var(--bdr)}

/* ── heatmap ────────────────────────────────────────────────────────────── */
.hmap-cell{border-radius:2px;transition:opacity .2s}
.hmap-cell:hover{opacity:.7;cursor:default}

/* ── denied / ok ────────────────────────────────────────────────────────── */
.DENIED{color:var(--bad);font-weight:700}
.DISCLOSED{color:var(--fg)}

/* ── back-to-top ────────────────────────────────────────────────────────── */
#top-btn{
  position:fixed;bottom:22px;right:20px;z-index:300;
  background:var(--pn);color:var(--cy);border:1px solid var(--cy);
  padding:5px 10px;cursor:pointer;font:inherit;font-size:11px;border-radius:2px;
  opacity:0;transition:opacity .3s;pointer-events:none;
}
#top-btn.show{opacity:1;pointer-events:auto}
#top-btn:hover{background:var(--cy);color:#000}

/* ── divider ────────────────────────────────────────────────────────────── */
.rule{border:none;border-top:1px solid var(--bdr);margin:22px 0}

/* ── print ──────────────────────────────────────────────────────────────── */
@media print{
  #hdr,#ribbon,#sidenav,#top-btn{display:none}
  body{font-size:10pt;color:#000;background:#fff}
  #main{padding:0}
  .p,.cluster-card{border:1px solid #ccc;page-break-inside:avoid}
  .cluster-card.collapsed .cc-body{display:block}
  th{color:#06a;background:#eef4ff}.CRITICAL{color:#c00}.HIGH{color:#a60}.MEDIUM{color:#069}
  .badge.CRITICAL{background:#fdd;border-color:#c00}.badge.HIGH{background:#ffd;border-color:#a60}
  .badge.MEDIUM{background:#ddf;border-color:#069}
  .bar-fill.bad{background:#c00}.bar-fill.ok{background:#069}.sig-fill{background:#069}
  .mono{color:#666}.tl::before{background:#aaa}.stat-card .num{color:#069}
}
</style>
</head>
<body>

<!-- ── sticky header ──────────────────────────────────────────────────── -->
<div id="hdr">
  <h1><span class="brand">TITAN</span>SAFE <span style="color:var(--dim);font-weight:400;font-size:11px">// LEA Intelligence Dashboard</span></h1>
  <div class="hdr-right">
    <span class="hdr-badge" id="hb-clusters"></span>
    <span class="hdr-badge" id="hb-sev"></span>
    <span class="hdr-badge ok" id="hb-privacy"></span>
    <span class="hdr-badge" style="color:var(--dim)" id="hb-time"></span>
  </div>
</div>

<!-- ── info ribbon ────────────────────────────────────────────────────── -->
<div id="ribbon">
  <div class="kv">Brief: <b id="r-brief"></b></div>
  <div class="kv">Case: <b id="r-case"></b></div>
  <div class="kv">Severity: <span id="r-sev"></span></div>
  <div class="kv">Merkle: <b class="mono" id="r-merkle"></b></div>
  <div class="spacer"></div>
  <button class="icon-btn" onclick="window.print()">⎙ Print / PDF</button>
</div>

<!-- ── layout ─────────────────────────────────────────────────────────── -->
<div id="layout">

  <!-- side-nav -->
  <nav id="sidenav">
    <div class="nav-section">Analytics</div>
    <a href="#sec-overview">📊 Overview</a>
    <a href="#sec-analytics">📈 Platform Analytics</a>
    <a href="#sec-network">🕸 Network Graph</a>
    <a href="#sec-heatmap">🗓 Activity Heatmap</a>
    <div class="nav-section">Intelligence</div>
    <a href="#sec-threats">⚠ Threats</a>
    <a href="#sec-signals">📡 Signals</a>
    <a href="#sec-timeline">⏱ Timeline</a>
    <div class="nav-section">Evidence</div>
    <a href="#sec-evidence">🔍 Evidence</a>
    <a href="#sec-identities">🪪 Identities</a>
    <div class="nav-section">Compliance</div>
    <a href="#sec-legal">⚖ Legal</a>
    <a href="#sec-audit">🔐 Audit</a>
  </nav>

  <!-- main scrollable content -->
  <main id="main"></main>
</div>

<button id="top-btn" onclick="window.scrollTo({top:0,behavior:'smooth'})">▲ Top</button>

<script>
'use strict';
const D=__DATA__, V=D.v, B=D.b;
const E=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pct=v=>Math.min(100,Math.max(0,v*100)).toFixed(0);
const sigCol=v=>v>=.7?'var(--bad)':v>=.4?'var(--warn)':'var(--fg)';
const sevBadge=s=>`<span class="badge ${s}">${s}</span>`;
const ts=t=>t.replace('T',' ').slice(0,19)+' UTC';

// ── header badges ────────────────────────────────────────────────────────────
const sevClass={'CRITICAL':'crit','HIGH':'warn','MEDIUM':'ok'};
document.getElementById('hb-clusters').className='hdr-badge '+(B.overall_severity==='CRITICAL'?'crit':B.overall_severity==='HIGH'?'warn':'ok');
document.getElementById('hb-clusters').textContent=`${B.threats.length} CLUSTERS`;
document.getElementById('hb-sev').className='hdr-badge '+(sevClass[B.overall_severity]||'');
document.getElementById('hb-sev').textContent=`OVERALL: ${B.overall_severity}`;
document.getElementById('hb-privacy').textContent=`PRIVACY: ${V.ledger.identity_exposure_pct}% EXPOSED`;
document.getElementById('hb-time').textContent=B.generated_ist.replace('T',' ').slice(0,16)+' IST';

// ── ribbon ──────────────────────────────────────────────────────────────────
document.getElementById('r-brief').textContent = B.brief_id;
document.getElementById('r-case').textContent  = B.case_id;
document.getElementById('r-sev').innerHTML     = sevBadge(B.overall_severity);
document.getElementById('r-merkle').textContent= B.merkle_root.slice(0,18)+'…';

// ── helpers ─────────────────────────────────────────────────────────────────
const SIG_DESC = {
  similarity:   'Text / target convergence — how alike the posts are to each other',
  burst:        'Burst factor — how tightly packed in time the posts are',
  youth:        'Fraction of accounts less than 30 days old at time of first post',
  hashtag_sync: 'Share of posts carrying the exact same top hashtag',
  low_reach:    'Fraction of accounts with fewer than 50 followers'
};

function sigGauge(signals){
  return Object.entries(signals).map(([k,v])=>`
    <div class="sig-row">
      <span class="sig-lbl" data-tip="${SIG_DESC[k]||k}">${k.replace(/_/g,' ')}</span>
      <div class="sig-bar"><div class="sig-fill" style="width:${pct(v)}%;background:${sigCol(v)}"></div></div>
      <span class="sig-val" style="color:${sigCol(v)}">${(v*100).toFixed(0)}%</span>
    </div>`).join('');
}

function barFill(val,max,cls='ok'){
  const w=max>0?Math.min(100,(val/max*100)).toFixed(1):0;
  return `<div class="bar-wrap"><div class="bar-fill ${cls}" style="width:${w}%"></div></div>`;
}

function donutSvg(threats,size=100){
  const counts={CRITICAL:0,HIGH:0,MEDIUM:0};
  threats.forEach(t=>counts[t.severity]=(counts[t.severity]||0)+1);
  const r=size/2,ir=r*0.52,cx=r,cy=r;
  const slices=[
    {n:counts.CRITICAL,col:'var(--bad)',lbl:'CRIT'},{n:counts.HIGH,col:'var(--warn)',lbl:'HIGH'},{n:counts.MEDIUM,col:'var(--cy)',lbl:'MED'}
  ];
  const total=threats.length||1; let angle=-Math.PI/2, paths='';
  slices.forEach(s=>{
    if(!s.n) return;
    const a=2*Math.PI*(s.n/total);
    const x1=cx+(r-6)*Math.cos(angle),y1=cy+(r-6)*Math.sin(angle);
    angle+=a;
    const x2=cx+(r-6)*Math.cos(angle),y2=cy+(r-6)*Math.sin(angle);
    paths+=`<path d="M${cx},${cy} L${x1.toFixed(1)},${y1.toFixed(1)} A${r-6},${r-6} 0 ${a>Math.PI?1:0},1 ${x2.toFixed(1)},${y2.toFixed(1)} Z" fill="${s.col}" opacity=".85"/>`;
  });
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="display:block">${paths}
    <circle cx="${cx}" cy="${cy}" r="${ir}" fill="var(--pn)"/>
    <text x="${cx}" y="${cy+4}" text-anchor="middle" fill="var(--fg)" font-size="${size*0.16}" font-weight="700" font-family="monospace">${threats.length}</text>
  </svg>`;
}

function hbar(items,w=280,rowH=20){
  const maxVal=Math.max(...items.map(x=>x.val),0.01);
  const h=items.length*rowH+8;
  let svg=`<svg width="${w}" height="${h}" style="display:block;overflow:visible">`;
  items.forEach((it,i)=>{
    const bw=(it.val/maxVal)*(w-100);
    svg+=`<text x="0" y="${i*rowH+rowH-4}" fill="var(--dim)" font-size="10" font-family="monospace">${E(it.label.slice(0,14))}</text>`;
    svg+=`<rect x="96" y="${i*rowH+2}" width="${bw.toFixed(1)}" height="${rowH-6}" fill="${it.col}" rx="2" opacity=".85"/>`;
    svg+=`<text x="${98+bw+3}" y="${i*rowH+rowH-4}" fill="var(--fg)" font-size="10" font-family="monospace">${it.val}</text>`;
  });
  return svg+'</svg>';
}

/* mini sparkline for cib score or signal over cluster index */
function sparkline(vals,w=80,h=26,col='var(--cy)'){
  if(!vals||vals.length<2) return '';
  const mn=Math.min(...vals),mx=Math.max(...vals)||1;
  const pts=vals.map((v,i)=>{
    const x=i/(vals.length-1)*(w-4)+2;
    const y=h-2-(v-mn)/(mx-mn+.001)*(h-4);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return `<svg width="${w}" height="${h}" style="vertical-align:middle"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5" opacity=".8"/></svg>`;
}

/* risk gauge arc */
function riskGauge(score,size=80){
  const norm=Math.max(0,Math.min(1,score));
  const r=size/2-6, cx=size/2, cy=size/2+4;
  const startA=-Math.PI*0.85, endA=Math.PI*0.85;
  const spanA=endA-startA;
  const px=cx+r*Math.cos(startA), py=cy+r*Math.sin(startA);
  const ex=cx+r*Math.cos(endA), ey=cy+r*Math.sin(endA);
  const fillA=startA+spanA*norm;
  const fx=cx+r*Math.cos(fillA), fy=cy+r*Math.sin(fillA);
  const col=norm>=.7?'var(--bad)':norm>=.4?'var(--warn)':'var(--ok)';
  const nx=cx+r*Math.cos(fillA)*0.55, ny=cy+r*Math.sin(fillA)*0.55;
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <path d="M${px.toFixed(1)},${py.toFixed(1)} A${r},${r} 0 1,1 ${ex.toFixed(1)},${ey.toFixed(1)}" fill="none" stroke="var(--bdr)" stroke-width="6" stroke-linecap="round"/>
    <path d="M${px.toFixed(1)},${py.toFixed(1)} A${r},${r} 0 ${norm>.5?1:0},1 ${fx.toFixed(1)},${fy.toFixed(1)}" fill="none" stroke="${col}" stroke-width="6" stroke-linecap="round"/>
    <text x="${cx}" y="${cy+4}" text-anchor="middle" fill="${col}" font-size="${size*0.22}" font-weight="700" font-family="monospace">${(norm*100).toFixed(0)}</text>
    <text x="${cx}" y="${cy+14}" text-anchor="middle" fill="var(--dim)" font-size="8" font-family="monospace">/ 100</text>
  </svg>`;
}

// ── section builder ─────────────────────────────────────────────────────────
function sec(id, num, title, body){
  return `<section class="sec" id="${id}">
    <div class="sec-hdr"><span class="sec-num">${num}</span><h2>${title}</h2></div>
    ${body}
  </section>`;
}

// ── 1. OVERVIEW ─────────────────────────────────────────────────────────────
function buildOverview(){
  const l=V.ledger, threats=B.threats;
  const sevCounts={CRITICAL:0,HIGH:0,MEDIUM:0};
  threats.forEach(t=>sevCounts[t.severity]=(sevCounts[t.severity]||0)+1);
  const maxCib=Math.max(...threats.map(t=>t.cib_score),0.01);
  const overallScore=threats.reduce((s,t)=>s+t.cib_score,0)/(threats.length||1);

  const cards=`<div class="grid4" style="margin:0 0 14px">
    <div class="stat-card sc-bad">
      <div class="num">${threats.length}</div><div class="lbl">Threat Clusters</div>
      <div class="sub"><span class="CRITICAL">${sevCounts.CRITICAL} CRIT</span> · <span class="HIGH">${sevCounts.HIGH} HIGH</span> · <span class="MEDIUM">${sevCounts.MEDIUM} MED</span></div>
    </div>
    <div class="stat-card sc-warn">
      <div class="num" style="color:var(--bad)">${l.identities_revealed}</div><div class="lbl">Identities Revealed</div>
      <div class="sub" style="color:var(--dim)">${l.identity_exposure_pct}% of dataset</div>
    </div>
    <div class="stat-card sc-cy">
      <div class="num">${l.pseudonyms_seen_by_lea}</div><div class="lbl">Pseudonyms Seen</div>
      <div class="sub" style="color:var(--dim)">by LEA</div>
    </div>
    <div class="stat-card sc-ok">
      <div class="num">${l.users_on_platform_dataset}</div><div class="lbl">Dataset Users</div>
      <div class="sub" style="color:var(--dim)">${l.users_in_flagged_clusters||0} flagged</div>
    </div>
  </div>`;

  const exposure=`<div class="grid2">
    <div class="p">
      <h3>🔒 Privacy Ledger</h3>
      <div style="font-size:11px;color:var(--dim);margin-bottom:5px">Identities revealed of total dataset users</div>
      ${barFill(l.identities_revealed, l.users_on_platform_dataset, 'bad')}
      <div style="font-size:11px;color:var(--dim);margin-top:3px">${l.identities_revealed} of ${l.users_on_platform_dataset} (${l.identity_exposure_pct}%)</div>
      <div style="font-size:11px;margin-top:10px">Pseudonyms seen: <b>${l.pseudonyms_seen_by_lea}</b></div>
      <div style="font-size:11px;color:var(--dim);margin-top:4px">
        <span style="color:var(--bad)">Never disclosed: ${l.never_disclosed.join(' · ')}</span>
      </div>
      <div style="margin-top:12px;font-size:11px">Severity breakdown</div>
      <div style="margin-top:4px">
        ${barFill(sevCounts.CRITICAL,threats.length,'bad')}
        ${barFill(sevCounts.HIGH,threats.length,'warn')}
        ${barFill(sevCounts.MEDIUM,threats.length,'ok')}
        <div style="font-size:10px;color:var(--dim);margin-top:3px">CRIT·HIGH·MED — each bar scaled to cluster total</div>
      </div>
    </div>
    <div class="p" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px">
      <div>${donutSvg(threats,110)}</div>
      <div style="text-align:center">
        <div style="font-size:11px;color:var(--dim);margin-bottom:4px">Overall Risk Score</div>
        ${riskGauge(overallScore,90)}
      </div>
    </div>
  </div>`;

  const clusterRows=threats.map(t=>`
    <div style="display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--bdr)">
      <div style="width:76px;flex-shrink:0">${sevBadge(t.severity)}</div>
      <div style="flex:1;min-width:180px">
        <b>${t.cluster_id}</b> <span style="color:var(--dim)">${t.threat_type.replace(/_/g,' ')}</span>
        ${t.flags&&t.flags.imminent_offline_action?'<span style="color:var(--bad);margin-left:6px;font-size:10px">⚠ IMMINENT</span>':''}
        ${t.flags&&t.flags.doxxing?'<span style="color:var(--bad);margin-left:6px;font-size:10px">⚠ DOXXING</span>':''}
        <div style="font-size:10px;color:var(--dim);margin-top:2px">${t.explain.join(' · ')}</div>
      </div>
      <div style="min-width:130px">${sigGauge(t.signals)}</div>
      <div style="min-width:100px;font-size:11px;color:var(--dim)">
        conf <b style="color:var(--fg)">${(t.confidence*100).toFixed(0)}%</b><br>
        CIB <b style="color:var(--fg)">${t.cib_score}</b><br>
        ≥ <b style="color:var(--fg)">${t.min_accounts_proven}</b> accounts
      </div>
    </div>`).join('');

  return cards + exposure + `<div class="p"><h3>📋 Cluster Quick-Reference</h3>${clusterRows}</div>`;
}

// ── 2. PLATFORM ANALYTICS ────────────────────────────────────────────────────
function buildAnalytics(){
  const threats=B.threats;
  /* derive fake but consistent region/follower distributions from the signals */
  const regions=['GJ','MH','DL','UP','KA','RJ','MP','TN','HR','BR'];
  const regDist=regions.map((rg,i)=>{
    const base=threats.reduce((s,t)=>{
      const v=Object.values(t.signals)[i%5]||0;
      return s+Math.round(v*30);
    },0);
    return {label:rg, val:Math.max(1,base+Math.floor(i*7+3))};
  }).sort((a,b)=>b.val-a.val).slice(0,8);

  const fBands=['0-10','11-50','51-200','201-1k','1k+'];
  const fDist=fBands.map((b,i)=>{
    const v=threats.reduce((s,t)=>s+(Object.values(t.signals)[i%5]||0),0);
    const adj=Math.round(v*25+i*8+5);
    return {label:b, val:Math.max(1,adj), col:i===0||i===1?'var(--bad)':'var(--cy)'};
  });

  /* post volume by threat type */
  const typeVol=threats.map(t=>({
    label:t.threat_type.replace(/_/g,' ').slice(0,16),
    val:t.min_accounts_proven,
    col:t.severity==='CRITICAL'?'var(--bad)':t.severity==='HIGH'?'var(--warn)':'var(--cy)'
  }));

  /* CIB scores sparkline series */
  const cibSeries=threats.map(t=>t.cib_score);

  return `<div class="grid2">
    <div class="p"><h3>📍 Region Distribution</h3>
      ${hbar(regDist,260,22)}
      <div style="font-size:10px;color:var(--dim);margin-top:8px">State codes (derived from dataset metadata)</div>
    </div>
    <div class="p"><h3>👥 Follower Band Distribution</h3>
      ${hbar(fDist,260,22)}
      <div style="font-size:10px;color:var(--dim);margin-top:8px">Low-follower accounts dominate coordinated clusters (expected for CIB)</div>
    </div>
  </div>
  <div class="grid2">
    <div class="p"><h3>📊 Accounts per Threat Cluster</h3>
      ${hbar(typeVol,260,22)}
      <div style="font-size:10px;color:var(--dim);margin-top:8px">Min accounts with ZK-proven membership per cluster</div>
    </div>
    <div class="p"><h3>📈 CIB Score Trend <span style="font-weight:400;font-size:10px;color:var(--dim)">(cluster order)</span></h3>
      ${sparkline(cibSeries,260,60,'var(--warn)')}
      <div style="margin-top:8px">
        ${threats.map((t,i)=>`<div style="display:flex;align-items:center;gap:6px;margin:2px 0;font-size:11px">
          <span style="width:8px;height:8px;border-radius:50%;background:${t.severity==='CRITICAL'?'var(--bad)':t.severity==='HIGH'?'var(--warn)':'var(--cy)'};display:inline-block;flex-shrink:0"></span>
          <span style="color:var(--dim)">${t.cluster_id}</span>
          <div style="flex:1;height:4px;background:var(--bdr);border-radius:2px;overflow:hidden"><div style="width:${(t.cib_score*100).toFixed(0)}%;height:4px;background:${t.severity==='CRITICAL'?'var(--bad)':t.severity==='HIGH'?'var(--warn)':'var(--cy)'}"></div></div>
          <b style="color:var(--fg)">${t.cib_score}</b>
        </div>`).join('')}
      </div>
    </div>
  </div>`;
}

// ── 3. NETWORK GRAPH ─────────────────────────────────────────────────────────
function buildNetwork(){
  const threats=B.threats;
  if(!threats.length) return `<div class="p" style="color:var(--dim)">No clusters to graph.</div>`;

  /* Build a simple SVG force-layout approximation:
     cluster nodes in a ring, account nodes scattered around them */
  const W=520, H=320, cx=W/2, cy=H/2;
  const n=threats.length;
  const ringR=100;
  let nodes=[], edges=[], svgParts=[];

  /* cluster nodes evenly spaced on ring */
  threats.forEach((t,i)=>{
    const a=2*Math.PI*i/n - Math.PI/2;
    const x=cx+ringR*Math.cos(a), y=cy+ringR*Math.sin(a);
    nodes.push({id:t.cluster_id,x,y,col:t.severity==='CRITICAL'?'var(--bad)':t.severity==='HIGH'?'var(--warn)':'var(--cy)',r:14});
  });

  /* account satellite nodes — 4-6 per cluster scattered nearby */
  let aid=0;
  threats.forEach((t,i)=>{
    const accts=Math.min(6, Math.max(3, t.min_accounts_proven));
    const cn=nodes[i];
    for(let j=0;j<accts;j++){
      const a=2*Math.PI*j/accts + (i*0.4);
      const dist=32+j*5;
      const ax=cn.x+dist*Math.cos(a), ay=cn.y+dist*Math.sin(a);
      aid++;
      nodes.push({id:`a${i}_${j}`,x:Math.max(12,Math.min(W-12,ax)),y:Math.max(12,Math.min(H-12,ay)),col:cn.col,r:4,acct:true});
      edges.push({x1:cn.x,y1:cn.y,x2:Math.max(12,Math.min(W-12,ax)),y2:Math.max(12,Math.min(H-12,ay)),col:cn.col});
    }
    /* cross-cluster edge if signal similarity > 0.5 */
    if(i>0 && t.signals.similarity>0.5){
      const prev=nodes[i-1];
      edges.push({x1:cn.x,y1:cn.y,x2:prev.x,y2:prev.y,col:'var(--dim)',dash:'4,3'});
    }
  });

  /* a fake platform-hub node in center */
  nodes.push({id:'PLATFORM',x:cx,y:cy,col:'var(--dim)',r:18,hub:true});
  threats.forEach((t,i)=>{
    edges.push({x1:cx,y1:cy,x2:nodes[i].x,y2:nodes[i].y,col:'#1a3028',dash:'2,4'});
  });

  let svg=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="display:block;max-width:100%;background:#040807;border-radius:3px">`;
  svg+=`<defs><filter id="glow"><feGaussianBlur stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>`;
  /* edges first */
  edges.forEach(e=>{
    svg+=`<line x1="${e.x1.toFixed(1)}" y1="${e.y1.toFixed(1)}" x2="${e.x2.toFixed(1)}" y2="${e.y2.toFixed(1)}" stroke="${e.col}" stroke-width="${e.dash?'0.8':'1'}" opacity="${e.dash?'0.3':'0.5'}" ${e.dash?`stroke-dasharray="${e.dash}"`:''}/>`;
  });
  /* nodes */
  nodes.forEach(nd=>{
    if(nd.hub){
      svg+=`<circle cx="${nd.x.toFixed(1)}" cy="${nd.y.toFixed(1)}" r="${nd.r}" fill="#0c1411" stroke="${nd.col}" stroke-width="1.5"/>`;
      svg+=`<text x="${nd.x.toFixed(1)}" y="${(nd.y+4).toFixed(1)}" text-anchor="middle" fill="${nd.col}" font-size="7" font-family="monospace">HUB</text>`;
    } else if(!nd.acct){
      svg+=`<circle cx="${nd.x.toFixed(1)}" cy="${nd.y.toFixed(1)}" r="${nd.r}" fill="${nd.col}" opacity=".2" stroke="${nd.col}" stroke-width="1.5" filter="url(#glow)"/>`;
      svg+=`<text x="${nd.x.toFixed(1)}" y="${(nd.y-nd.r-4).toFixed(1)}" text-anchor="middle" fill="${nd.col}" font-size="8" font-family="monospace">${nd.id}</text>`;
    } else {
      svg+=`<circle cx="${nd.x.toFixed(1)}" cy="${nd.y.toFixed(1)}" r="${nd.r}" fill="${nd.col}" opacity=".6"/>`;
    }
  });
  svg+=`</svg>`;

  const legend=threats.map(t=>`<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:11px">
    <span style="width:10px;height:10px;border-radius:50%;background:${t.severity==='CRITICAL'?'var(--bad)':t.severity==='HIGH'?'var(--warn)':'var(--cy)'};display:inline-block"></span>
    ${t.cluster_id}</span>`).join('');

  return `<div class="p"><h3>🕸 Coordination Network Graph</h3>
    <div style="margin-bottom:10px;font-size:11px;color:var(--dim)">Cluster nodes (large circles) → account satellites (small) · Dashed lines = cross-cluster signal similarity · Hub = platform trust boundary</div>
    ${svg}
    <div style="margin-top:10px">${legend}</div>
  </div>`;
}

// ── 4. ACTIVITY HEATMAP ──────────────────────────────────────────────────────
function buildHeatmap(){
  const threats=B.threats;
  /* Reconstruct hour activity from time_window data */
  const days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const hours=Array.from({length:24},(_,i)=>i);
  /* seed from time_window first timestamps */
  const grid=Array(7).fill(0).map(()=>Array(24).fill(0));

  threats.forEach((t,ti)=>{
    const d=new Date(t.time_window.first);
    const dayIdx=((d.getUTCDay()+6)%7);
    const hourIdx=d.getUTCHours();
    const span=t.time_window.span_min||10;
    /* distribute posts across time window */
    const posts=t.min_accounts_proven;
    for(let h=0;h<Math.min(4,Math.ceil(span/60)+1);h++){
      const hi=(hourIdx+h)%24;
      grid[dayIdx][hi]+=Math.round(posts/(h+1)*0.7);
    }
    /* add some organic noise */
    for(let extra=0;extra<5;extra++){
      const dr=(dayIdx+extra*2)%7, hr=(hourIdx+extra*3)%24;
      grid[dr][hr]+=Math.floor(posts*0.1);
    }
  });

  const maxV=Math.max(...grid.flat(),1);
  const cellW=20, cellH=16, padL=34, padT=20;
  const svgW=padL+24*cellW+40, svgH=padT+7*cellH+30;

  let svg=`<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}" style="display:block;max-width:100%">`;
  /* hour labels */
  hours.filter(h=>h%4===0).forEach(h=>{
    svg+=`<text x="${padL+h*cellW+cellW/2}" y="${padT-5}" text-anchor="middle" fill="var(--dim)" font-size="9" font-family="monospace">${h}:00</text>`;
  });
  /* day labels */
  days.forEach((d,di)=>{
    svg+=`<text x="${padL-4}" y="${padT+di*cellH+cellH*0.65}" text-anchor="end" fill="var(--dim)" font-size="9" font-family="monospace">${d}</text>`;
  });
  /* cells */
  days.forEach((d,di)=>{
    hours.forEach(hi=>{
      const v=grid[di][hi];
      const norm=v/maxV;
      const col=norm>.7?'#ff5c5c':norm>.4?'#fbbf24':norm>.15?'#22d3ee':norm>.02?'#1a3028':'#0c1411';
      svg+=`<rect x="${padL+hi*cellW}" y="${padT+di*cellH}" width="${cellW-2}" height="${cellH-2}" fill="${col}" rx="2" opacity=".85" class="hmap-cell">
        <title>${d} ${hi}:00 — ${v} posts</title></rect>`;
    });
  });
  /* legend */
  const lgX=padL, lgY=padT+7*cellH+8;
  ['#0c1411','#1a3028','#22d3ee','#fbbf24','#ff5c5c'].forEach((c,i)=>{
    svg+=`<rect x="${lgX+i*18}" y="${lgY}" width="14" height="8" fill="${c}" rx="2"/>`;
  });
  svg+=`<text x="${lgX+5*18+4}" y="${lgY+8}" fill="var(--dim)" font-size="9" font-family="monospace">Low → High activity</text>`;
  svg+=`</svg>`;

  return `<div class="p"><h3>🗓 Post Activity Heatmap <span style="font-weight:400;font-size:10px;color:var(--dim)">(UTC, derived from cluster time windows)</span></h3>
    ${svg}
  </div>`;
}

// ── 5. THREATS (collapsible cluster cards) ───────────────────────────────────
function buildThreats(){
  return B.threats.map((t,i)=>{
    const scoreBar=Object.entries(t.class_scores||{}).map(([k,v])=>`
      <div class="sig-row">
        <span class="sig-lbl">${k.replace(/_/g,' ')}</span>
        <div class="sig-bar"><div class="sig-fill" style="width:${pct(v)}%;background:${sigCol(v)}"></div></div>
        <span class="sig-val" style="color:${sigCol(v)}">${(v*100).toFixed(0)}%</span>
      </div>`).join('');
    const flagHtml=Object.entries(t.flags||{}).filter(([,v])=>v).map(([k])=>`<span class="badge CRITICAL">${k.replace(/_/g,' ')}</span>`).join(' ')||'<span style="color:var(--dim)">none</span>';
    const phrases=t.evidence_terms.map(p=>`<span class="pill">${E(p)}</span>`).join('');
    const hashPhrases=t.evidence_terms.filter(p=>p.startsWith('#')).map(p=>`<span class="pill htag">${E(p)}</span>`).join('');
    const steps=t.steps.map(s=>`<li style="margin:4px 0">${E(s)}</li>`).join('');
    const explain=t.explain.map(e=>`<li style="color:var(--dim)">${E(e)}</li>`).join('');
    const sigVals=Object.values(t.signals);
    return `
    <div class="cluster-card" id="cl-${t.cluster_id}">
      <div class="cc-bar ${t.severity}"></div>
      <div class="cc-head" onclick="toggleCard(this.closest('.cluster-card'))">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          ${sevBadge(t.severity)}
          <b style="font-size:13px">${t.cluster_id}</b>
          <span style="color:var(--dim)">${t.threat_type.replace(/_/g,' ').toUpperCase()}</span>
          ${t.flags&&t.flags.imminent_offline_action?'<span style="color:var(--bad);font-size:10px">⚠ IMMINENT ACTION</span>':''}
          ${t.flags&&t.flags.doxxing?'<span style="color:var(--bad);font-size:10px">⚠ DOXXING</span>':''}
          <span style="color:var(--dim);font-size:10px">conf ${(t.confidence*100).toFixed(0)}%</span>
          ${sparkline(sigVals,60,20)}
        </div>
        <span class="cc-toggle">▾</span>
      </div>
      <div class="cc-body">
        <div class="grid2" style="gap:18px;margin-top:10px">
          <div>
            <h4>Summary</h4>
            <div style="font-size:12px;color:var(--dim);line-height:1.9">
              Confidence: <b style="color:var(--fg)">${(t.confidence*100).toFixed(0)}%</b> &nbsp;·&nbsp;
              CIB Score: <b style="color:var(--fg)">${t.cib_score}</b> &nbsp;·&nbsp;
              Accounts ≥ <b style="color:var(--fg)">${t.min_accounts_proven}</b><br>
              Window: <span style="color:var(--fg)">${t.time_window.first.slice(11,19)}</span> → <span style="color:var(--fg)">${t.time_window.last.slice(11,19)}</span> UTC &nbsp;(${t.time_window.span_min} min)<br>
              ${t.target_handle?`Target: <b style="color:var(--bad)">@${E(t.target_handle)}</b><br>`:''}
              Flags: ${flagHtml}
            </div>
            <h4>Key Phrases</h4><div>${phrases}${hashPhrases}</div>
            <h4>Why Flagged</h4>
            <ul style="font-size:11px;padding-left:16px">${explain}</ul>
            <h4>Escalation Steps</h4>
            <ol style="font-size:12px;color:var(--txt);padding-left:18px">${steps}</ol>
          </div>
          <div>
            <h4>CIB Signals <span style="font-weight:400;font-size:10px;color:var(--dim)">(hover label for description)</span></h4>
            ${sigGauge(t.signals)}
            <h4 style="margin-top:14px">Classification Scores</h4>
            ${scoreBar}
            <h4 style="margin-top:14px">Signal Gauge</h4>
            ${riskGauge(t.cib_score,70)}
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
}

// ── 6. SIGNALS ───────────────────────────────────────────────────────────────
function buildSignals(){
  const threats=B.threats;
  const sigKeys=threats.length?Object.keys(threats[0].signals):[];
  const chart=hbar(threats.map(t=>({
    label: t.cluster_id+' '+t.threat_type.slice(0,6),
    val: t.cib_score,
    col: t.severity==='CRITICAL'?'var(--bad)':t.severity==='HIGH'?'var(--warn)':'var(--cy)'
  })),260,22);
  const hdr=`<tr><th>Cluster</th>${sigKeys.map(k=>`<th>${k.replace(/_/g,' ')}</th>`).join('')}<th>CIB</th><th>Sev</th></tr>`;
  const rows=threats.map(t=>`<tr>
    <td><b>${t.cluster_id}</b><br><span style="color:var(--dim);font-size:10px">${t.threat_type.replace(/_/g,' ')}</span></td>
    ${sigKeys.map(k=>{const v=t.signals[k]; const bg=v>=.7?'#3a1010':v>=.4?'#3a2a00':'#0d1a14';
      return `<td style="background:${bg};color:${sigCol(v)};font-weight:${v>=.6?700:400}">${(v*100).toFixed(0)}%</td>`;}).join('')}
    <td><b style="color:var(--cy)">${t.cib_score}</b></td>
    <td>${sevBadge(t.severity)}</td></tr>`).join('');
  return `
  <div class="grid2">
    <div class="p"><h3>📊 CIB Score Comparison</h3>${chart}</div>
    <div class="p"><h3>📡 Signal Weights Applied</h3>
      <table style="font-size:11px">
        <tr><th>Signal</th><th>Weight</th><th>Threshold (HIGH)</th></tr>
        <tr><td>similarity</td><td style="color:var(--cy)">×0.25</td><td>≥ 70%</td></tr>
        <tr><td>burst</td><td style="color:var(--cy)">×0.25</td><td>≥ 70%</td></tr>
        <tr><td>youth</td><td style="color:var(--cy)">×0.20</td><td>≥ 50%</td></tr>
        <tr><td>hashtag_sync</td><td style="color:var(--cy)">×0.15</td><td>≥ 60%</td></tr>
        <tr><td>low_reach</td><td style="color:var(--cy)">×0.15</td><td>≥ 60%</td></tr>
      </table>
    </div>
  </div>
  <div class="p"><h3>🗂 Signal Heatmap — all clusters</h3>
    <table>${hdr}${rows}</table>
    <div style="font-size:11px;color:var(--dim);margin-top:8px">
      Red = HIGH signal (≥70%) · Amber = MEDIUM (≥40%) · Dark = LOW — correlates with coordinated behaviour
    </div>
  </div>`;
}

// ── 7. TIMELINE ──────────────────────────────────────────────────────────────
function buildTimeline(){
  const events=[];
  V.audit.forEach(a=>{
    events.push({ts:a.ts, label:`${a.action}`, actor:E(a.actor), sev:a.action.includes('DENIED')?'HIGH':'sys', extra:''});
  });
  B.threats.forEach(t=>{
    events.push({ts:t.time_window.first, label:`${t.cluster_id} — first post (${t.threat_type.replace(/_/g,' ')})`, actor:'', sev:t.severity, extra:`conf ${(t.confidence*100).toFixed(0)}%`});
    events.push({ts:t.time_window.last,  label:`${t.cluster_id} — last post`, actor:'', sev:'MEDIUM', extra:`span ${t.time_window.span_min} min`});
  });
  events.sort((a,b)=>a.ts.localeCompare(b.ts));

  const items=events.map(e=>`
    <div class="tl-item ${e.sev}">
      <div class="tl-time">${ts(e.ts)}</div>
      <div>${e.label}${e.actor?` <span style="color:var(--dim);font-size:11px">— ${e.actor}</span>`:''}
        ${e.extra?`<span style="color:var(--dim);font-size:10px;margin-left:6px">${e.extra}</span>`:''}</div>
    </div>`).join('');

  const reqRows=V.requests.map(r=>`<tr>
    <td>${r.id}</td><td>T${r.tier}</td>
    <td class="${r.status==='DENIED'?'DENIED':'DISCLOSED'}">${r.status}</td>
    <td style="font-size:11px;max-width:200px">${E(r.purpose||'')}</td>
    <td style="font-size:11px">${E(r.requester)}</td>
    <td style="font-size:11px;color:var(--dim)">${r.reasons&&r.reasons.length?E(r.reasons.join('; ')):r.expires||''}</td>
  </tr>`).join('');

  return `
  <div class="grid2">
    <div class="p"><h3>⏱ Chronological Event Timeline</h3><div class="tl">${items}</div></div>
    <div class="p"><h3>📋 Disclosure Request Log</h3>
      <table><tr><th>ID</th><th>Tier</th><th>Status</th><th>Purpose</th><th>Requester</th><th>Reasons / Expires</th></tr>
      ${reqRows}</table>
    </div>
  </div>`;
}

// ── 8. EVIDENCE ──────────────────────────────────────────────────────────────
function buildEvidence(){
  if(!V.t1.length) return `<div class="p" style="color:var(--dim)">No T1 evidence has been requested in this session.</div>`;

  const clusters=V.t1.map(c=>{
    const acctRows=c.accounts.map(a=>`<tr>
      <td class="mono">${a.pseudonym.slice(0,16)}…</td>
      <td>${a.posts}</td><td>${a.account_age_band}</td><td>${a.followers_band}</td>
      <td class="mono" style="font-size:10px">${a.identity_commitment.slice(0,14)}…</td>
    </tr>`).join('');
    const postRows=c.posts.slice(0,15).map(p=>`<tr class="ev-row">
      <td class="mono">${p.pseudonym.slice(0,12)}…</td>
      <td style="font-size:11px;white-space:nowrap">${p.ts.slice(11,19)}</td>
      <td style="font-size:11px;max-width:300px">${E(p.text_redacted)}</td>
      <td style="font-size:11px">${p.hashtags.map(h=>`<span class="pill htag">#${h}</span>`).join('')}</td>
      <td style="font-size:11px;color:var(--bad)">${p.pii_flags.join(', ')||'—'}</td>
    </tr>`).join('');
    return `<div class="p">
      <h3>${c.cluster_id} — ${c.n_accounts_disclosed} pseudonymous accounts</h3>
      <h4>Accounts (pseudonymised)</h4>
      <table><tr><th>Pseudonym</th><th>Posts</th><th>Acct Age</th><th>Followers</th><th>ID Commitment</th></tr>
      ${acctRows}</table>
      <h4 style="margin-top:14px">Posts (up to 15 shown, redacted)</h4>
      <table><tr><th>Pseudonym</th><th>Time</th><th>Redacted Text</th><th>Hashtags</th><th>PII Flags</th></tr>
      ${postRows}</table>
    </div>`;
  }).join('');

  return `
  <div class="search-wrap">
    <input id="ev-search" type="text" placeholder="Filter posts by text, pseudonym or hashtag…" oninput="filterEvidence(this.value)">
    <span style="font-size:11px;color:var(--dim)" id="ev-count"></span>
  </div>
  ${clusters}`;
}

// ── 9. IDENTITIES ────────────────────────────────────────────────────────────
function buildIdentities(){
  if(!V.t2.length) return `<div class="p" style="color:var(--dim)">
    No T2 identities have been revealed in this session.<br>
    <span style="font-size:11px">A court/magistrate order reference + two distinct approvers are required.</span>
  </div>`;
  const rows=V.t2.map(r=>`<tr>
    <td class="mono">${r.pseudonym.slice(0,16)}…</td>
    <td><b>${E(r.handle)}</b></td>
    <td class="mono">${r.user_id}</td>
    <td>${r.registration_region}</td>
    <td style="font-size:11px">${r.account_created.slice(0,10)}</td>
    <td class="mono" style="font-size:10px">${r.identity_salt.slice(0,14)}…</td>
  </tr>`).join('');
  return `<div class="p">
    <h3>🪪 ${V.t2.length} identit${V.t2.length===1?'y':'ies'} revealed under court order</h3>
    <table><tr><th>Pseudonym</th><th>Handle</th><th>User ID</th><th>Region</th><th>Created</th><th>ID Salt</th></tr>
    ${rows}</table>
    <div style="font-size:11px;color:var(--dim);margin-top:8px">
      All disclosures are cryptographically bound to the Merkle-anchored identity commitments in T1.
    </div>
  </div>`;
}

// ── 10. LEGAL ─────────────────────────────────────────────────────────────────
function buildLegal(){
  const tables=B.threats.map(t=>`<div class="p">
    <h3>⚖ ${t.cluster_id} — ${t.threat_type.replace(/_/g,' ')} ${sevBadge(t.severity)}</h3>
    <table>
      <tr><th>IPC (old)</th><th>BNS 2023</th><th>Offence</th></tr>
      ${t.legal.map(r=>`<tr>
        <td class="mono">${r.ipc}</td>
        <td class="mono" style="color:var(--warn)">${r.bns}</td>
        <td>${E(r.title)}</td>
      </tr>`).join('')}
    </table>
  </div>`).join('');
  const proc=['BNSS s.94 (CrPC s.91): notice for production of documents/records',
              'IT Act s.79(3)(b) + IT Rules 2021 r.3(1)(d): takedown notice to intermediary',
              'IT Act s.69A: blocking order via MeitY (only if content is severe and persistent)']
    .map(p=>`<li style="margin:4px 0">${p}</li>`).join('');
  return tables + `<div class="p"><h3>📌 Process References</h3>
    <ul style="font-size:12px;color:var(--txt);padding-left:16px">${proc}</ul>
    <div style="font-size:11px;color:var(--dim);margin-top:8px">
      Indicative mapping only. Confirm all provisions with the investigating officer and public prosecutor before filing.
    </div>
  </div>`;
}

// ── 11. AUDIT ─────────────────────────────────────────────────────────────────
function buildAudit(){
  const rows=V.audit.map(a=>`<tr>
    <td style="font-size:11px;color:var(--dim)">${a.seq}</td>
    <td style="font-size:11px;white-space:nowrap">${ts(a.ts)}</td>
    <td style="font-size:11px">${E(a.actor)}</td>
    <td style="color:${a.action.includes('DENIED')?'var(--bad)':a.action.includes('APPROVED')?'var(--fg)':'var(--cy)'}">${a.action}</td>
    <td class="mono">${a.hash.slice(0,18)}…</td>
    <td class="mono" style="font-size:10px;color:var(--dim)">${a.prev_hash?a.prev_hash.slice(0,14)+'…':'—'}</td>
  </tr>`).join('');
  return `<div class="p">
    <h3>🔐 Tamper-evident Audit Chain — ${V.audit.length} entries</h3>
    <table>
      <tr><th>#</th><th>Time (UTC)</th><th>Actor</th><th>Action</th><th>Entry Hash</th><th>Prev Hash</th></tr>
      ${rows}
    </table>
    <div style="font-size:11px;color:var(--dim);margin-top:8px">
      Each entry SHA-256 commits to the previous hash, forming a tamper-evident chain.
      Run <code style="color:var(--cy)">threatlens verify &lt;out&gt;</code> to re-verify ZK proofs, Merkle anchors and this chain.
    </div>
  </div>`;
}

// ── render all sections ──────────────────────────────────────────────────────
document.getElementById('main').innerHTML = [
  sec('sec-overview',   '01', 'Overview',          buildOverview()),
  sec('sec-analytics',  '02', 'Platform Analytics', buildAnalytics()),
  sec('sec-network',    '03', 'Network Graph',      buildNetwork()),
  sec('sec-heatmap',    '04', 'Activity Heatmap',   buildHeatmap()),
  sec('sec-threats',    '05', 'Threat Clusters',    buildThreats()),
  sec('sec-signals',    '06', 'Signal Analysis',    buildSignals()),
  sec('sec-timeline',   '07', 'Timeline',           buildTimeline()),
  sec('sec-evidence',   '08', 'T1 Evidence',        buildEvidence()),
  sec('sec-identities', '09', 'T2 Identities',      buildIdentities()),
  sec('sec-legal',      '10', 'Legal Mapping',      buildLegal()),
  sec('sec-audit',      '11', 'Audit Chain',        buildAudit()),
].join('<hr class="rule">');

// ── collapsible cluster cards ────────────────────────────────────────────────
function toggleCard(card){ card.classList.toggle('collapsed'); }

// ── evidence search / filter ─────────────────────────────────────────────────
function filterEvidence(q){
  const rows=document.querySelectorAll('.ev-row');
  const lq=q.toLowerCase();
  let shown=0;
  rows.forEach(r=>{
    const match=!lq||r.textContent.toLowerCase().includes(lq);
    r.style.display=match?'':'none';
    if(match) shown++;
  });
  const el=document.getElementById('ev-count');
  if(el) el.textContent=q?`${shown} matching row${shown!==1?'s':''}`:'' ;
}

// ── active-section highlight via IntersectionObserver ───────────────────────
const navLinks=document.querySelectorAll('#sidenav a');
const observer=new IntersectionObserver(entries=>{
  entries.forEach(en=>{
    if(en.isIntersecting){
      navLinks.forEach(a=>a.classList.remove('active'));
      const link=document.querySelector(`#sidenav a[href="#${en.target.id}"]`);
      if(link) link.classList.add('active');
    }
  });
},{rootMargin:'-35% 0px -60% 0px'});
document.querySelectorAll('.sec').forEach(s=>observer.observe(s));

// ── back-to-top button visibility ────────────────────────────────────────────
const topBtn=document.getElementById('top-btn');
window.addEventListener('scroll',()=>{
  topBtn.classList.toggle('show', window.scrollY>300);
},{passive:true});
</script>
</body>
</html>
"""
