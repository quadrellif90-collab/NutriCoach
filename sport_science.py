"""NutriCoach — Strategie pro adattate ad amatoriale/semi-pro.

Raccoglie approcci documentati nel mondo elite (WorldTour ciclismo, calcio
professionistico) e li rende APPLICABILI dal nutrizionista su clienti
amatoriali/semi-pro. Tutto e' basato su letteratura 2024-2026 (vedi NOTE).
NON e' consulenza medica: sono linee guida pratiche di periodizzazione.

Fonti (realI):
- Cao W et al., "Carbohydrate Supplementation Approaches...", PMC 2025 (review).
- Outside/Velo + Olympics.com: Tour de France 2025 fueling 100-120 g/h (fino 200).
- EF Pro Cycling gut-training; Aspetar journal "Emerging Challenges in Recovery
  for the Elite Football Player" (FIFA World Cup 2026 targeted topic, 2024-2026).
- Ranchordas MK et al., nutritional recovery elite soccer (PMC 2017).
- Rackard G et al., "Nutrition Strategies to Promote Sleep in Elite Athletes"
  (2025).
- UCI declaration on ketone supplements: USA sconsiglia l'uso (no evidenza
  performance/recovery convincente). Cyclingnews/MDPI 2024.

Single source of truth: i target qui dentro alimentano il pianificatore come
gli altri preset (diet_presets), cosi' numeri e note non divergono.
"""

# ---------------------------------------------------------------------------
# 1) FUEL FOR THE WORK REQUIRED (FTWR) — periodizzazione carb endurance
#    Invece di "train-low", si adatta la disponibilita' di carboidrati alla
#    richiesta della seduta. Valori come g di carboidrati per kg di peso (g/kg)
#    nella giornata e g/h durante lo sforzo (fonte: review Cao 2025 + TDFF 2025).
# ---------------------------------------------------------------------------
FUELING = {
    "note": (
        "Fuel for the Work Required: si dosano i carboidrati in base alla "
        "seduta, non si restringe in cieco. In gara i pro assumono 100-120 g/h "
        "(fino a 200 g/h in fasi severe, Tour de France 2025)."
    ),
    "daily_g_per_kg": {
        # giorno tipo di allenamento / gara / recupero
        "low":        {"label": "Basso carico / recupero", "g_per_kg": 3,  "carb_pct": 40},
        "moderate":   {"label": "Allenamento moderato",    "g_per_kg": 5,  "carb_pct": 50},
        "high":       {"label": "Alto carico / lungo",     "g_per_kg": 7,  "carb_pct": 55},
        "race":       {"label": "Gara / evento",           "g_per_kg": 8,  "carb_pct": 60},
    },
    "during_exercise_g_per_h": {
        "easy":    {"label": "Basso intensita'", "g_per_h": 30},
        "tempo":   {"label": "Medio/intensita'", "g_per_h": 60},
        "race":    {"label": "Gara / soglia",    "g_per_h": 90},
        "ultra":   {"label": "Ultradistanza",    "g_per_h": 120},
    },
}

# ---------------------------------------------------------------------------
# 2) RECOVERY MICROCYCLE (football pro -> amatoriale)
#    Fondamenta (priorita' 1): sonno 7-9h, nutrizione, idratazione.
#    Poi adjunct sequenziati per microciclo (Aspetar 2024/2026).
# ---------------------------------------------------------------------------
RECOVERY = {
    "foundations": [
        {"key": "sleep", "label": "Sonno 7-9h", "detail": "Igiene del sonno: camera buia/fresca, routine, niente schermi 30' prima."},
        {"key": "nutrition", "label": "Nutrizione post-sforzo", "detail": "0.4 g/kg proteina + 1.0-1.2 g/kg carb entro 1-2h; idratazione con sodio."},
        {"key": "hydration", "label": "Idratazione", "detail": "Recupero fluidi + elettroliti; controllo peso pre/post."},
    ],
    "microcycle": {
        # fase -> adjunct consigliati
        "match_day":      {"label": "Giorno gara", "adjunct": ["cooling", "compression"], "focus": "Ripristino rapido funzione"},
        "day_after":      {"label": "Giorno post-gara", "adjunct": ["active_recovery", "compression", "sleep"], "focus": "Drenaggio metabolico + sonno"},
        "training":       {"label": "Allenamento", "adjunct": [], "focus": "Adattamento (niente adjunct indiscriminati)"},
        "rest":           {"label": "Recupero / off", "adjunct": ["sleep", "mindfulness"], "focus": "Adattamento + recupero psicologico"},
    },
    "adjuncts": {
        "cooling":      "Raffreddamento (crioterapia/immersione) post match acuto.",
        "compression":  "Compressione per drenaggio.",
        "active_recovery": "Recupero attivo a bassa intensita'.",
        "sleep":        "Napping / igiene del sonno.",
        "mindfulness":  "Respirazione/mindfulness per fatica centrale.",
    },
    "note": (
        "Recovery periodizzato (Aspetar/FIFA 2026): le fondamenta (sonno, "
        "nutrizione, idratazione) vengono prime; gli adjunct si sequenziano "
        "secondo lo stress della seduta, non a caso."
    ),
}

# ---------------------------------------------------------------------------
# 3) KETONI ESOGENI — NOTA (UCI sconsiglia)
# ---------------------------------------------------------------------------
KETONES = {
    "recommended": False,
    "note": (
        "CHETONI ESOGENI: l'UCI (2024) sconsiglia l'uso nei ciclisti professionali "
        "per mancanza di evidenza convincente su performance/recovery; possibili "
        "effetti EPO ma rischi GI e costi elevati. Non proposti come strategia."
    ),
}

# ---------------------------------------------------------------------------
# 4) DISTRIBUZIONE PROTEICA (A) — totale giornaliero > timing
#    Fonti: Lak&Bagheri 2024 (Frontiers), meta MDPI 2025, USADA, Morton 2018,
#    Mamerow 2014. Totale 1.6-2.2 g/kg; 4-5 pasti da 0.25-0.4 g/kg o 20-40g;
#    ~3g leucina/pasto; finestra anabolica di ORE (non 30').
# ---------------------------------------------------------------------------
PROTEIN = {
    "note": (
        "La quantita' totale di proteina al giorno conta PIU' del timing. "
        "Target atleti: 1.6-2.2 g/kg. Distribuire in 4-5 pasti da 0.25-0.4 g/kg "
        "(o 20-40 g) per massimizzare MPS; ~3 g leucina/pasto; la 'finestra "
        "anabolica' dura ore, non 30'. Front-load a colazione."
    ),
    "per_kg_range": [1.6, 2.2],
    "meals_range": [4, 5],
    "per_meal_g_range": [20, 40],
    "per_meal_per_kg": [0.25, 0.40],
    "leucine_g_per_meal": 3.0,
    "myth": (
        "MITO della 'finestra anabolica' di 30': smentito da meta-analisi (MDPI "
        "2025) e Schoenfeld 2013/2017 — conta il totale giornaliero e una "
        "distribuzione equa, non il momento esatto pre/post."
    ),
}

# ---------------------------------------------------------------------------
# 5) GUT TRAINING (B) — assorbimento carb trainabile
#    Fonti: Cao 2025 (PMC), EF Pro Cycling gut-training 2025, Morton 2026.
#    Salire 30->120 g/h in ~4 settimane; rapporto 2:1 glucosio:fruttosio oltre 60 g/h.
# ---------------------------------------------------------------------------
GUT_TRAINING = {
    "note": (
        "L'assorbimento di carboidrati e' TRAINABILE. Si sale da ~30 a 120 g/h in "
        "~4 settimane usando il mix che si usera' in gara, con rapporto 2:1 "
        "glucosio:fruttosio oltre 60 g/h (TDFF 2025: 120 g/h)."
    ),
    "ratio_note": "Oltre 60 g/h usare 2:1 glucosio:fruttosio (doppi trasportatori SGLT1+GLUT5).",
    "protocol_weeks": [
        {"week": 1, "g_per_h": 30, "note": "Adatta lo stomaco al carico base."},
        {"week": 2, "g_per_h": 60, "note": "Introduce fruttosio (2:1) su uscite >90'."},
        {"week": 3, "g_per_h": 90, "note": "Simula intensita' gara con carb a 90 g/h."},
        {"week": 4, "g_per_h": 120, "note": "Target gara; tolleranza verificata."},
    ],
}

# ---------------------------------------------------------------------------
# 6) PERIODIZZAZIONE A BLOCCHI + FTWR (C) — macro-ciclo
#    Fonti: Rønnestad block periodization review; Issurin. Fasi -> target carb %.
# ---------------------------------------------------------------------------
BLOCK_PERIOD = {
    "note": (
        "Periodizzazione a blocchi (Rønnestad) supera la tradizionale su VO2max/"
        "Wmax. Ogni fase ha un target di carboidrati coerente con FTWR."
    ),
    "phases": {
        "base":       {"label": "Base (volume)",       "carb_pct": 55, "focus": "Aerobico, volume alto"},
        "build":      {"label": "Costruzione (intensita')", "carb_pct": 55, "focus": "Soglia/VO2, carico alto"},
        "peak":       {"label": "Picco (specifico)",   "carb_pct": 60, "focus": "Simulazioni gara, carb alto"},
        "taper":      {"label": "Defaticamento",        "carb_pct": 60, "focus": "Mantenere carb, ridurre volume"},
        "race":       {"label": "Gara",                "carb_pct": 65, "focus": "Carbossatura, 8-10 g/kg"},
        "off":        {"label": "Off / recupero",      "carb_pct": 45, "focus": "Mantenimento, meno carb"},
    },
}

# ---------------------------------------------------------------------------
# 7) CREATINA (D) — sicura e benefica, anche donne
#    Fonti: ISSN/Kreider 2025, Garcia 2025, Tam 2025.
# ---------------------------------------------------------------------------
CREATINE = {
    "note": (
        "Creatina monoidrato: sicura e benefica in tutto l'arco di vita, incluso "
        "donne/atlete (Kreider 2025, Garcia 2025, Tam 2025). Migliora forza/"
        "potenza e composizione corporea."
    ),
    "loading": {"g_per_kg": 0.3, "days": 5, "maintenance_g": 3.0,
                "note": "Loading 0.3 g/kg/die per 5-7 g, oppure 3-5 g/d sole (piu' lento)."},
    "myth_note": "Nessun 'effetto wash-out' pericoloso; idratazione adeguata.",
}

# ---------------------------------------------------------------------------
# 8) WEARABLE RECOVERY (E) — HRV / sonno
#    Fonti: Topalidis 2024, Dasari 2024, Khawaja 2024, Schyvens 2025.
# ---------------------------------------------------------------------------
WEARABLE = {
    "note": (
        "Wearable (Oura/WHOOP/Garmin): seguire i TREND su settimane, non il "
        "giorno singolo. Metriche valide: RHR, HRV, durata sonno. Oura miglior "
        "staging sonno; WHOOP miglior loop sforzo-recupero; Garmin senza abbon."
    ),
    "valid_metrics": ["RHR (frequenza a riposo)", "HRV (trend notturno)", "durata sonno", "consistenza"],
    "best_practice": "Adatta l'intensita' nei giorni di basso recupero; riconosci trend HRV discendenti prima dell'overtraining.",
    "devices": {
        "oura": "Miglior staging sonno + temperatura (ciclo mestruale/malattia).",
        "whoop": "Miglior loop sforzo-recupero, HRV in sonno profondo.",
        "garmin": "Training Readiness + Body Battery, senza abbonamento.",
    },
}


def fueling_daily_targets(day_type, body_weight_kg):
    """Ritorna target carb giornalieri (g) per tipo di giorno FTWR."""
    d = FUELING["daily_g_per_kg"].get(day_type)
    if not d or not body_weight_kg:
        return None
    g = round(body_weight_kg * d["g_per_kg"], 0)
    return {"day_type": day_type, "label": d["label"], "g_per_kg": d["g_per_kg"],
            "carb_g": int(g), "carb_pct": d["carb_pct"]}


def fueling_during_targets(intensity):
    """Ritorna g/h di carb durante lo sforzo."""
    d = FUELING["during_exercise_g_per_h"].get(intensity)
    if not d:
        return None
    return {"intensity": intensity, "label": d["label"], "g_per_h": d["g_per_h"]}


def protein_dist_targets(body_weight_kg, g_per_kg=1.8, meals=4):
    """Ritorna distribuzione proteica: totale g, g/pasto, leucina/pasto."""
    if not body_weight_kg:
        return None
    total = round(body_weight_kg * g_per_kg, 0)
    per_meal = round(total / meals, 0)
    return {
        "g_per_kg": g_per_kg, "meals": meals,
        "total_g": int(total), "per_meal_g": int(per_meal),
        "leucine_g_per_meal": PROTEIN["leucine_g_per_meal"],
    }


def creatine_dose(body_weight_kg, sex="M"):
    """Ritorna dose loading + mantenimento (g)."""
    if not body_weight_kg:
        return None
    loading = round(body_weight_kg * CREATINE["loading"]["g_per_kg"], 0)
    return {
        "sex": sex,
        "loading_g_per_day": int(loading),
        "loading_days": CREATINE["loading"]["days"],
        "maintenance_g_per_day": CREATINE["loading"]["maintenance_g"],
    }


def block_phase_target(phase, body_weight_kg, kcal):
    """Ritorna target carb per fase di periodizzazione a blocchi."""
    d = BLOCK_PERIOD["phases"].get(phase)
    if not d:
        return None
    carb_pct = d["carb_pct"]
    carb_kcal = kcal * carb_pct / 100.0
    carb_g = round(carb_kcal / 4, 0)
    return {
        "phase": phase, "label": d["label"], "focus": d["focus"],
        "carb_pct": carb_pct, "kcal": kcal, "carb_g": int(carb_g),
    }


def science_bundle():
    """Payload per la UI 'Scienza Sport'."""
    return {
        "fueling": FUELING,
        "recovery": RECOVERY,
        "ketones": KETONES,
        "protein": PROTEIN,
        "gut_training": GUT_TRAINING,
        "block_period": BLOCK_PERIOD,
        "creatine": CREATINE,
        "wearable": WEARABLE,
    }
