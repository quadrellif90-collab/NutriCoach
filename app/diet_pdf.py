"""NutriCoach v2.3.0 — Export piano alimentare in PDF professionale."""
import os, io, datetime as dt
from fpdf import FPDF

W = 210
H = 297
MARGIN = 15
CW_DAY = 18
CW_MEAL = (W - 2 * MARGIN - CW_DAY) / 5
COL_W = [CW_DAY] + [CW_MEAL] * 5
MEALS = ["colazione", "spuntino", "pranzo", "spuntino2", "cena"]
DAY_NAMES = {"lun":"Lunedì","mar":"Martedì","mer":"Mercoledì",
             "gio":"Giovedì","ven":"Venerdì","sab":"Sabato","dom":"Domenica"}

# Font search
_FONT_PATH = None
for p in ["C:\\Windows\\Fonts\\arial.ttf","C:\\Windows\\Fonts\\Arial.ttf",
          "C:\\Windows\\Fonts\\segoeui.ttf","C:\\Windows\\Fonts\\Calibri.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"]:
    if os.path.isfile(p): _FONT_PATH = p; break

FONT_NAME = "Uni" if _FONT_PATH else "Helvetica"

class DietPDF(FPDF):
    def __init__(self, brand=None):
        super().__init__()
        self.brand = brand or {}
        if _FONT_PATH:
            self.add_font("Uni","",_FONT_PATH,uni=True)
            self.add_font("Uni","B",_FONT_PATH,uni=True)
            self.add_font("Uni","I",_FONT_PATH,uni=True)
            self.add_font("Uni","BI",_FONT_PATH,uni=True)

    def _f(self,style="",size=10): self.set_font(FONT_NAME,style,size)
    def _tc(self,r,g,b): self.set_text_color(r,g,b)

    def header(self):
        bn = (self.brand.get("clinic_name") or "").strip()
        # Logo + clinic name
        logo_url = self.brand.get("logo_url","")
        if logo_url and os.path.isfile(logo_url):
            try:
                self.image(logo_url, MARGIN, 8, 16)
                self.set_x(MARGIN+18)
            except: pass
        tc = self.brand.get("theme_color","")
        if not tc: tc = "#0d9488"
        if tc.startswith("#"): tc = tc[1:]
        if len(tc) < 6:
            tc = "0d9488"
        r,g,b = int(tc[0:2],16), int(tc[2:4],16), int(tc[4:6],16)
        self._f("B",14); self._tc(r,g,b)
        title = bn if bn else "NutriCoach - Piano Alimentare"
        self.cell(0,8,title,align="C",new_x="LMARGIN",new_y="NEXT")
        self._f("",8); self._tc(100,116,139)
        sub = f"Generato il {dt.date.today().strftime('%d/%m/%Y')}"
        if bn: sub += f" | {bn}"
        else: sub += " | NutriCoach v2"
        self.cell(0,4,sub,align="C",new_x="LMARGIN",new_y="NEXT")
        self.line(MARGIN,self.get_y(),W-MARGIN,self.get_y()); self.ln(4)

    def footer(self):
        self.set_y(-15); self._f("I",7); self._tc(148,163,184)
        self.cell(0,10,f"Pagina {self.page_no()}/{{nb}}",align="C")

    def patient_info(self, patient):
        self._f("B",11); self._tc(30,41,59)
        self.cell(0,6,f"Paziente: {patient.get('name','-')}",new_x="LMARGIN",new_y="NEXT")
        self._f("",9); self._tc(100,116,139)
        meta = []
        if patient.get("goal"): meta.append(f"Obiettivo: {patient['goal']}")
        if patient.get("sport"): meta.append(f"Sport: {patient['sport']}")
        if patient.get("conditions"):
            meta.append(f"Condizioni: {', '.join(patient['conditions'][:3])}")
        self.cell(0,5," | ".join(meta) if meta else "",new_x="LMARGIN",new_y="NEXT")
        self.ln(3)

    def targets_section(self, targets):
        self._f("B",10); self._tc(30,41,59)
        self.cell(0,6,"Obiettivi Nutrizionali",new_x="LMARGIN",new_y="NEXT")
        self._f("",9); self._tc(100,116,139)
        kcal = targets.get("kcal",0)
        p=targets.get("protein_pct",0); c=targets.get("carb_pct",0); f=targets.get("fat_pct",0)
        self.cell(0,5,f"{int(kcal)} kcal | P {p}% ({int(kcal*p/100/4)}g) | C {c}% ({int(kcal*c/100/4)}g) | F {f}% ({int(kcal*f/100/9)}g)",
                  new_x="LMARGIN",new_y="NEXT")
        if targets.get("preset"):
            self._f("I",8)
            self.cell(0,4,f"Protocollo: {targets['preset']}",new_x="LMARGIN",new_y="NEXT")
        self.ln(3)

    def meal_plan_table(self, days_data, macros):
        self._f("B",9)
        self.set_fill_color(13,148,136); self._tc(255,255,255)
        headers = ["Giorno"]+[m.capitalize() for m in MEALS]
        for i,h in enumerate(headers):
            self.cell(COL_W[i],6,h,border=1,fill=True,align="C")
        self.ln()

        for day_key in ["lun","mar","mer","gio","ven","sab","dom"]:
            yb = self.get_y()
            dn = DAY_NAMES.get(day_key,day_key)
            meals = days_data.get(day_key,{})
            dm = macros.get(day_key,{})

            texts = [dn]
            mx = 1
            for meal in MEALS:
                items = meals.get(meal,[])
                txt = "\n".join([f"{i.get('food','-')} {i.get('grams',0)}g" for i in items]) if items else "-"
                texts.append(txt)
                lines = txt.count("\n")+1
                if lines > mx: mx = lines

            rh = max(6, mx*3.5+2)
            if yb+rh > H-25:
                self.add_page()
                self._f("B",9)
                self.set_fill_color(13,148,136); self._tc(255,255,255)
                for i,h in enumerate(headers):
                    self.cell(COL_W[i],6,h,border=1,fill=True,align="C")
                self.ln()

            rh = max(6, mx*3.5+2)
            xs = self.get_x(); ys = self.get_y()

            for i,txt in enumerate(texts):
                x = xs + sum(COL_W[:i])
                self.set_xy(x,ys)
                if i==0:
                    self._f("B",7); self._tc(13,148,136)
                else:
                    self._f("",6.5); self._tc(30,41,59)
                self.multi_cell(COL_W[i],3.5,txt,border=1)

            self.set_xy(xs,ys+rh)
            if dm:
                self._f("I",6); self._tc(100,116,139)
                self.cell(sum(COL_W),4,
                    f"{dn}: {int(dm.get('kcal',0))} kcal | P {int(dm.get('protein_g',0))}g | C {int(dm.get('carbs_g',0))}g | F {int(dm.get('fat_g',0))}g",
                    align="R",new_x="LMARGIN",new_y="NEXT")
            self.ln(2)

    def recommendations(self, recs):
        if not recs: return
        if self.get_y() > H-40: self.add_page()
        self._f("B",10); self._tc(13,148,136)
        self.cell(0,6,"Raccomandazioni",new_x="LMARGIN",new_y="NEXT")
        self._f("",8); self._tc(30,41,59)
        for r in recs[:5]:
            txt = r.get("condition",r) if isinstance(r,dict) else str(r)
            self.cell(5,4,"*"); self.multi_cell(W-2*MARGIN-5,4,txt)

    def excluded_foods(self, foods):
        if not foods: return
        if self.get_y() > H-35: self.add_page()
        self._f("B",10); self._tc(239,68,68)
        self.cell(0,6,"Alimenti Esclusi",new_x="LMARGIN",new_y="NEXT")
        self._f("",8); self._tc(30,41,59)
        self.multi_cell(W-2*MARGIN,4,", ".join(foods))


def generate_diet_pdf(patient,targets,days_data,macros,recommendations=None,excluded_foods=None,brand=None):
    pdf = DietPDF(brand=brand)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True,margin=20)
    pdf.add_page()
    pdf.patient_info(patient)
    pdf.targets_section(targets)
    pdf.meal_plan_table(days_data,macros)
    pdf.recommendations(recommendations or [])
    pdf.excluded_foods(excluded_foods or [])
    return pdf.output()


def generate_shopping_pdf(patient, by_category, brand=None):
    """Genera lista spesa in PDF raggruppata per categoria."""
    pdf = DietPDF(brand=brand)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf._f("B", 14); pdf._tc(13, 148, 136)
    pdf.cell(0, 8, f"Lista della Spesa - {patient.get('name', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf._f("", 8); pdf._tc(100, 116, 139)
    pdf.cell(0, 4, f"Generato il {dt.date.today().strftime('%d/%m/%Y')} | NutriCoach v2", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for cat, items in by_category.items():
        if pdf.get_y() > H - 40:
            pdf.add_page()
        pdf._f("B", 11); pdf._tc(13, 148, 136)
        pdf.cell(0, 6, cat.capitalize(), new_x="LMARGIN", new_y="NEXT")
        pdf._f("", 9); pdf._tc(30, 41, 59)
        for it in items:
            pdf.cell(4, 5, "□")
            pdf.cell(0, 5, f"{it['food']} — {int(it['grams'])} g", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    return pdf.output()


# ─── BIA REPORT PDF (grafici evolutivi disegnati) ──────────────────────────

def _draw_line_chart(pdf, x, y, w, h, values, color=(13, 148, 136), label=""):
    """Disegna un mini grafico a linee da una lista di valori (None saltati)."""
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pts) < 1:
        return
    pdf.set_draw_color(*color)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 116, 139)
    if label:
        pdf.text(x, y - 1, label)
    if len(pts) == 1:
        # singolo punto
        px = x + 5
        py = y + h - 5
        pdf.circle(px, py, 1, style="F")
        return
    vals = [v for _, v in pts]
    vmin, vmax = min(vals), max(vals)
    rng = (vmax - vmin) or 1
    n = len(pts)
    for i in range(1, n):
        x1 = x + 3 + (pts[i-1][0] / max(1, n-1)) * (w - 6)
        y1 = y + h - 4 - ((pts[i-1][1] - vmin) / rng) * (h - 8)
        x2 = x + 3 + (pts[i][0] / max(1, n-1)) * (w - 6)
        y2 = y + h - 4 - ((pts[i][1] - vmin) / rng) * (h - 8)
        pdf.line(x1, y1, x2, y2)
    # cerchi sui punti
    pdf.set_fill_color(*color)
    for i, v in pts:
        px = x + 3 + (i / max(1, n-1)) * (w - 6)
        py = y + h - 4 - ((v - vmin) / rng) * (h - 8)
        pdf.circle(px, py, 0.8, style="F")


def generate_bia_report_pdf(patient, trend, brand=None):
    """Report PDF con grafici evolutivi multi-metrica."""
    pdf = DietPDF(brand=brand)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf._f("B", 14); pdf._tc(13, 148, 136)
    pdf.cell(0, 8, f"Report BIA - {patient.get('name', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf._f("", 8); pdf._tc(100, 116, 139)
    pdf.cell(0, 4, f"Generato il {dt.date.today().strftime('%d/%m/%Y')} | NutriCoach v2", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    dates = trend.get("dates", [])
    series = trend.get("series", {})
    labels = {
        "weight_kg": "Peso (kg)", "bf_pct": "BF%", "ffm_kg": "Massa magra (kg)",
        "tbw_kg": "Acqua totale (kg)", "phase_angle": "Angolo di fase (°)", "muscle_kg": "Muscolo (kg)", "bmi": "BMI",
    }
    colors = [(13,148,136),(239,68,68),(59,130,246),(34,197,94),(168,85,247),(245,158,11),(100,116,139)]
    for i, m in enumerate(trend.get("metrics", [])):
        if pdf.get_y() > H - 50:
            pdf.add_page()
        lab = labels.get(m, m)
        pdf._f("B", 10); pdf._tc(30, 41, 59)
        pdf.cell(0, 5, lab, new_x="LMARGIN", new_y="NEXT")
        _draw_line_chart(pdf, MARGIN, pdf.get_y(), W - 2*MARGIN, 22, series.get(m, []), colors[i % len(colors)])
        pdf.set_y(pdf.get_y() + 24)
    # Tabella riassuntivo
    if dates:
        pdf._f("B", 10); pdf._tc(13, 148, 136)
        pdf.cell(0, 6, "Dettaglio misurazioni", new_x="LMARGIN", new_y="NEXT")
        pdf._f("", 7); pdf._tc(30, 41, 59)
        for d in dates:
            pdf.cell(0, 4, d, new_x="LMARGIN", new_y="NEXT")
    return pdf.output()