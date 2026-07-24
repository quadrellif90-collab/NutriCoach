"""NutriCoach — Grafici trend in SVG (offline, nessuna dipendenza esterna).

Genera mini-grafici SVG (line chart) per i trend nel tempo di peso, % grassa
e BIA, da usare inline nell'export HTML e nel report PDF. Niente matplotlib:
SVG puro, leggero e portabile.
"""

import base64


def _scale(values, w, h, pad):
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1
    rng = hi - lo
    pts = []
    n = len(values)
    for i, v in enumerate(values):
        x = pad + (w - 2 * pad) * (i / (n - 1)) if n > 1 else w / 2
        y = h - pad - (h - 2 * pad) * ((v - lo) / rng)
        pts.append((round(x, 1), round(y, 1)))
    return pts


def line_chart(values, labels=None, w=420, h=140, color="#0d9488", title="", unit=""):
    """Ritorna una stringa SVG con un line chart dei `values`."""
    if not values:
        return ""
    pts = _scale(values, w, h, 24)
    path = "M " + " L ".join(f"{x},{y}" for x, y in pts)
    # area
    area = f"M {pts[0][0]},{h-24} " + " L ".join(f"{x},{y}" for x, y in pts) + f" L {pts[-1][0]},{h-24} Z"
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="2.5" fill="{color}"/>' for x, y in pts)
    # ultimo valore
    lx, ly = pts[-1]
    last_v = values[-1]
    svg = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMidYMid meet" role="img">
      <text x="8" y="14" fill="#64748b" font-size="11">{title}</text>
      <path d="{area}" fill="{color}" opacity="0.10"/>
      <path d="{path}" fill="none" stroke="{color}" stroke-width="2"/>
      {dots}
      <text x="{w-8}" y="{ly-6 if ly>20 else ly+14}" text-anchor="end" fill="{color}" font-size="12" font-weight="600">{last_v}{unit}</text>
    </svg>"""
    return svg.strip()


def trend_block(weight_series, fat_series, bia_series, labels=None):
    """Blocco SVG multi-trend per il riepilogo (3 mini-chart affiancati)."""
    charts = []
    if weight_series:
        charts.append(line_chart(weight_series, labels, title="Peso (kg)", color="#0d9488"))
    if fat_series:
        charts.append(line_chart(fat_series, labels, title="% grassa", color="#f59e0b"))
    if bia_series:
        charts.append(line_chart(bia_series, labels, title="BIA PhA (°)", color="#6366f1"))
    return "".join(f'<div style="flex:1;min-width:200px">{c}</div>' for c in charts)
