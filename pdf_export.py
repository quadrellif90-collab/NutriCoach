"""NutriCoach — Export PDF professionale (reportlab).

Genera un report per cliente:
1. Intestazione studio (logo opzionale)
2. Anamnesi (nome, età, sesso, obiettivo, allergie, patologie, preferenze)
3. Scheda antropometrica + calcoli (BMI, BMR, TDEE, %grassa, WHR, FFMI, peso ideale, proteine)
4. BIA (ultima misura)
5. Fabbisogno energetico vs dieta
6. Piano settimanale (giorni/pasti/alternative selezionate) con conteggi
7. Lista della spesa

Funzioni:
    build_report_pdf(client_id, diet_id, selections, path) -> salva PDF
    build_diet_pdf(diet, selections, path) -> PDF stile "dieta import" (output form)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, HRFlowable)

TEAL = colors.HexColor("#0d9488")
AMBER = colors.HexColor("#f59e0b")
DARK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
LIGHT = colors.HexColor("#f1f5f9")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1", parent=ss["Title"], textColor=TEAL, fontSize=18, spaceAfter=4))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13,
                          spaceBefore=10, spaceAfter=4, textColor=TEAL))
    ss.add(ParagraphStyle("Body", parent=ss["BodyText"], fontSize=9, leading=12))
    ss.add(ParagraphStyle("Small", parent=ss["BodyText"], fontSize=8, textColor=MUTED, leading=10))
    return ss


def _kv_table(rows, col_widths):
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LIGHT),
    ]))
    return t


def build_report_pdf(client_id, diet_id, selections, path, logo_path=None):
    import db, nutrition_engine, anthropometry as ant
    from nutrition_db import nutrition_for

    c = db.get_client(client_id)
    comp = None
    diet = None
    if diet_id:
        d = db.get_diet(diet_id)
        if d:
            diet = d["diet"]
            comp = nutrition_engine.compute_diet(diet, selections)
    anth = db.compute_anthropometry(client_id)
    bia_rows = db.list_bia(client_id)
    bia = bia_rows[0]["data"] if bia_rows else {}

    ss = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=14 * mm, bottomMargin=12 * mm,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            title=f"Report Nutrizionale - {c['name'] if c else ''}")
    el = []

    # header
    hdr = []
    if logo_path:
        try:
            hdr.append(Image(logo_path, width=28 * mm, height=12 * mm))
        except Exception:
            pass
    hdr.append(Paragraph(f"Report Nutrizionale<br/><font size=10 color='#64748b'>{c['name'] if c else ''}</font>", ss["H1"]))
    el.append(Table([hdr], colWidths=[40 * mm, 130 * mm]))
    el.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=8))

    # 1. Anamnesi
    el.append(Paragraph("Anamnesi", ss["H2"]))
    rows = [
        ["Nome", c.get("name", ""), "Età", c.get("age", "") or ""],
        ["Sesso", c.get("sex", ""), "Altezza", f"{c.get('height_cm') or ''} cm"],
        ["Attività", c.get("activity", ""), "Atleta", "Sì" if c.get("athlete") else "No"],
        ["Obiettivo", c.get("goal", ""), "Email", c.get("email", "")],
        ["Allergie", c.get("allergies", "") or "—", "Patologie", c.get("pathologies", "") or "—"],
        ["Preferenze", c.get("preferences", "") or "—", "", ""],
    ]
    el.append(_kv_table(rows, [28 * mm, 72 * mm, 24 * mm, 66 * mm]))

    # 2. Antropometria + calcoli
    if anth:
        el.append(Paragraph("Scheda antropometrica e fabbisogno", ss["H2"]))
        m = anth.get("measurement", {})
        kv = [
            ["Peso", f"{m.get('weight_kg') or '—'} kg", "BMI", f"{anth.get('bmi') or '—'} ({anth.get('bmi_class') or ''})"],
            ["Vita", f"{m.get('waist_cm') or '—'} cm", "Fianchi", f"{m.get('hip_cm') or '—'} cm"],
            ["WHR", f"{anth.get('whr') or '—'}", "WHR rischio", anth.get("whr_risk") or "—"],
            ["BMR", f"{anth.get('bmr') or '—'} kcal", "TDEE", f"{anth.get('tdee') or '—'} kcal"],
            ["% grassa", f"{anth.get('fat_pct') or '—'} %", "Massa magra", f"{anth.get('lean_mass_kg') or '—'} kg"],
            ["FFMI", f"{anth.get('ffmi') or '—'}", "Peso ideale", f"{anth.get('ideal_weight') or '—'} kg"],
            ["Proteine", f"{anth.get('protein_g') or '—'} g/die", "", ""],
        ]
        el.append(_kv_table(kv, [26 * mm, 46 * mm, 30 * mm, 48 * mm]))

    # 3. BIA
    if bia:
        el.append(Paragraph("Bioimpedenziometria (ultima misura)", ss["H2"]))
        bia_items = list(bia.items())[:10]
        rows = [[k, str(v)] for k, v in bia_items]
        el.append(_kv_table(rows, [50 * mm, 70 * mm]))

    # 4. Dieta + conteggi
    if comp:
        wk = comp["week"]["avg_day"]
        el.append(Paragraph("Piano alimentare — media giornaliera", ss["H2"]))
        macro = [
            ["kcal/giorno", f"{wk['kcal']:.0f}"],
            ["Proteine", f"{wk['p']:.0f} g"],
            ["Carboidrati", f"{wk['c']:.0f} g"],
            ["Grassi", f"{wk['f']:.0f} g"],
            ["Fibre", f"{wk['fib']:.0f} g"],
        ]
        t = Table([["", ""]] + macro, colWidths=[60 * mm, 30 * mm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (0, -1), MUTED),
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT),
        ]))
        el.append(t)

        # giorni
        for day in comp["days"]:
            el.append(Paragraph(f"{day['day']} — {day['totals']['kcal']:.0f} kcal", ss["Small"]))
            data = [["Pasto", "Alimento (scelta)", "g", "kcal"]]
            for meal in day["meals"]:
                for gi, grp in enumerate(meal["groups"]):
                    for oi, o in enumerate(grp["options"]):
                        if o.get("active"):
                            data.append([meal["meal"] if gi == 0 and oi == 0 else "",
                                         f"{o['food']} {'✓' if o.get('active') else ''}",
                                         f"{o['grams']:.0f}", f"{o['kcal']:.0f}"])
            t = Table(data, colWidths=[24 * mm, 96 * mm, 16 * mm, 16 * mm])
            t.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.2, LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            el.append(t)
            el.append(Spacer(1, 4))

    # 5. Spesa
    if diet:
        sl = nutrition_engine.build_shopping_list(diet, selections)
        if sl:
            el.append(Paragraph("Lista della spesa (settimana)", ss["H2"]))
            data = [["Alimento", "Quantità"]] + [[s["food"], f"{s['grams']:.0f} g"] for s in sl]
            t = Table(data, colWidths=[110 * mm, 40 * mm])
            t.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.2, LIGHT),
            ]))
            el.append(t)

    el.append(Spacer(1, 8))
    el.append(Paragraph("Generato con NutriCoach — software gestionale per nutrizionisti (localhost). "
                        "I valori sono stime basate su tabelle INRAN/LARN/USDA.", ss["Small"]))
    doc.build(el)
    return path


def build_diet_pdf(diet, selections, path):
    """Genera un PDF dieta in stile 'import' (output form): giorni, pasti,
    alimenti con grammi e alternative, pronte per essere ristampate."""
    import nutrition_engine
    comp = nutrition_engine.compute_diet(diet, selections)
    ss = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=16 * mm, bottomMargin=12 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm, title=diet.get("title", "Dieta"))
    el = [Paragraph(diet.get("title", "Piano alimentare"), ss["H1"]),
          HRFlowable(width="100%", color=AMBER, thickness=1, spaceAfter=8)]
    for day in comp["days"]:
        el.append(Paragraph(f"{day['day']}  ·  {day['totals']['kcal']:.0f} kcal", ss["H2"]))
        for meal in day["meals"]:
            el.append(Paragraph(meal["meal"], ss["Body"]))
            for grp in meal["groups"]:
                for o in grp["options"]:
                    mark = "✓ " if o.get("active") else ("  o " if not o.get("default") else "  ")
                    el.append(Paragraph(f"{mark}{o['food']} {o['grams']:.0f} g", ss["Small"]))
            el.append(Spacer(1, 4))
    doc.build(el)
    return path
