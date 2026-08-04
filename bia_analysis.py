"""NutriCoach — Analisi BIA avanzata e riassunto clinico.

Calcola indici derivati (BMI, BMR con Mifflin/Harris/Katch, FFMI, FMI,
TBW atteso con formula di Watson, ECW/ICW ratio, idratazione, PhA, BF% vs
range di riferimento per sesso ed età) e genera una valutazione testuale
in italiano della condizione del paziente, incrociando i dati BIA con
quelli antropometrici e clinici (patologie, obiettivi sportivi).

Nessuna dipendenza esterna: matematica pura.
"""

import datetime as dt

# ─── Range di riferimento (consensus: Gallagher, Bosy-Westphal, android BIA) ───

def _fr(age):
    """Fascia età per i range BF%."""
    if age is None:
        return "adult"
    if age < 20:
        return "adult"
    if age < 40:
        return "20-39"
    if age < 60:
        return "40-59"
    return "60+"

BF_PCT_RANGE = {  # (min, max) accettabile per sesso e fascia età
    "M": {"adult": (10, 22), "20-39": (8, 20), "40-59": (11, 22), "60+": (13, 24)},
    "F": {"adult": (20, 32), "20-39": (21, 33), "40-59": (23, 35), "60+": (24, 36)},
}

PHA_RANGE = {  # interpretazione PhA a 50 kHz (gradi)
    "low": (None, 5.5),     # <-5.5 ridotto (fragilità/denutrizione)
    "normal": (5.5, 6.5),   # 5.5-6.5 medio
    "good": (6.5, None),    # >6.5 buono (massa cellulare integra)
}

ECW_ICW_RATIO_RANGE = (0.78, 1.0)  # ECW/ICW normale

ECW_TBW_PCT_RANGE = (38.0, 43.0)   # ECW come % del TBW

FFMI_RANGE = {  # Fat-Free Mass Index per sesso (sarcopenia se < soglia)
    "M": {"low": 17.0, "normal_low": 18.0, "normal_high": 23.0},
    "F": {"low": 15.0, "normal_low": 16.0, "normal_high": 20.0},
}

BMI_RANGE = {"low": 18.5, "normal_high": 24.9, "overweight": 29.9}

TBW_PCT_RANGE = {"M": (50.0, 65.0), "F": (45.0, 60.0)}  # TBW come % peso


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None  # NaN check


def age_from_birth(birth_date):
    if not birth_date:
        return None
    try:
        b = dt.date.fromisoformat(str(birth_date)[:10])
        today = dt.date.today()
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    except Exception:
        return None


# ─── Calcoli derivati ───

def calculate(bia, patient=None, anthro=None):
    """Calcola tutti gli indici derivati da una misurazione BIA.

    bia      -> dict con i campi di bia_readings
    patient  -> dict paziente (sex, birth_date, pathologies, goal, sport)
    anthro   -> dict antropometria (waist_cm, hip_cm, whr, fat_pct_durnin)
    Ritorna  -> dict {value, label, unit, range_text, status, note}
    """
    res = {}
    w = _num(bia.get("weight_kg"))
    h = _num(bia.get("height_cm"))
    bf = _num(bia.get("bf_pct"))
    mm = _num(bia.get("mm_pct"))
    sex = str((patient or {}).get("sex", "M") or "M").upper()
    if not sex.startswith("M") and not sex.startswith("F"):
        sex = "M"
    s_letter = "M" if sex.startswith("M") else "F"
    age = age_from_birth((patient or {}).get("birth_date"))

    # BMI
    if w and h and h > 0:
        bmi = round(w / ((h / 100.0) ** 2), 1)
        if bmi < BMI_RANGE["low"]:
            bmi_s = "basso"
        elif bmi <= BMI_RANGE["normal_high"]:
            bmi_s = "normale"
        elif bmi <= BMI_RANGE["overweight"]:
            bmi_s = "sovrappeso"
        else:
            bmi_s = "obesità"
        res["bmi"] = {"value": bmi, "unit": "kg/m²", "label": "BMI",
                      "range": "18.5-24.9", "status": bmi_s,
                      "note": "Indice di massa corporea."}

    # BMR (Mifflin-St Jeor come principale, + Harris, + Katch se BF%)
    if w and h and age:
        miff = bmr_mifflin(w, h, age, s_letter)
        har = bmr_harris(w, h, age, s_letter)
        res["bmr_mifflin"] = {"value": miff, "unit": "kcal/die", "label": "BMR (Mifflin-St Jeor)",
                              "status": "normale", "note": "Mifflin-St Jeor (10·kg+6.25·cm−5·età±5/161)."}
        res["bmr_harris"] = {"value": har, "unit": "kcal/die", "label": "BMR (Harris-Benedict)",
                             "status": "normale", "note": "Harris-Benedict rivista."}
    if w and bf is not None and _num(bia.get("bf_kg")) is None:
        katch = bmr_katch(w, bf)
        res.setdefault("bmr_mifflin", {})
        res["bmr_katch"] = {"value": katch, "unit": "kcal/die", "label": "BMR (Katch-McArdle)",
                            "status": "normale", "note": "No lean=370+21.6·LBM (richiede BF%)."}

    # Massa magra / grassa e indici normalizzati (FFMI, FMI)
    ffm_kg = _num(bia.get("ffm_kg"))
    if ffm_kg is None and w is not None and bf is not None:
        ffm_kg = round(w * (1 - bf / 100.0), 1)
    if w is not None and bf is not None and _num(bia.get("bf_kg")) is None:
        res["bf_kg_der"] = {"value": round(w * bf / 100.0, 1), "unit": "kg",
                            "label": "Massa grassa (calcolata)",
                            "status": "normale", "note": "Peso×BF%."}
    if w is not None and bf is not None:
        if _num(bia.get("mm_kg")) is None and _num(bia.get("smm_kg")) is None:
            res["mm_kg_der"] = {"value": round(w * (1 - bf / 100.0), 1), "unit": "kg",
                                "label": "Massa magra (stima)", "status": "normale",
                                "note": "Stima da BF% (LBM, non selettivo)."}
    if ffm_kg and h and h > 0:
        ffmi = round(ffm_kg / ((h / 100.0) ** 2), 1)
        r = FFMI_RANGE[s_letter]
        if ffmi < r["low"]:
            ffmi_s = "basso (rischio sarcopenia)"
        elif ffmi < r["normal_low"]:
            ffmi_s = "modesto"
        else:
            ffmi_s = "adeguato"
        res["ffmi"] = {"value": ffmi, "unit": "kg/m²", "label": "FFMI",
                       "range": f"{r['normal_low']}-{r['normal_high']}",
                       "status": ffmi_s, "note": "Indice di massa magra (kg FFM/m²)."}
    if w and h and bf is not None and h > 0:
        fmi = round(w * bf / 100.0 / ((h / 100.0) ** 2), 1)
        res["fmi"] = {"value": fmi, "unit": "kg/m²", "label": "FMI",
                      "note": "Indice di massa grassa (kg FM/m²).", "status": "normale"}

    # Composizione: BF% / MM% vs range di riferimento
    if bf is not None:
        lo, hi = BF_PCT_RANGE[s_letter][_fr(age)]
        if bf < lo:
            bf_s = "basso"
        elif bf <= hi:
            bf_s = "nella norma"
        else:
            bf_s = "elevato"
        res["bf_pct"] = {"value": bf, "unit": "%", "label": "Massa grassa",
                         "range": f"{lo}-{hi} ({s_letter}, fascia {_fr(age)})",
                         "status": bf_s,
                         "note": "Percentuale di massa grassa, range di riferimento per sesso/età."}
    if mm is not None:
        res["mm_pct"] = {"value": mm, "unit": "%", "label": "Massa muscolare",
                         "status": "normale", "note": "Percentuale massa muscolare."}

    # Idratazione: TBW% e ratio ECW/ICW
    tbw = _num(bia.get("tbw_l"))
    ecw = _num(bia.get("ecw_l"))
    icw = _num(bia.get("icw_l"))
    if tbw and w:
        tbw_pct = round(tbw / w * 100, 1)
        lo, hi = TBW_PCT_RANGE[s_letter]
        tbw_s = "nella norma" if lo <= tbw_pct <= hi else ("basso" if tbw_pct < lo else "alto")
        res["tbw_pct"] = {"value": tbw_pct, "unit": "%", "label": "Idratazione (TBW%)",
                          "range": f"{lo}-{hi}", "status": tbw_s,
                          "note": "Acqua totale come % del peso."}
    if ecw and icw and icw > 0:
        ratio = round(ecw / icw, 2)
        lo, hi = ECW_ICW_RATIO_RANGE
        ratio_s = "normale" if lo <= ratio <= hi else ("basso" if ratio < lo else "elevato (over-idratazione)")
        res["ecw_icw"] = {"value": ratio, "unit": "", "label": "Rapporto ECW/ICW",
                          "range": f"{lo}-{hi}", "status": ratio_s,
                          "note": ">1.0 segnala tendenza a ritenzione/edema; <0.78 verso disidratazione."}
    if ecw and tbw and tbw > 0:
        ecw_tbw = round(ecw / tbw * 100, 1)
        lo, hi = ECW_TBW_PCT_RANGE
        ecwtbw_s = "normale" if lo <= ecw_tbw <= hi else ("basso" if ecw_tbw < lo else "elevato")
        res["ecw_tbw_pct"] = {"value": ecw_tbw, "unit": "%", "label": "ECW su TBW",
                              "range": f"{lo}-{hi}", "status": ecwtbw_s,
                              "note": "Rapporto extrasellulare/totale; >43% indica over-idratazione."}

    # PhA
    pha = _num(bia.get("pha"))
    if pha is not None:
        if pha < PHA_RANGE["low"][1]:
            pha_s = "ridotto (massa cellulare carente)"
        elif pha < PHA_RANGE["normal"][1]:
            pha_s = "medio"
        else:
            pha_s = "buono (prognosi favorevole)"
        res["pha"] = {"value": pha, "unit": "°", "label": "Angolo di fase",
                      "range": "≥6.5 buono · 5.5-6.5 medio · <5.5 ridotto",
                      "status": pha_s,
                      "note": "Indice di qualità cellulare a 50 kHz."}

    # SMM / BCM + percentuali di massa per il radar
    smm = _num(bia.get("smm_kg"))
    if smm:
        res["smm_kg"] = {"value": smm, "unit": "kg", "label": "Massa muscolo-scheletrica",
                         "status": "normale", "note": "Skeletal Muscle Mass."}
    if w:
        if ffm_kg:
            res["ffm_pct"] = {"value": round(ffm_kg / w * 100, 1), "unit": "%",
                              "label": "Massa magra", "status": "normale",
                              "note": "Massa magra come % del peso (FFM/peso)."}
        if smm:
            res["smm_pct"] = {"value": round(smm / w * 100, 1), "unit": "%",
                              "label": "SMM su peso", "status": "normale",
                              "note": "Massa muscolo-scheletrica come % del peso."}
    bcm = _num(bia.get("bcm_kg"))
    if bcm:
        res["bcm_kg"] = {"value": bcm, "unit": "kg", "label": "Massa cellulare corporea",
                         "status": "normale", "note": "Body Cell Mass (componente metabolicamente attiva)."}

    # Antropometria: WHR e pliche (se presenti)
    if anthro:
        waist = _num(anthro.get("waist_cm"))
        hip = _num(anthro.get("hip_cm"))
        if waist and hip and hip > 0:
            whr = round(waist / hip, 2)
            whr_lim = 0.90 if s_letter == "M" else 0.85
            whr_s = "normale" if whr <= whr_lim else "elevato (rischio cardiometabolico)"
            res["whr"] = {"value": whr, "unit": "", "label": "Rapporto vita/fianchi",
                          "range": f"≤{whr_lim}", "status": whr_s,
                          "note": ">soglia indica grasso addominale."}
        if waist:
            abdo_lim = 102 if s_letter == "M" else 88
            wa_s = "normale" if waist <= abdo_lim else "circonferenza elevata"
            res["waist_cm"] = {"value": waist, "unit": "cm", "label": "Circonferenza vita",
                               "range": f"≤{abdo_lim}", "status": wa_s,
                               "note": "Indicatore di adiposità centrale."}
        durnin = _num(anthro.get("fat_pct_durnin"))
        if durnin:
            res["fat_pct_durnin"] = {"value": durnin, "unit": "%", "label": "BF% (pliche Durnin)",
                                     "status": "normale", "note": "Stima da pliche cutanee."}

    return res


def _flag(res, key, cond, label, good):
    if cond:
        res.setdefault("flags", []).append(
            {"key": key, "item": label, "good": good, "text": f"{label}."})


def summarize(bia, patient=None, anthro=None):
    """Genera il riassunto clinico in italiano a partire dai calcoli."""
    calc = calculate(bia, patient, anthro)
    flags = []

    # Flag clinicamente rilevanti
    for k in ("bf_pct", "bmi", "tbw_pct", "ecw_icw", "ecw_tbw_pct", "pha", "ffmi", "whr", "waist_cm"):
        v = calc.get(k)
        if not v:
            continue
        st = v.get("status", "")
        if k == "bf_pct" and "elevato" in st:
            flags.append({"key": k, "item": "Massa grassa", "good": False,
                          "text": f"BF% a {v['value']}{v.get('unit','')} è oltre il range di riferimento ({v.get('range','')})."})
        elif k == "bf_pct" and "basso" in st:
            flags.append({"key": k, "item": "Massa grassa", "good": True,
                          "text": f"BF% a {v['value']}{v.get('unit','')} è sotto il range di riferimento; monitorare apporto energetico."})
        elif k == "bmi" and st not in ("normale",):
            flags.append({"key": k, "item": "BMI", "good": st not in ("sovrappeso", "obesità"),
                          "text": f"BMI {v['value']} ({st})."})
        elif k == "pha" and "ridotto" in st:
            flags.append({"key": k, "item": "Angolo di fase", "good": False,
                          "text": f"PhA {v['value']}° ridotto: possibile carenza di massa cellulare."})
        elif k == "pha" and "buono" in st:
            flags.append({"key": k, "item": "Angolo di fase", "good": True,
                          "text": f"PhA {v['value']}° buono: massa cellulare integra."})
        elif k == "ffmi" and "basso" in st:
            flags.append({"key": k, "item": "Massa magra (FFMI)", "good": False,
                          "text": f"FFMI {v['value']} è basso: rischio di sarcopenia."})
        elif "over" in st or "elevato" in st and k in ("ecw_icw", "ecw_tbw_pct", "tbw_pct"):
            flags.append({"key": k, "item": v["label"], "good": False,
                          "text": f"{v['label']} {v['value']}{v.get('unit','')} segnala alterazione idrica."})
        elif k in ("whr", "waist_cm") and "elevato" in st:
            flags.append({"key": k, "item": v["label"], "good": False,
                          "text": f"{v['label']} {v['value']}{v.get('unit','')} è elevato ({v.get('range','')})."})

    # Testo narrativo
    lines = []
    name = (patient or {}).get("name", "paziente")
    w = calc.get("bmi")
    bf = calc.get("bf_pct")
    ffmi = calc.get("ffmi")
    pha = calc.get("pha")
    tbw = calc.get("tbw_pct")
    ecm = calc.get("ecw_icw") or calc.get("ecw_tbw_pct")

    lines.append(f"Il {name} presenta un quadro metabolico complessivamente "
                 f"{'equilibrato' if not flags else 'da monitorare'}.")

    if w:
        lines.append(f"BMI {w['value']} ({w['status']}).")
    if bf:
        lines.append(f"Massa grassa {bf['value']}% ({bf['status']}).")
    if ffmi:
        lines.append(f"Indice di massa magra FFMI {ffmi['value']} ({ffmi['status']}).")
    if pha:
        lines.append(f"Angolo di fase {pha['value']}° — {pha['status']}.")
    if tbw:
        lines.append(f"Idratazione (TBW) {tbw['value']}% ({tbw['status']}).")
    if ecm:
        lines.append(f"Equilibrio idrico compartimentale {ecm['label']} {ecm['value']} ({ecm['status']}).")

    pathologies = (patient or {}).get("pathologies") or "{}"
    try:
        import json as _json
        patho = _json.loads(pathologies) if isinstance(pathologies, str) else pathologies
        plist = patho.get("list") if isinstance(patho, dict) else None
    except Exception:
        plist = None
    if plist:
        lines.append(f"Comorbidità riportate: {', '.join(plist)}.")
        # Incrocio semplice: patologie che richiedono attenzione
        risk = [p for p in plist if any(k in p.lower() for k in
                ("diabet", "ipertension", "gott", "dislipid", "cardio", "ren", "edem"))]
        if risk:
            lines.append("Attenzione alle comorbidità: " + ", ".join(risk) +
                         " — integrare con la valutazione clinica dell'equilibrio idrico e lipidico.")

    if not flags:
        lines.append("Non sono emerse anomalie di rilievo dai parametri disponibili.")
    else:
        bad = [f for f in flags if not f["good"]]
        good = [f for f in flags if f["good"]]
        if bad:
            lines.append("Punti di attenzione: " + "; ".join(f["text"] for f in bad) + ".")
        if good:
            lines.append("Aspetti nella norma/positivi: " + "; ".join(f["text"] for f in good) + ".")

    return {"calculations": calc, "flags": flags, "summary": " ".join(lines)}


# Re-export compat da energy_calc (per non duplicare logica)
from app.energy_calc import bmr_mifflin, bmr_harris, bmr_katch, age_from_birth as _afe  # noqa
age_from_birth = _afe