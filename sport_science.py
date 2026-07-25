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


def science_bundle():
    """Payload per la UI 'Scienza Sport'."""
    return {
        "fueling": FUELING,
        "recovery": RECOVERY,
        "ketones": KETONES,
    }
