"""NutriCoach v2.4.0 — Calcolo fabbisogno energetico (BMR/TDEE).

Formule: Mifflin-St Jeor, Harris-Benedict (rivista), Katch-McArdle (se BF% nota).
"""
import datetime as dt

ACTIVITY_FACTORS = {
    "sedentario": 1.2,
    "leggero": 1.375,
    "moderato": 1.55,
    "intenso": 1.725,
    "molto_intenso": 1.9,
}

GOAL_ADJUST = {
    "dimagrimento": -0.15,   # -15%
    "mantenimento": 0.0,
    "massa": 0.10,           # +10%
    "performance": 0.05,
}


def age_from_birth(birth_date):
    if not birth_date:
        return None
    try:
        b = dt.date.fromisoformat(str(birth_date)[:10])
        today = dt.date.today()
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    except Exception:
        return None


def bmr_mifflin(weight_kg, height_cm, age, sex):
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + (5 if str(sex).upper().startswith("M") else -161))


def bmr_harris(weight_kg, height_cm, age, sex):
    if str(sex).upper().startswith("M"):
        return round(88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age)
    return round(447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age)


def bmr_katch(weight_kg, bf_pct):
    lbm = weight_kg * (1 - bf_pct / 100.0)
    return round(370 + 21.6 * lbm)


def energy_needs(weight_kg, height_cm, age, sex, activity="moderato",
                 goal="mantenimento", bf_pct=None):
    """Calcola BMR con 3 formule + TDEE + target kcal secondo obiettivo."""
    res = {"inputs": {"weight_kg": weight_kg, "height_cm": height_cm, "age": age,
                      "sex": sex, "activity": activity, "goal": goal, "bf_pct": bf_pct}}
    formulas = {}
    if weight_kg and height_cm and age:
        formulas["mifflin"] = bmr_mifflin(weight_kg, height_cm, age, sex)
        formulas["harris"] = bmr_harris(weight_kg, height_cm, age, sex)
    if weight_kg and bf_pct:
        formulas["katch"] = bmr_katch(weight_kg, bf_pct)
    if not formulas:
        return {"error": "Servono peso, altezza ed età (o BF% per Katch-McArdle)"}
    res["bmr"] = formulas
    # BMR di riferimento: Katch se disponibile (più accurato con BF%), altrimenti Mifflin
    ref = formulas.get("katch") or formulas.get("mifflin")
    res["bmr_ref"] = ref
    factor = ACTIVITY_FACTORS.get(activity, 1.55)
    tdee = round(ref * factor)
    res["tdee"] = tdee
    adj = GOAL_ADJUST.get(goal, 0.0)
    res["target_kcal"] = round(tdee * (1 + adj))
    res["goal_adjustment_pct"] = int(adj * 100)
    # Range proteine consigliate
    res["protein_g_range"] = [round(weight_kg * 1.2), round(weight_kg * 2.0)] if weight_kg else None
    return res