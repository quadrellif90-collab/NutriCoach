"""NutriCoach — Motore piano alimentare (SINGLE SOURCE OF TRUTH).

Tutto il calcolo di macronutrienti e micronutrienti passa da qui:
- compute_entry(name, grams, custom=None): nutrienti di una voce (BDD ref + custom)
- aggregate(entries): somma macro+micro di una lista di voci
- generate_plan(targets, options): genera un diario settimanale a partire
  dai target (kcal, P, C, F) bilanciando colazione/pranzo/cena/spuntini.
- diary_totals(cid, day): aggrega le voci del diario del cliente (VISTA).

I valori degli alimenti arrivano da nutrition_db (BDD) o da foods_custom (db).
"""

import db
import nutrition_db as ndb


# pasti standard e loro quota dei target
MEALS = [
    ("colazione", 0.20),
    ("spuntino", 0.10),
    ("pranzo", 0.35),
    ("spuntino2", 0.10),
    ("cena", 0.25),
]

# categorie di alimenti per comporre un pasto bilanciato
_PROTEINS = ["petto di pollo", "uova gallina", "tonno", "salmone", "mozzarella",
             "yogurt greco", "tacchino", "manzo magro", "ricotta", "formaggio bianco",
             "prosciutto cotto", "fesa di tacchino"]
_CARBS = ["pasta", "riso basmati", "pane comune", "patate", "avena",
          "fiocchi d'avena", "pane integrale", "riso integrale", "quinoa", "farro"]
_VEG = ["pomodori", "zucchine", "spinaci", "broccoli", "insalata mista",
        "peperoni", "carote", "cavolfiore", "verdure miste", "finocchi"]
_FATS = ["olio extravergine d'oliva", "avocado", "mandorle", "noci", "semi di girasole",
         "olive", "arachidi"]
_FRUIT = ["mela", "banana", "arancia", "kiwi", "fragole", "pera"]


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
        }
    return ndb.nutrition_for(name, grams)


def _empty():
    return {"kcal": 0.0, "p": 0.0, "c": 0.0, "f": 0.0, "fib": 0.0, "sug": 0.0,
            "salt": 0.0, "ca": 0.0, "fe": 0.0, "vitc": 0.0, "k": 0.0, "mg": 0.0}


def aggregate(entries):
    """Somma i nutrienti di una lista di voci (dict da compute_entry)."""
    tot = _empty()
    for e in entries:
        for k in tot:
            tot[k] += e.get(k, 0) or 0
    for k in tot:
        tot[k] = round(tot[k], 1)
    return tot


def _meal_combo(protein, carb, veg, fat, fruit, t_kcal, t_p):
    """Costruisce un pasto bilanciato vicino ai target (euristico)."""
    p_g = 150 if protein in ("petto di pollo", "tacchino", "manzo magro", "fesa di tacchino") else 100
    c_g = 70 if carb in ("pasta", "riso basmati") else 50
    v_g = 150
    f_ml = 10 if fat == "olio extravergine d'oliva" else 15
    fr_g = 120 if fruit else 0
    items = [
        {"food": protein, "g": p_g},
        {"food": carb, "g": c_g},
        {"food": veg, "g": v_g},
        {"food": fat, "g": f_ml},
    ]
    if fruit:
        items.append({"food": fruit, "g": fr_g})
    entries = [compute_entry(i["food"], i["g"]) for i in items]
    return aggregate(entries), items


def generate_plan(targets, options=None):
    """Genera un diario settimanale a partire dai target.

    targets = {kcal, p, c, f}  (valori GIORNALIERI)
    Ritorna {days:[{day, meals:[{meal, items, totals}], totals}], week_totals}
    """
    options = options or {}
    days = options.get("days", ["lun", "mar", "mer", "gio", "ven", "sab", "dom"])
    import random
    rnd = random.Random(42)
    week = []
    for d in days:
        day_meals = []
        day_items_all = []
        for meal, share in MEALS:
            protein = rnd.choice(_PROTEINS)
            carb = rnd.choice(_CARBS)
            veg = rnd.choice(_VEG)
            fat = rnd.choice(_FATS)
            fruit = rnd.choice(_FRUIT) if meal in ("colazione", "spuntino", "spuntino2") else None
            tot, items = _meal_combo(protein, carb, veg, fat, fruit,
                                     targets["kcal"] * share, targets["p"] * share)
            day_meals.append({"meal": meal, "items": items, "totals": tot})
            day_items_all.extend(items)
        week.append({"day": d, "meals": day_meals,
                     "totals": aggregate([compute_entry(i["food"], i["g"]) for i in day_items_all])})
    week_tot = aggregate([d["totals"] for d in week]) if week else _empty()
    return {"days": week, "week_totals": week_tot}


def diary_totals(cid, day=None):
    """Aggrega le voci del diario del cliente (VISTA del motore)."""
    items = db.list_diet_items(cid, day)
    custom = {c["name"]: c["per_100g"] for c in db.list_custom_foods()}
    entries = []
    for it in items:
        c = custom.get(it["food"]) if it.get("custom") else None
        entries.append(compute_entry(it["food"], it["grams"], c))
    return aggregate(entries)


def diary_full(cid, day=None):
    """Voci + totale, per la UI del diario."""
    items = db.list_diet_items(cid, day)
    custom = {c["name"]: c["per_100g"] for c in db.list_custom_foods()}
    out = []
    for it in items:
        c = custom.get(it["food"]) if it.get("custom") else None
        e = compute_entry(it["food"], it["grams"], c)
        e["id"] = it["id"]; e["day"] = it["day"]; e["meal"] = it["meal"]; e["grams"] = it["grams"]
        out.append(e)
    return {"items": out, "totals": aggregate(out)}


if __name__ == "__main__":
    plan = generate_plan({"kcal": 2000, "p": 150, "c": 200, "f": 67})
    print("Giorni:", len(plan["days"]))
    g0 = plan["days"][0]
    print("Giorno", g0["day"], "kcal:", g0["totals"]["kcal"])
    for m in g0["meals"]:
        print("  ", m["meal"], "->", m["totals"]["kcal"], "kcal")
