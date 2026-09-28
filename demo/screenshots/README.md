# Screenshots

Place dashboard and report screenshots here.

## Suggested screenshots

| Filename | What to capture |
|---|---|
| `01-overview.png` | Dashboard Overview section — stat cards + donut chart + exposure bar |
| `02-threats.png` | Threats section — a CRITICAL cluster card expanded showing signal gauges |
| `03-signals.png` | Signals section — CIB score bar chart + heatmap table |
| `04-timeline.png` | Timeline section — scrollable event timeline + request log |
| `05-evidence.png` | Evidence section — evidence search filter + post table |
| `06-pdf-report.png` | threat_report.html open in browser showing the cover page |
| `07-verify.png` | Terminal showing `TitanSafe verify out` with all 4 PASS lines |
| `08-datasets.png` | Terminal showing `TitanSafe datasets` listing all 4 datasets |

## How to take screenshots

```bash
# Generate all four datasets
python -m TitanSafe.cli demo --out out --pdf
python -m TitanSafe.cli demo --dataset election_disinfo --out out_election --pdf
python -m TitanSafe.cli demo --dataset communal_riot    --out out_riot     --pdf
python -m TitanSafe.cli demo --dataset journalist_doxxing --out out_doxxing --pdf

# Open out/dashboard.html in browser and capture each section
# Open out/threat_report.html for the PDF report screenshot
```
