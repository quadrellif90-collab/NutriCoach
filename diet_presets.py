"""NutriCoach — Preset di dieta con distribuzione macro.

Ogni preset definisce una distribuzione di macronutrienti (% di kcal) e,
dove utile, grammi di proteina per kg di peso (g/kg). Il nutrizionista puo'
selezionare un preset e poi SOVRASCRIVERE i valori nel configuratore: i
numeri mostrati sono la "vista" dei preset, non un calcolo nascosto.

Tutte le fonti sono diete documentate in letteratura (non mediche):
 - Mediterranea: ~40% C / 20% P / 40% F (grassi soprattutto insaturi)
 - Zona: 40% C / 30% P / 30% F (blocchi 40-30-30)
 - CKD (Ciclica Chetogenica): 5 giorni std + 2 giorni reload carb (qui il target medio)
 - Carb Cycling: alterna giorni alto/basso carb (target medio)
 - Alto proteico: 35-40% P
 - Vegano/Plant-based: 55% C / 18% P / 27% F
 - Keto classica: 5% C / 20% P / 75% F
 - Personalizzato: lascia i campi editabili a mano

Single source of truth: i target sono sempre {kcal, p, c, f} (grammi/giorno).
"""

# Distribuzione % kcal per macronutriente (p=proteine, c=carboidrati, f=grassi)
PRESETS = {
    "mediterranea": {
        "label": "Mediterranea",
        "p_pct": 20, "c_pct": 40, "f_pct": 40,
        "protein_g_per_kg": 1.2,
        "note": "Grassi prevalenti insaturi (olio EVO, pesce, frutta secca).",
    },
    "zona": {
        "label": "Zona (40-30-30)",
        "p_pct": 30, "c_pct": 40, "f_pct": 30,
        "protein_g_per_kg": 1.6,
        "note": "Blocchi 40% carb / 30% prot / 30% grassi.",
    },
    "ckd": {
        "label": "CKD (Ciclica Chetogenica)",
        "p_pct": 25, "c_pct": 20, "f_pct": 55,
        "protein_g_per_kg": 2.0,
        "note": "5 giorni keto + 2 giorni reload carb (target medio settimanale).",
    },
    "carbcycling": {
        "label": "Carb Cycling",
        "p_pct": 30, "c_pct": 35, "f_pct": 35,
        "protein_g_per_kg": 2.0,
        "note": "Alterna giorni alto/basso carb; qui il target medio.",
    },
    "altoproteico": {
        "label": "Alto proteico",
        "p_pct": 38, "c_pct": 35, "f_pct": 27,
        "protein_g_per_kg": 2.2,
        "note": "Per ricomposizione/ipada massa.",
    },
    "vegano": {
        "label": "Vegano / Plant-based",
        "p_pct": 18, "c_pct": 55, "f_pct": 27,
        "protein_g_per_kg": 1.1,
        "note": "Proteine da legumi, soia, cereali.",
    },
    "keto": {
        "label": "Keto classica",
        "p_pct": 20, "c_pct": 5, "f_pct": 75,
        "protein_g_per_kg": 1.5,
        "note": "Very low carb (<10% kcal).",
    },
    "personalizzato": {
        "label": "Personalizzato",
        "p_pct": None, "c_pct": None, "f_pct": None,
        "protein_g_per_kg": None,
        "note": "Inserisci i valori a mano.",
    },
}


def preset_list():
    """Ritorna lista di {key,label,note} per la UI."""
    return [{"key": k, "label": v["label"], "note": v.get("note", "")} for k, v in PRESETS.items()]


def preset_targets(key, kcal, weight_kg=None):
    """Calcola i target {kcal,p,c,f} (grammi/giorno) da un preset.

    kcal: target calorico giornaliero.
    weight_kg: se fornito, la proteina segue g/kg (altrimenti la % del preset).
    Ritorna anche i valori % per comodità UI.
    """
    p = PRESETS.get(key, PRESETS["personalizzato"])
    pct_p = p["p_pct"]; pct_c = p["c_pct"]; pct_f = p["f_pct"]
    # se il preset e' personalizzato o mancano %, ritorna None (UI usa valori manuali)
    if pct_p is None or pct_c is None or pct_f is None:
        return {"kcal": kcal, "p": None, "c": None, "f": None,
                "p_pct": None, "c_pct": None, "f_pct": None, "manual": True}
    # proteina: se peso dato, privilegia g/kg
    if weight_kg:
        g_p = round(weight_kg * (p["protein_g_per_kg"] or 0), 0)
        kcal_from_p = g_p * 4
        # ricalibra le % rimanenti su carb/grassi in proporzione al preset
        rem = max(kcal - kcal_from_p, 0)
        g_c = round(rem * (pct_c / (pct_c + pct_f)) / 4, 0)
        g_f = round(rem * (pct_f / (pct_c + pct_f)) / 9, 0)
    else:
        g_p = round(kcal * pct_p / 100.0 / 4, 0)
        g_c = round(kcal * pct_c / 100.0 / 4, 0)
        g_f = round(kcal * pct_f / 100.0 / 9, 0)
    return {
        "kcal": kcal,
        "p": int(g_p), "c": int(g_c), "f": int(g_f),
        "p_pct": pct_p, "c_pct": pct_c, "f_pct": pct_f,
        "manual": False,
    }
