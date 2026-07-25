"""NutriCoach — Report PDF delle strategie pro adattate (sport science).

Genera un PDF esportabile con le strategie pro->amatoriali (FTWR, recovery
microcycle, nota chetoni) e, se fornito, i dati del cliente. Usa reportlab
(offline, nessun cloud). Fonti 2024-2026 citate nel pie' di pagina.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

from sport_science import science_bundle


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1b", parent=ss["Heading1"], textColor=colors.HexColor("#1f8a70"), spaceAfter=6))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], textColor=colors.HexColor("#0d9488"), spaceBefore=10, spaceAfter=4))
    ss.add(ParagraphStyle("Body", parent=ss["BodyText"], fontSize=9.5, leading=13))
    ss.add(ParagraphStyle("Small", parent=ss["BodyText"], fontSize=8, textColor=colors.grey))
    return ss


def build_sport_science_pdf(client=None, day_type="race", intensity="race", weight_kg=None):
    """Ritorna i bytes del PDF. client = dict opzionale (nome, sesso, obiettivo)."""
    b = science_bundle()
    ss = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16*mm, bottomMargin=16*mm,
                            leftMargin=16*mm, rightMargin=16*mm,
                            title="NutriCoach — Strategie Sport")
    el = []

    el.append(Paragraph("NutriCoach — Strategie Sport (pro → amatoriale)", ss["H1b"]))
    if client:
        el.append(Paragraph(
            f"Cliente: <b>{client.get('name','')}</b> &nbsp;|&nbsp; Sesso: {client.get('sex','')} "
            f"&nbsp;|&nbsp; Obiettivo: {client.get('goal','')}", ss["Body"]))
    el.append(Spacer(1, 4))

    # --- FTWR ---
    el.append(Paragraph("⛽ Fuel for the Work Required (periodizzazione carb)", ss["H2b"]))
    el.append(Paragraph(b["fueling"]["note"], ss["Body"]))
    # tabella daily
    daily_rows = [["Tipo giorno", "g/kg", "Carb %", "Carb (g) a 70kg"]]
    for k, v in b["fueling"]["daily_g_per_kg"].items():
        ref = int(round(70 * v["g_per_kg"]))
        daily_rows.append([v["label"], f"{v['g_per_kg']}", f"{v['carb_pct']}%", str(ref)])
    t = Table(daily_rows, colWidths=[70*mm, 20*mm, 20*mm, 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f8a70")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.4, colors.lightgrey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f7f5")]),
    ]))
    el.append(t)
    el.append(Spacer(1, 3))
    during_rows = [["Intensita' sforzo", "g/h carb"]]
    for k, v in b["fueling"]["during_exercise_g_per_h"].items():
        during_rows.append([v["label"], str(v["g_per_h"])])
    t2 = Table(during_rows, colWidths=[70*mm, 35*mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d9488")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.4, colors.lightgrey),
    ]))
    el.append(t2)
    if weight_kg:
        import sport_science as ssci
        d = ssci.fueling_daily_targets(day_type, weight_kg)
        u = ssci.fueling_during_targets(intensity) if intensity else None
        if d:
            el.append(Spacer(1, 3))
            el.append(Paragraph(
                f"<b>Calcolo per {weight_kg} kg</b> — giorno '{day_type}': "
                f"{d['carb_g']} g carb/giorno (~{d['carb_pct']}% kcal)."
                + (f" Durante sforzo '{intensity}': {u['g_per_h']} g/h." if u else ""),
                ss["Body"]))

    # --- Recovery ---
    el.append(Paragraph("🔄 Recovery microcycle (football pro → amatoriale)", ss["H2b"]))
    el.append(Paragraph(b["recovery"]["note"], ss["Body"]))
    el.append(Paragraph("Fondamenta (priorita' 1):", ss["Body"]))
    for f in b["recovery"]["foundations"]:
        el.append(Paragraph(f"• <b>{f['label']}</b> — {f['detail']}", ss["Body"]))
    el.append(Paragraph("Microciclo:", ss["Body"]))
    for k, v in b["recovery"]["microcycle"].items():
        adjuncts = ", ".join(b["recovery"]["adjuncts"][a] for a in v["adjunct"] if a in b["recovery"]["adjuncts"]) or "fondamenta"
        el.append(Paragraph(f"• <b>{v['label']}</b> ({v['focus']}): {adjuncts}", ss["Body"]))

    # --- Chetoni ---
    el.append(Paragraph("🧪 Chetoni esogeni", ss["H2b"]))
    el.append(Paragraph(b["ketones"]["note"], ss["Body"]))

    el.append(Spacer(1, 8))
    el.append(Paragraph(
        "Fonti: Cao W et al. (PMC 2025); Outside/Velo & Olympics.com (Tour de France 2025, "
        "fueling 100-120 g/h); Aspetar journal 'Emerging Challenges in Recovery for the Elite "
        "Football Player' (FIFA World Cup 2026); Ranchordas MK et al. (PMC 2017); Rackard G et al. "
        "(2025); UCI declaration on ketone supplements (2024). Non e' consulenza medica.",
        ss["Small"]))

    doc.build(el)
    return buf.getvalue()
