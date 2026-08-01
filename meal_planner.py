"""NutriCoach — Motore piano alimentare (SINGLE SOURCE OF TRUTH).

Tutto il calcolo di macronutrienti e micronutrienti passa da qui:
- compute_entry(name, grams, custom=None): nutrienti di una voce (BDD ref + custom)
- aggregate(entries): somma macro+micro di una lista di voci
- generate_plan(targets, options): genera un diario settimanale a partire
  dai target (kcal, P, C, F) bilanciando colazione/pranzo/cena/spuntini.
- diary_totals(cid, day): aggrega le voci del diario del cliente (VISTA).
- diary_full(cid, day): voci + totale + flags cliniche.

I valori degli alimenti arrivano da nutrition_db (BDD) o da foods_custom (db).

ESTENSIONI CLINICHE (2026):
- FODMAP-aware meal generation (IBS/SIBO)
- Meal spacing enforcement (SIBO)
- Chrononutrition timing hints
- Histamine-aware filtering (intolleranza istamina/MCAS)
- Condition-specific food substitutions
- Multi-condition conflict check
- Extended micronutrient tracking (omega3, vit D, zinco, B12, folati, selenio, vit A, vit E)
- Dietary protocol phases (eliminazione/reintroduzione/mantenimento)
"""

import db
import nutrition_db as ndb

try:
    import clinical_nutrition as _clin
except ImportError:
    _clin = None

import random as _random
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# ESCLUSIONI CLINICHE
# Mappa condizione clinica -> alimenti del BDD da escludere dal generatore.
# VISTA delle regole in clinical_nutrition (foods_avoid): qui i nomi sono
# normalizzati sulle chiavi reali di nutrition_db usate dal planner.
# ─────────────────────────────────────────────────────────────────────────────
CONDITION_EXCLUSIONS = {
    "lactose_intolerance": ["mozzarella", "ricotta", "formaggio bianco", "yogurt greco"],
    "celiac": ["pasta", "pane comune", "pane integrale", "avena", "fiocchi d'avena", "farro"],
    "ncgs": ["pasta", "pane comune", "pane integrale", "farro"],
    "ibs": ["fiocchi d'avena", "avena", "mela", "pera", "cavolfiore", "olive"],
    "gerd": ["pomodori", "arancia", "kiwi", "peperoni"],
    "dyspepsia": ["peperoni", "olive", "arachidi"],
    "hypertension": ["prosciutto cotto", "olive"],
    "diabetes_t2": ["pane comune", "banana"],
    "food_allergy": [],   # dipende dall'allergene: usare campo allergies
    "eoe": ["mozzarella", "ricotta", "formaggio bianco", "yogurt greco", "uova gallina",
            "pane comune", "pasta"],
    "obesity": [],
    "osteoporosis": [],
    "histamine_intolerance": ["salmone", "tonno", "sgombro", "prosciutto cotto",
                              "prosciutto crudo", "salame", "mortadella", "spinaci",
                              "avocado", "aceto balsamico", "formaggio bianco"],
    "mcas": ["salmone", "tonno", "sgombro", "prosciutto cotto", "spinaci",
             "avocado", "formaggio bianco", "cioccolato fondente"],
    "sibo": ["fiocchi d'avena", "avena", "mela", "pera", "cavolfiore", "olive",
             "lenticchie", "ceci", "fagioli", "piselli"],
}

# parole chiave allergie (campo libero cliente) -> alimenti BDD
ALLERGY_KEYWORDS = {
    "lattosio": ["mozzarella", "ricotta", "formaggio bianco", "yogurt greco"],
    "latte": ["mozzarella", "ricotta", "formaggio bianco", "yogurt greco"],
    "glutine": ["pasta", "pane comune", "pane integrale", "avena", "fiocchi d'avena", "farro"],
    "uova": ["uova gallina"],
    "uovo": ["uova gallina"],
    "pesce": ["tonno", "salmone"],
    "frutta secca": ["mandorle", "noci", "arachidi"],
    "noci": ["noci", "mandorle"],
    "arachidi": ["arachidi"],
    "soia": [],
    "crostacei": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# SOSTITUZIONI SPECIFICHE PER CONDIZIONE
# Quando un cibo viene escluso, prova a sostituirlo con un'alternativa
# clinicamente appropriata prima di cadere su scelta casuale.
# ─────────────────────────────────────────────────────────────────────────────
CONDITION_SUBSTITUTIONS = {
    "ibs": {
        "cipolle": "cipollotto verde",
        "aglio": "olio all'aglio (infuso, non pezzi)",
        "cavolfiore": "zucchine",
        "mela": "fragole",
        "pera": "kiwi",
        "fiocchi d'avena": "riso basmati",
        "avena": "quinoa",
        "latte intero": "latte di mandorla",
        "latte parzialmente scremato": "latte di avena",
        "porri": "sedano",
        "finocchi": "carote",
        "pane comune": "riso basmati",
        "pane integrale": "pane di riso",
        "farro": "quinoa",
        "lenticchie": "tofu",
        "ceci": "tofu",
        "fagioli": "riso basmati",
        "piselli": "fagiolini",
    },
    "histamine_intolerance": {
        "salmone": "orata",
        "tonno": "merluzzo",
        "sgombro": "spigola",
        "prosciutto cotto": "petto di pollo cotto fresco",
        "prosciutto crudo": "bresaola fresca",
        "salame": "fesa di tacchino",
        "mortadella": "fesa di tacchino",
        "spinaci": "broccoli",
        "avocado": "olio extravergine d'oliva",
        "formaggio bianco": "yogurt greco",
        "aceto balsamico": "succo di limone",
    },
    "mcas": {
        "salmone": "orata",
        "tonno": "merluzzo",
        "sgombro": "spigola",
        "prosciutto cotto": "petto di pollo cotto fresco",
        "spinaci": "broccoli",
        "avocado": "olio extravergine d'oliva",
        "formaggio bianco": "yogurt greco",
        "cioccolato fondente": "miele (piccole dosi)",
    },
    "sibo": {
        "fiocchi d'avena": "riso basmati",
        "avena": "quinoa",
        "mela": "fragole",
        "pera": "kiwi",
        "cavolfiore": "zucchine",
        "lenticchie": "tofu",
        "ceci": "tofu",
        "fagioli": "riso basmati",
        "piselli": "fagiolini",
    },
    "diabetes_t2": {
        "pane comune": "pane integrale",
        "banana": "mela",
    },
    "gerd": {
        "pomodori": "zucchine",
        "arancia": "banana",
        "kiwi": "mela",
        "peperoni": "carote",
    },
    "celiac": {
        "pasta": "riso basmati",
        "pane comune": "pane di riso",
        "pane integrale": "pane di riso integrale",
        "avena": "quinoa",
        "fiocchi d'avena": "quinoa",
        "farro": "quinoa",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# CHRONONUTRITION: suggerimenti di timing pasti in base alla condizione
# ─────────────────────────────────────────────────────────────────────────────
CHRONONUTRITION_TIPS = {
    "diabetes_t2": [
        "Distribuire carboidrati equamente tra i pasti; evitare pasti carboidratici la sera",
        "Consumare carboidrati complessi a colazione per stabilità glicemica",
    ],
    "ibs": [
        "Pasti regolari, stessi orari ogni giorno; pasti più leggeri la sera",
        "Masticare lentamente, mangiare senza fretta",
    ],
    "sibo": [
        "Pasti regolari, stessi orari ogni giorno; pasti più leggeri la sera",
        "Evitare spuntini tra i pasti per favorire il migrating motor complex",
    ],
    "gerd": [
        "Ultimo pasto 3h prima di coricarsi; cena leggera",
        "Non sdraiarsi dopo i pasti; mantenere posizione eretta 30min",
    ],
    "histamine_intolerance": [
        "Cucinare fresco e consumare subito; non consumare cibi avanzati",
        "Evitare alimenti fermentati e stagionati",
    ],
    "mcas": [
        "Cucinare fresco e consumare subito; non consumare cibi avanzati",
        "Mangiare porzioni piccole per ridurre carico istaminico",
    ],
    "dyspepsia": [
        "Pasti piccoli e frequenti (5-6/giorno); masticare lentamente",
        "Evitare di riempire troppo lo stomaco",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# FASE DIETETICA: alimenti consentiti / restritti per (condizione, fase)
# ─────────────────────────────────────────────────────────────────────────────
PHASE_FOODS = {
    ("ibs", "elimination"): {
        "allowed": [
            "riso basmati", "riso integrale", "quinoa", "patate", "patate dolci",
            "petto di pollo", "tacchino", "manzo magro", "uova gallina",
            "tonno", "merluzzo", "gamberi",
            "zucchine", "carote", "spinaci", "broccoli", "peperoni",
            "melanzane", "insalata mista", "lattuga", "cetrioli",
            "fragole", "kiwi", "arancia", "banana", "mirtilli",
            "olio extravergine d'oliva", "mandorle", "noci",
            "tofu", "olive", "yogurt greco",
        ],
        "restricted": [
            "cipolle", "aglio", "porri", "finocchi", "cavolfiore", "cavolo",
            "mela", "pera", "frutta secca",
            "lenticchie", "ceci", "fagioli", "piselli", "fave",
            "pane comune", "pane integrale", "farro", "avena", "fiocchi d'avena",
            "latte intero", "latte parzialmente scremato",
        ],
    },
    ("ibs", "reintroduction"): {
        "allowed": [
            # Fase 2: test graduale gruppi FODMAP
            "riso basmati", "quinoa", "patate",
            "petto di pollo", "tacchino", "manzo magro", "uova gallina",
            "tonno", "salmone", "merluzzo",
            "zucchine", "carote", "spinaci", "broccoli", "peperoni",
            "fragole", "kiwi", "arancia", "banana",
            "olio extravergine d'oliva", "mandorle",
            "tofu", "yogurt greco",
            # Test singoli gruppi FODMAP (porzioni piccole):
            "lenticchie", "ceci",     # test GOS (25g cotti)
            "mela", "pera",           # test fruttosio (1 pezzo)
            "pane integrale",         # test fruttani (1 fetta)
        ],
        "restricted": [
            "cipolle", "aglio", "porri",  # testare separatamente
            "cavolfiore",                 # testare separatamente
            "latte intero",               # testare lattosio separatamente
        ],
    },
    ("ibs", "maintenance"): {
        "allowed": [],   # vuoto = tutti gli alimenti tollerati individualmente
        "restricted": [],
    },
    ("sibo", "elimination"): {
        "allowed": [
            "riso basmati", "riso integrale", "patate", "patate dolci",
            "petto di pollo", "tacchino", "manzo magro", "uova gallina",
            "merluzzo", "orata", "spigola", "gamberi",
            "zucchine", "carote", "spinaci", "broccoli", "peperoni",
            "melanzane", "insalata mista", "lattuga", "cetrioli", "sedano",
            "fragole", "kiwi", "arancia", "banana",
            "olio extravergine d'oliva", "tofu", "olive",
        ],
        "restricted": [
            "lenticchie", "ceci", "fagioli", "fagioli borlotti", "fave", "piselli",
            "cipolle", "aglio", "porri", "finocchi", "cavolfiore", "cavolo",
            "mela", "pera", "pane comune", "pane integrale", "farro", "avena",
            "latte intero", "latte parzialmente scremato",
        ],
    },
    ("histamine_intolerance", "elimination"): {
        "allowed": [
            "petto di pollo", "tacchino", "fesa di tacchino", "manzo magro",
            "vitello", "coniglio",
            "riso basmati", "riso integrale", "quinoa", "patate", "patate dolci",
            "zucchine", "carote", "cetrioli", "insalata mista", "lattuga",
            "sedano", "broccoli", "cavolfiore", "verdure miste",
            "fragole", "kiwi", "arancia", "mirtilli", "lamponi",
            "olio extravergine d'oliva", "tofu", "olive",
            "yogurt greco",
        ],
        "restricted": [
            "salmone", "tonno", "tonno in scatola", "sgombro", "acciughe", "trota",
            "prosciutto cotto", "prosciutto crudo", "salame", "mortadella", "salsiccia",
            "formaggio bianco", "formaggio fresco",
            "spinaci", "pomodori", "peperoni", "passata di pomodoro",
            "avocado", "melanzane", "aceto balsamico",
            "cioccolato fondente", "cacao amaro", "miele",
            "frutta secca", "frutta disidratata",
        ],
    },
    ("histamine_intolerance", "reintroduction"): {
        "allowed": [
            "petto di pollo", "tacchino", "manzo magro", "uova gallina",
            "riso basmati", "quinoa", "patate",
            "zucchine", "carote", "broccoli", "insalata mista",
            "fragole", "kiwi", "arancia",
            "olio extravergine d'oliva", "tofu", "yogurt greco",
            # Test graduale (piccole dosi, fresco cucinato):
            "mozzarella",             # test latticini
            "pomodori",               # test vegetali fermentati
            "mandorle", "noci",       # test frutta secca
        ],
        "restricted": [
            "salmone", "tonno", "sgombro", "acciughe",  # pesce alto istamina
            "prosciutto crudo", "salame", "mortadella",  # salumi fermentati
            "avocado", "spinaci", "aceto balsamico",
            "cioccolato fondente",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# PASTI STANDARD e loro quota dei target
# ─────────────────────────────────────────────────────────────────────────────
MEAL_DISTRIBUTIONS = {
    3: [("colazione", 0.25), ("pranzo", 0.40), ("cena", 0.35)],
    4: [("colazione", 0.25), ("spuntino", 0.10), ("pranzo", 0.35), ("cena", 0.30)],
    5: [("colazione", 0.20), ("spuntino", 0.10), ("pranzo", 0.35), ("spuntino2", 0.10), ("cena", 0.25)],
    6: [("colazione", 0.18), ("spuntino", 0.08), ("pranzo", 0.30), ("spuntino2", 0.08), ("merenda", 0.08), ("cena", 0.28)],
    7: [("colazione", 0.17), ("spuntino", 0.07), ("spuntino2", 0.07), ("pranzo", 0.28), ("merenda", 0.07), ("spuntino3", 0.07), ("cena", 0.27)],
}
# Default to 5 meals for backward compatibility
MEALS = MEAL_DISTRIBUTIONS[5]


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIE ALIMENTI per comporre un pasto bilanciato
# ─────────────────────────────────────────────────────────────────────────────
_PROTEINS = ["petto di pollo", "uova gallina", "tonno", "salmone", "mozzarella",
             "yogurt greco", "tacchino", "manzo magro", "ricotta", "formaggio bianco",
             "prosciutto cotto", "fesa di tacchino"]
_CARBs = ["pasta", "riso basmati", "pane comune", "patate", "avena",
          "fiocchi d'avena", "pane integrale", "riso integrale", "quinoa", "farro"]
_VEG = ["pomodori", "zucchine", "spinaci", "broccoli", "insalata mista",
        "peperoni", "carote", "cavolfiore", "verdure miste", "finocchi"]
_FATS = ["olio extravergine d'oliva", "avocado", "mandorle", "noci", "semi di girasole",
         "olive", "arachidi"]
_FRUIT = ["mela", "banana", "arancia", "kiwi", "fragole", "pera"]


# ─────────────────────────────────────────────────────────────────────────────
# Soglie FODMAP (grammi)
# ─────────────────────────────────────────────────────────────────────────────
_FODMAP_MEAL_THRESHOLD = 0.75    # g per pasto
_FODMAP_DAY_THRESHOLD = 1.50     # g per giorno


def excluded_foods(conditions=None, allergies_text=""):
    """Alimenti del BDD da escludere date condizioni cliniche + allergie testuali."""
    out = set()
    for c in conditions or []:
        out.update(CONDITION_EXCLUSIONS.get(c, []))
    txt = (allergies_text or "").lower()
    for kw, foods in ALLERGY_KEYWORDS.items():
        if kw in txt:
            out.update(foods)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# FILTRI CLINICI AVANZATI
# ─────────────────────────────────────────────────────────────────────────────

def _filter_high_histamine(foods_list, conditions):
    """Rimuove alimenti con istamina alta/media se il cliente ha histamine_intolerance o mcas."""
    histamine_conditions = {"histamine_intolerance", "mcas"}
    if not (set(conditions or []) & histamine_conditions):
        return foods_list
    return [f for f in foods_list
            if ndb.food_histamine_level(f) not in ("high", "medium")]


def _filter_by_phase(foods_list, conditions, phase):
    """Filtra gli alimenti in base alla fase di protocollo dietetico."""
    if not conditions or not phase:
        return foods_list
    for c in conditions:
        key = (c, phase)
        pf = PHASE_FOODS.get(key)
        if pf:
            restricted = set(pf.get("restricted", []))
            foods_list = [f for f in foods_list if f not in restricted]
    return foods_list


def _apply_substitution(food, conditions):
    """Se il cibo è escluso, cerca una sostituzione clinica."""
    if not conditions:
        return food
    for c in conditions:
        subs = CONDITION_SUBSTITUTIONS.get(c, {})
        if food in subs:
            sub = subs[food]
            # verifica che il sostituto esista nel database
            if ndb._norm(sub):
                return sub
    return food


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE / AGGREGATE
# ─────────────────────────────────────────────────────────────────────────────

def compute_entry(name, grams, custom=None):
    """Nutrienti di una voce. `custom` = dict per_100g (da foods_custom)."""
    grams = float(grams or 0)
    if custom:
        f = float(custom.get("kcal", 0))
        return {
            "food": name, "matched": True,
            "kcal": round(f * grams / 100.0, 1),
            "p": round(float(custom.get("p", 0)) * grams / 100.0, 1),
            "c": round(float(custom.get("c", 0)) * grams / 100.0, 1),
            "f": round(float(custom.get("f", 0)) * grams / 100.0, 1),
            "fib": round(float(custom.get("fib", 0)) * grams / 100.0, 1),
            "sug": round(float(custom.get("sug", 0)) * grams / 100.0, 1),
            "salt": round(float(custom.get("salt", 0)) * grams / 100.0, 2),
            "ca": round(float(custom.get("ca", 0)) * grams / 100.0, 1),
            "fe": round(float(custom.get("fe", 0)) * grams / 100.0, 2),
            "vitc": round(float(custom.get("vitc", 0)) * grams / 100.0, 1),
            "k": round(float(custom.get("k", 0)) * grams / 100.0, 1),
            "mg": round(float(custom.get("mg", 0)) * grams / 100.0, 1),
            # estensioni micro: per cibo custom, default 0
            "omega3": 0.0, "vit_d": 0.0, "zinc": 0.0, "b12": 0.0,
            "folate": 0.0, "selenium": 0.0, "vit_a": 0.0, "vit_e": 0.0,
        }
    return ndb.nutrition_for(name, grams)


def _empty():
    """Dizionario zeri per somma nutrienti (macro + micro base + micro estesi)."""
    return {
        "kcal": 0.0, "p": 0.0, "c": 0.0, "f": 0.0, "fib": 0.0, "sug": 0.0,
        "salt": 0.0, "ca": 0.0, "fe": 0.0, "vitc": 0.0, "k": 0.0, "mg": 0.0,
        # micro estesi (EXTENDED_MICROS da nutrition_db)
        "omega3": 0.0, "vit_d": 0.0, "zinc": 0.0, "b12": 0.0,
        "folate": 0.0, "selenium": 0.0, "vit_a": 0.0, "vit_e": 0.0,
    }


def aggregate(entries):
    """Somma i nutrienti di una lista di voci (dict da compute_entry)."""
    tot = _empty()
    for e in entries:
        for k in tot:
            tot[k] += e.get(k, 0) or 0
    for k in tot:
        tot[k] = round(tot[k], 1)
    return tot


# ─────────────────────────────────────────────────────────────────────────────
# COMPOSIZIONE PASTO
# ─────────────────────────────────────────────────────────────────────────────

def _meal_combo(protein, carb, veg, fat, fruit, t_kcal, t_p, alts=None, t_carb=None):
    """Costruisce un pasto bilanciato e lo SCALA verso il target kcal.

    alts: dict {categoria: [lista alimenti]} da cui pescare le 'alternative'
          per ciascun cibo (stile Dietowin: 'o alternativa').
    t_carb: target grammi carb del pasto (opzionale). Se fornito, il carb
          viene ricalibrato verso questo valore (usato dai protocolli a fasi
          come carb cycling / CKD per differenziare i giorni).
    per ciascun cibo (stile referto Dietowin: 'o [alternativa]'). Per ogni
    cibo scelto si allegheranno fino a 2 swap della stessa categoria.
    """
    alts = alts or {}
    p_g = 150 if protein in ("petto di pollo", "tacchino", "manzo magro", "fesa di tacchino") else 100
    c_g = 70 if carb in ("pasta", "riso basmati") else 50
    v_g = 150
    f_ml = 10 if fat == "olio extravergine d'oliva" else 15
    fr_g = 120 if fruit else 0
    items = []
    if protein:
        items.append({"food": protein, "g": p_g, "cat": "protein"})
    if carb:
        items.append({"food": carb, "g": c_g, "cat": "carb"})
    if veg:
        items.append({"food": veg, "g": v_g, "cat": "veg"})
    if fat:
        items.append({"food": fat, "g": f_ml, "cat": "fat"})
    if fruit:
        items.append({"food": fruit, "g": fr_g, "cat": "fruit"})

    # ── allegato alternative per ciascun cibo ──
    for it in items:
        pool = [x for x in alts.get(it["cat"], []) if x != it["food"]]
        it["alternatives"] = pool[:2] if pool else []

    entries = [compute_entry(i["food"], i["g"]) for i in items]
    tot = aggregate(entries)
    # scala le grammature verso il target kcal del pasto (single source of truth:
    # i target del preset/configuratore guidano il piano, non porzioni fisse)
    if t_kcal and tot["kcal"] > 0:
        factor = max(0.4, min(2.5, t_kcal / tot["kcal"]))
        for i in items:
            i["g"] = round(i["g"] * factor)
        entries = [compute_entry(i["food"], i["g"]) for i in items]
        tot = aggregate(entries)
    # ricalibra il carb verso il target di fase (carb cycling / CKD)
    if t_carb is not None:
        carb_item = next((i for i in items if i["cat"] == "carb"), None)
        if carb_item:
            carb_entry = compute_entry(carb_item["food"], carb_item["g"])
            if carb_entry["c"] > 0:
                cf = max(0.2, min(3.0, t_carb / carb_entry["c"]))
                carb_item["g"] = round(carb_item["g"] * cf)
                tot = aggregate([compute_entry(i["food"], i["g"]) for i in items])
    return tot, items


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLLI A FASI (CKD, Carb Cycling, Keto, ecc.)
# ─────────────────────────────────────────────────────────────────────────────
def _phase_targets(preset, base, day_index, total_days):
    """Ritorna i target {kcal,p,c,f} (grammi/giorno) per il giorno `day_index`
    secondo il protocollo `preset`, partendo dai target base `base`.

    I protocolli "a fasi" applicano pattern settimanali reali (non solo medie %):
      - ckd (Ciclica Chetogenica): 5 giorni keto (carb ~5%) + 2 giorni reload
        (carb alti). Pattern: lun-mar-mer-gio-ven = keto, sab-dom = reload.
      - carbcycling: alterna giorni alto/basso carb (es. 4 alto / 3 basso).
      - keto: tutti i giorni cheto.
      - others (mediterranea, zona, ...): target uniformi.
    """
    from diet_presets import PRESETS, preset_targets
    preset = (preset or "").lower()
    # target base dai macro % del preset (se presente), altrimenti usa base
    pct = PRESETS.get(preset)
    if pct and pct.get("p_pct") is not None:
        t = preset_targets(preset, base["kcal"], None)
        base_k = base["kcal"]
        base_p = t["p"]; base_c = t["c"]; base_f = t["f"]
    else:
        base_k, base_p, base_c, base_f = base["kcal"], base["p"], base["c"], base["f"]

    di = day_index % max(1, total_days)

    if preset == "ckd":
        # 5 giorni keto, 2 reload (sab/dom)
        keto = di < 5
        if keto:
            c_pct = 0.05
        else:
            c_pct = 0.55
        # proteina alta stabile, grassi inversi ai carb
        p_g = base_p * (1.10 if keto else 1.0)
        c_g = base_k * c_pct / 4.0
        f_g = (base_k - p_g * 4 - c_g * 4) / 9.0
        return {"kcal": round(base_k), "p": round(p_g, 1), "c": round(c_g, 1), "f": round(max(f_g, 1), 1)}

    if preset == "carbcycling":
        # 4 giorni alto carb, 3 basso (alternanza: 0,1,2,3 alto; 4,5,6 basso)
        high = di < 4
        c_pct = 0.50 if high else 0.20
        p_g = base_p * (1.05 if high else 1.10)
        c_g = base_k * c_pct / 4.0
        f_g = (base_k - p_g * 4 - c_g * 4) / 9.0
        return {"kcal": round(base_k), "p": round(p_g, 1), "c": round(c_g, 1), "f": round(max(f_g, 1), 1)}

    if preset == "keto":
        c_pct = 0.05
        p_g = base_p
        c_g = base_k * c_pct / 4.0
        f_g = (base_k - p_g * 4 - c_g * 4) / 9.0
        return {"kcal": round(base_k), "p": round(p_g, 1), "c": round(c_g, 1), "f": round(max(f_g, 1), 1)}

    # default: uniforme
    return {"kcal": round(base_k), "p": round(base_p, 1), "c": round(base_c, 1), "f": round(base_f, 1)}


# ─────────────────────────────────────────────────────────────────────────────
# CALCOLO FODMAP
# ─────────────────────────────────────────────────────────────────────────────

def _compute_meal_fodmap(items):
    """Calcola i FODMAP totali (g) per un pasto dato la lista di items.

    Usa ndb.food_fodmap() che ritorna un dict con sotto-categorie FODMAP
    (fructan, gos, lactose, excess_fructose, sorbitol, mannitol, mannosio).
    Somma tutti i valori per ottenere il FODMAP totale.
    """
    total = 0.0
    for it in items:
        grams = float(it.get("g", 0))
        food = it.get("food", "")
        fp = ndb.food_fodmap(food)  # dict con chiavi FODMAP
        # somma tutti i componenti FODMAP
        meal_fodmap = sum(fp.values()) if isinstance(fp, dict) else float(fp or 0)
        total += meal_fodmap * grams / 100.0
    return round(total, 3)


# ─────────────────────────────────────────────────────────────────────────────
# GENERAZIONE PIANO
# ─────────────────────────────────────────────────────────────────────────────

def generate_plan(targets, options=None):
    """Genera un diario settimanale a partire dai target.

    targets = {kcal, p, c, f}  (valori GIORNALIERI)
    Accetta anche chiavi estese (protein/carbs/fat) per robustezza.

    options:
      - exclude_foods: set di nomi alimenti da escludere
      - conditions: lista di chiavi condizione clinica
      - phase: fase dieta ('elimination', 'reintroduction', 'maintenance')
      - min_hours_between_meals: ore minime tra pasti (default 2; SIBO: 3)
      - breakfast_time: orario colazione 'HH:MM' (default '08:00')
      - fodmap_threshold: soglia FODMAP giornaliera in g (default 1.5)
      - days: lista giorni (default 7 giorni)

    Ritorna {days:[{day, meals:[{meal, items, totals}], totals}], week_totals,
             fodmap_per_day, fodmap_per_meal, high_fodmap_warnings,
             meal_times, chrononutrition_tips, condition_conflicts}
    """
    # ── normalizza chiavi target (robusto a input parziale) ──
    t = targets or {}
    kcal = float(t.get("kcal") or t.get("kcal_target") or 2000)
    p = float(t.get("p") or t.get("protein") or 150)
    c = float(t.get("c") or t.get("carbs") or 200)
    f = float(t.get("f") or t.get("fat") or 67)
    targets = {"kcal": kcal, "p": p, "c": c, "f": f}
    options = options or {}

    days = options.get("days", ["lun", "mar", "mer", "gio", "ven", "sab", "dom"])
    conditions = options.get("conditions", [])
    phase = options.get("phase", "")
    min_hours = int(options.get("min_hours_between_meals", 2))
    breakfast_time = options.get("breakfast_time", "08:00")
    fodmap_threshold = float(options.get("fodmap_threshold", _FODMAP_DAY_THRESHOLD))
    num_meals = int(options.get("meals", 5))
    meals = MEAL_DISTRIBUTIONS.get(num_meals, MEAL_DISTRIBUTIONS[5])

    # SIBO: forza 3h tra pasti
    if "sibo" in conditions:
        min_hours = max(min_hours, 3)

    # ── esclusioni cliniche/allergie ──
    excl = set(options.get("exclude_foods") or [])

    def _filt(cat, fallback):
        """Filtra una categoria rimuovendo alimenti esclusi, con fallback."""
        keep = [x for x in cat if x not in excl]
        return keep or [fallback]

    proteins = _filt(_PROTEINS, "petto di pollo")
    carbs = _filt(_CARBs, "riso basmati")
    vegs = _filt(_VEG, "zucchine")
    fats = _filt(_FATS, "olio extravergine d'oliva")
    fruits = _filt(_FRUIT, "banana")

    # ── filtro istamina (MCAS / intolleranza istamina) ──
    proteins = _filter_high_histamine(proteins, conditions)
    carbs = _filter_high_histamine(carbs, conditions)
    vegs = _filter_high_histamine(vegs, conditions)
    fats = _filter_high_histamine(fats, conditions)
    fruits = _filter_high_histamine(fruits, conditions)

    # ── filtro fase dietetica ──
    if phase:
        proteins = _filter_by_phase(proteins, conditions, phase)
        carbs = _filter_by_phase(carbs, conditions, phase)
        vegs = _filter_by_phase(vegs, conditions, phase)
        fats = _filter_by_phase(fats, conditions, phase)
        fruits = _filter_by_phase(fruits, conditions, phase)

    # ── garantisce liste non vuote dopo tutti i filtri ──
    proteins = proteins or ["petto di pollo"]
    carbs = carbs or ["riso basmati"]
    vegs = vegs or ["zucchine"]
    fats = fats or ["olio extravergine d'oliva"]
    fruits = fruits or ["banana"]

    rnd = _random.Random(42)
    week = []

    # ── FODMAP tracking ──
    fodmap_per_day_all = {}
    fodmap_per_meal_all = {}
    high_fodmap_warnings = []

    # ── meal times ──
    meal_names = [m[0] for m in meals]
    meal_times = {}
    if min_hours > 0:
        try:
            start = datetime.strptime(breakfast_time, "%H:%M")
        except (ValueError, TypeError):
            start = datetime.strptime("08:00", "%H:%M")
        for i, mname in enumerate(meal_names):
            t_meal = start + timedelta(hours=min_hours * i)
            meal_times[mname] = t_meal.strftime("%H:%M")

    # ── crononutrition tips ──
    chrononutrition_tips = []
    for c in conditions:
        tips = CHRONONUTRITION_TIPS.get(c, [])
        chrononutrition_tips.extend(tips)
    # deduplica mantenendo ordine
    seen_tips = set()
    unique_tips = []
    for tip in chrononutrition_tips:
        if tip not in seen_tips:
            seen_tips.add(tip)
            unique_tips.append(tip)
    chrononutrition_tips = unique_tips

    # ── conflitti multi-condizione ──
    condition_conflicts = []
    if _clin and len(conditions) >= 2:
        try:
            condition_conflicts = _clin.get_condition_conflicts(conditions)
        except (AttributeError, TypeError):
            condition_conflicts = []

    # ── genera ogni giorno ──
    for idx, d in enumerate(days):
        # target specifici della fase (CKD/carb cycling/keto applicano pattern reali)
        day_t = _phase_targets(options.get("preset", ""), targets, idx, len(days))
        day_meals = []
        day_items_all = []
        day_fodmap = 0.0

        for meal, share in meals:
            # seleziona alimenti con sostituzioni cliniche
            protein = rnd.choice(proteins)
            # nei giorni cheto (keto / CKD fase keto) i carb sono praticamente nulli:
            # ometti del tutto carb e frutta. Nei giorni "basso carb" (carb cycling)
            # i carb restano ma con grammature ridotte (gestite dai target di fase).
            very_low_carb = day_t["c"] < 30
            carb = rnd.choice(carbs) if not very_low_carb else None
            veg = rnd.choice(vegs)
            fat = rnd.choice(fats)
            # la frutta porta carb: solo nei giorni non cheto
            fruit = rnd.choice(fruits) if (meal in ("colazione", "spuntino", "spuntino2", "merenda", "spuntino3") and not very_low_carb) else None

            # applica sostituzioni per condizione
            protein = _apply_substitution(protein, conditions)
            if carb:
                carb = _apply_substitution(carb, conditions)
            veg = _apply_substitution(veg, conditions)
            fat = _apply_substitution(fat, conditions)
            if fruit:
                fruit = _apply_substitution(fruit, conditions)

            # ── pool di alternative per categoria (stile Dietowin: 'o alternativa') ──
            alts = {
                "protein": proteins, "carb": carbs, "veg": vegs,
                "fat": fats, "fruit": fruits,
            }

            tot, items = _meal_combo(protein, carb, veg, fat, fruit,
                                     day_t["kcal"] * share, day_t["p"] * share,
                                     alts=alts, t_carb=day_t["c"] * share)

            # ── calcolo FODMAP per pasto ──
            meal_fodmap = _compute_meal_fodmap(items)
            fodmap_per_meal_all.setdefault(d, {})[meal] = meal_fodmap
            day_fodmap += meal_fodmap

            # ── warning FODMAP ──
            if conditions and set(conditions) & {"ibs", "sibo"}:
                if meal_fodmap > _FODMAP_MEAL_THRESHOLD:
                    high_fodmap_warnings.append(
                        f"{d}/{meal}: FODMAP {meal_fodmap:.2f}g > soglia {_FODMAP_MEAL_THRESHOLD}g"
                    )

            day_meals.append({"meal": meal, "items": items, "totals": tot})
            day_items_all.extend(items)

        # ── FODMAP giornaliero ──
        fodmap_per_day_all[d] = round(day_fodmap, 3)
        if conditions and set(conditions) & {"ibs", "sibo"}:
            if day_fodmap > fodmap_threshold:
                high_fodmap_warnings.append(
                    f"{d}: FODMAP totale {day_fodmap:.2f}g > soglia giornaliera {fodmap_threshold}g"
                )

        week.append({
            "day": d,
            "meals": day_meals,
            "totals": aggregate([compute_entry(i["food"], i["g"]) for i in day_items_all]),
        })

    week_tot = aggregate([d["totals"] for d in week]) if week else _empty()

    return {
        "days": week,
        "week_totals": week_tot,
        # FODMAP tracking
        "fodmap_per_day": fodmap_per_day_all,
        "fodmap_per_meal": fodmap_per_meal_all,
        "high_fodmap_warnings": high_fodmap_warnings,
        # meal timing
        "meal_times": meal_times,
        # chrononutrition
        "chrononutrition_tips": chrononutrition_tips,
        # conflitti multi-condizione
        "condition_conflicts": condition_conflicts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DIARIO (VISTA del motore)
# ─────────────────────────────────────────────────────────────────────────────

def diary_totals(cid, day=None):
    """Aggrega le voci del diario del cliente (VISTA del motore).

    Ritorna dict nutrienti + flags clinici (FODMAP, istamina, ossalati).
    """
    items = db.list_diet_items(cid, day)
    custom = {c["name"]: c["per_100g"] for c in db.list_custom_foods()}
    entries = []
    for it in items:
        c = custom.get(it["food"]) if it.get("custom") else None
        entries.append(compute_entry(it["food"], it["grams"], c))
    tot = aggregate(entries)

    # ── flags clinici per le voci del diario ──
    total_fodmap = 0.0
    histamine_flags = {}
    oxalate_flags = {}
    for it in items:
        fname = it["food"]
        grams = float(it.get("grams", 0))
        # FODMAP: somma componenti dal dict
        fp = ndb.food_fodmap(fname)
        meal_fod = sum(fp.values()) if isinstance(fp, dict) else float(fp or 0)
        total_fodmap += meal_fod * grams / 100.0
        # istamina
        hl = ndb.food_histamine_level(fname)
        if hl in ("high", "medium"):
            histamine_flags[fname] = hl
        # ossalati
        ol = ndb.food_oxalate_level(fname)
        if ol in ("high", "medium"):
            oxalate_flags[fname] = ol

    tot["fodmap_g"] = round(total_fodmap, 3)
    tot["histamine_flags"] = histamine_flags
    tot["oxalate_flags"] = oxalate_flags
    return tot


def diary_full(cid, day=None):
    """Voci + totale, per la UI del diario.

    Include flags clinici (FODMAP, istamina, ossalati) per ogni voce.
    """
    items = db.list_diet_items(cid, day)
    custom = {c["name"]: c["per_100g"] for c in db.list_custom_foods()}
    out = []
    total_fodmap = 0.0
    histamine_flags = {}
    oxalate_flags = {}
    for it in items:
        c = custom.get(it["food"]) if it.get("custom") else None
        e = compute_entry(it["food"], it["grams"], c)
        e["id"] = it["id"]; e["day"] = it["day"]; e["meal"] = it["meal"]; e["grams"] = it["grams"]

        # ── flags clinici per ogni voce ──
        fname = it["food"]
        grams = float(it.get("grams", 0))
        fp = ndb.food_fodmap(fname)
        meal_fod = sum(fp.values()) if isinstance(fp, dict) else float(fp or 0)
        total_fodmap += meal_fod * grams / 100.0
        e["fodmap_g"] = round(meal_fod * grams / 100.0, 3)
        e["fodmap_breakdown"] = fp if isinstance(fp, dict) else {}
        hl = ndb.food_histamine_level(fname)
        e["histamine_level"] = hl
        if hl in ("high", "medium"):
            histamine_flags[fname] = hl
        ol = ndb.food_oxalate_level(fname)
        e["oxalate_level"] = ol
        if ol in ("high", "medium"):
            oxalate_flags[fname] = ol

        out.append(e)

    totals = aggregate(out)
    totals["fodmap_g"] = round(total_fodmap, 3)
    totals["histamine_flags"] = histamine_flags
    totals["oxalate_flags"] = oxalate_flags
    return {"items": out, "totals": totals}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN (demo / test rapido)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    plan = generate_plan({"kcal": 2000, "p": 150, "c": 200, "f": 67})
    print("Giorni:", len(plan["days"]))
    g0 = plan["days"][0]
    print("Giorno", g0["day"], "kcal:", g0["totals"]["kcal"])
    for m in g0["meals"]:
        print("  ", m["meal"], "->", m["totals"]["kcal"], "kcal")

    # demo: piano IBS con FODMAP tracking
    plan_ibs = generate_plan(
        {"kcal": 2000, "p": 150, "c": 200, "f": 67},
        {"conditions": ["ibs"], "phase": "elimination",
         "min_hours_between_meals": 2, "breakfast_time": "08:00"},
    )
    print("\n--- Piano IBS (eliminazione) ---")
    print("FODMAP giornaliero:", plan_ibs["fodmap_per_day"])
    print("Warnings FODMAP:", plan_ibs["high_fodmap_warnings"])
    print("Orari pasti:", plan_ibs["meal_times"])
    print("Tips crononutrizione:", plan_ibs["chrononutrition_tips"])
    if plan_ibs["condition_conflicts"]:
        print("Conflitti:", plan_ibs["condition_conflicts"])
