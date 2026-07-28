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
    def __init__(self):
        super().__init__()
        if _FONT_PATH:
            self.add_font("Uni","",_FONT_PATH,uni=True)
            self.add_font("Uni","B",_FONT_PATH,uni=True)
            self.add_font("Uni","I",_FONT_PATH,uni=True)
            self.add_font("Uni","BI",_FONT_PATH,uni=True)

    def _f(self,style="",size=10): self.set_font(FONT_NAME,style,size)
    def _tc(self,r,g,b): self.set_text_color(r,g,b)

    def header(self):
        self._f("B",14); self._tc(13,148,136)
        self.cell(0,8,"NutriCoach - Piano Alimentare",align="C",new_x="LMARGIN",new_y="NEXT")
        self._f("",8); self._tc(100,116,139)
        self.cell(0,4,f"Generato il {dt.date.today().strftime('%d/%m/%Y')} | NutriCoach v2",
                  align="C",new_x="LMARGIN",new_y="NEXT")
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


def generate_diet_pdf(patient,targets,days_data,macros,recommendations=None,excluded_foods=None):
    pdf = DietPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True,margin=20)
    pdf.add_page()
    pdf.patient_info(patient)
    pdf.targets_section(targets)
    pdf.meal_plan_table(days_data,macros)
    pdf.recommendations(recommendations or [])
    pdf.excluded_foods(excluded_foods or [])
    return pdf.output()