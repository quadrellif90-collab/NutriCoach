"""NutriCoach — Modulo antropometria e calcoli del fabbisogno.

Implementa i calcoli standard usati dalle suite professionali per
nutrizionisti:
- IMC / BMI
- BMR (Metabolismo Basale) — equazione di Mifflin-St Jeor (1990)
- TDEE (fabbisogno energetico totale) — BMR x coefficiente di attività
- % grassa e massa magra da pieghe cutanee (Durnin & Womersley, 4 siti:
  tricipite, bicipite, sottoscapolare, sovrailiaca) — equazione generale
- Rapporto Vita-Fianchi (WHR)
- FFMI (Fat-Free Mass Index)
- Peso ideale (formule di Lorentz / BMI target)
- Fabbisogno proteico raccomandato (LARN: 0.8-1.0 g/kg; atleti 1.2-2.0 g/kg)

Tutti i calcoli sono funzioni pure -> facili da testare e da riusare sia
nel backend che nell'export PDF.
"""

from math import sqrt, log10


# Coefficienti di attività fisica (Physical Activity Level, PAL)
ACTIVITY_FACTORS = {
    "sedentario": 1.2,
    "leggero": 1.375,
    "moderato": 1.55,
    "intenso": 1.725,
    "atleta": 1.9,
}


def bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm:
        return None
    h = height_cm / 100.0
    return round(weight_kg / (h * h), 1)


def bmi_class(k):
    if k is None:
        return ""
    if k < 18.5:
        return "Sottopeso"
    if k < 25:
        return "Normopeso"
    if k < 30:
        return "Sovrappeso"
    if k < 35:
        return "Obesità I"
    if k < 40:
        return "Obesità II"
    return "Obesità III"


def bmr_mifflin(weight_kg, height_cm, age, sex):
    """Metabolismo basale (kcal/giorno), Mifflin-St Jeor."""
    if not (weight_kg and height_cm and age):
        return None
    s = 5 if sex and sex.upper().startswith("M") else -161
    return round(10 * weight_kg + 6.25 * height_cm - 5 * age + s)


def tdee(bmr, activity="moderato"):
    if bmr is None:
        return None
    f = ACTIVITY_FACTORS.get(activity, 1.55)
    return round(bmr * f)


def fat_percent_durnin(skinfolds, age, sex):
    """% grassa da 4 pieghe (tricipite, bicipite, sottoscapolare, sovrailiaca).

    skinfolds: dict con chiavi tricipite, bicipite, sottoscapolare, sovrailiaca
    (mm). Ritorna (body_density, fat_pct) o (None, None) se dati mancanti.
    Equazione di Durnin & Womersley (1974), log somma 4 pieghe.
    """
    need = ["tricipite", "bicipite", "sottoscapolare", "sovrailiaca"]
    if not all(skinfolds.get(k) for k in need):
        return None, None
    S = sum(skinfolds[k] for k in need)
    logS = log10(S)
    if sex and sex.upper().startswith("M"):
        D = 1.1715 - 0.0779 * logS
    else:
        D = 1.1581 - 0.0725 * logS
    fat = (4.95 / D - 4.50) * 100
    return round(D, 4), round(fat, 1)


def whr(waist_cm, hip_cm):
    if not (waist_cm and hip_cm):
        return None
    return round(waist_cm / hip_cm, 2)


def whr_risk(whr, sex):
    if whr is None:
        return ""
    if sex and sex.upper().startswith("M"):
        return "Rischio aumentato" if whr >= 0.90 else "Rischio normale"
    return "Rischio aumentato" if whr >= 0.85 else "Rischio normale"


def ffmi(weight_kg, fat_pct, height_cm):
    """Fat-Free Mass Index (kg/m^2)."""
    if not (weight_kg and fat_pct is not None and height_cm):
        return None
    ff_mass = weight_kg * (1 - fat_pct / 100.0)
    h = height_cm / 100.0
    return round(ff_mass / (h * h), 1)


def ideal_weight_lorentz(height_cm, sex):
    """Peso ideale (Lorentz)."""
    if not height_cm:
        return None
    if sex and sex.upper().startswith("M"):
        return round((height_cm - 100) - ((height_cm - 150) / 4), 1)
    return round((height_cm - 100) - ((height_cm - 150) / 2.5), 1)


def protein_target(weight_kg, activity_level="moderato", athlete=False):
    """Fabbisogno proteico (g/giorno). LARN base 0.8-1.0 g/kg;
    atleti 1.2-2.0 g/kg (ACSM/IOC)."""
    if not weight_kg:
        return None
    if athlete:
        gpg = 1.6
    elif activity_level in ("intenso", "atleta"):
        gpg = 1.4
    else:
        gpg = 1.0
    return round(weight_kg * gpg, 0)


def compute_all(profile, measurement):
    """Calcola tutto da profilo + misura. Ritorna dict completo.

    profile: {sex, age, height_cm, activity, athlete}
    measurement: {weight_kg, waist_cm, hip_cm, skinfolds:{...}}
    """
    sex = profile.get("sex")
    age = profile.get("age")
    h = profile.get("height_cm")
    act = profile.get("activity", "moderato")
    athlete = profile.get("athlete", False)
    w = measurement.get("weight_kg")
    out = {}
    out["bmi"] = bmi(w, h)
    out["bmi_class"] = bmi_class(out["bmi"])
    out["bmr"] = bmr_mifflin(w, h, age, sex)
    out["tdee"] = tdee(out["bmr"], act)
    dens, fat = fat_percent_durnin(measurement.get("skinfolds", {}), age, sex)
    out["body_density"] = dens
    out["fat_pct"] = fat
    out["fat_mass_kg"] = round(w * (fat / 100.0), 1) if fat is not None else None
    out["lean_mass_kg"] = round(w * (1 - (fat or 0) / 100.0), 1) if fat is not None else None
    out["whr"] = whr(measurement.get("waist_cm"), measurement.get("hip_cm"))
    out["whr_risk"] = whr_risk(out["whr"], sex)
    out["ffmi"] = ffmi(w, fat, h)
    out["ideal_weight"] = ideal_weight_lorentz(h, sex)
    out["protein_g"] = protein_target(w, act, athlete)
    return out


if __name__ == "__main__":
    prof = {"sex": "M", "age": 35, "height_cm": 180, "activity": "intenso", "athlete": True}
    meas = {"weight_kg": 75, "waist_cm": 84, "hip_cm": 98,
            "skinfolds": {"tricipite": 10, "bicipite": 8, "sottoscapolare": 12, "sovrailiaca": 14}}
    r = compute_all(prof, meas)
    for k, v in r.items():
        print(f"{k:14s}: {v}")
