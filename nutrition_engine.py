"""NutriCoach — Motore nutrizione.

Prende la dieta parsata (diet_parser) e:
1. Calcola i conteggi nutrizionali (kcal/proteine/carb/grassi/fibre) per
   ogni opzione scelta (via nutrition_db), pasto, giorno e settimana.
2. Gestisce le ALTERNATIVE come gruppi mutuamente esclusivi: ogni gruppo ha
   N opzioni (base + alternative "o ..."). Il conteggio usa UNA sola opzione
   per gruppo (default la base, o quella selezionata dal nutrizionista).
   Questo rispecchia il PDF reale: "Pane comune 50g o Pane di segale 62g"
   = scegli UNO, NON li sommare tutti.
3. Genera la LISTA DELLA SPESA aggregando le grammature della selezione attiva.
4. Produce un riepilogo settimanale (medie, totali).

Tutto è una vista deterministica dei numeri di nutrition_db (single source of
truth), così pianificatore, spesa e riepilogo NON divergono mai.
"""

from nutrition_db import nutrition_for


def _resolve_option(opt):
    food = opt["food"]
    grams = opt.get("grams") or 0
    nut = nutrition_for(food, grams)
    return {
        "food": nut["food"] if nut["matched"] else food,
        "matched": nut["matched"],
        "grams": grams,
        "kcal": nut["kcal"], "p": nut["p"], "c": nut["c"], "f": nut["f"], "fib": nut["fib"],
    }


def _active_option(group, sel_opt_index=None):
    """Ritorna l'opzione da conteggiare per un gruppo.

    sel_opt_index: indice dell'opzione scelta (dal nutrizionista). Se None o
    fuori range, usa la BASE (quella con default=True, altrimenti la prima).
    """
    opts = group["options"]
    if sel_opt_index is not None and 0 <= sel_opt_index < len(opts):
        return opts[sel_opt_index]
    for o in opts:
        if o.get("default"):
            return o
    return opts[0]


def compute_diet(diet, selections=None):
    """Calcola conteggi settimanali. selections = {
        day_index: { meal_index: { group_index: option_index } }
    } per forzare l'alternativa scelta. Se assente, usa la base di ogni gruppo.
    """
    selections = selections or {}
    out_days = []
    for di, day in enumerate(diet.get("days", [])):
        day_meals = []
        day_tot = {"kcal": 0, "p": 0, "c": 0, "f": 0, "fib": 0}
        for mi, meal in enumerate(day["meals"]):
            meal_groups = []
            meal_tot = {"kcal": 0, "p": 0, "c": 0, "f": 0, "fib": 0}
            sel_meal = (selections.get(str(di), {}) or {}).get(str(mi), {}) if selections else {}
            for gi, group in enumerate(meal["groups"]):
                sel_opt = sel_meal.get(str(gi))
                active = _active_option(group, sel_opt)
                resolved = _resolve_option(active)
                for k in ("kcal", "p", "c", "f", "fib"):
                    meal_tot[k] += resolved[k]
                    day_tot[k] += resolved[k]
                # mantiene tutte le opzioni per la UI, ma marca quella attiva
                opts_out = []
                for oi, o in enumerate(group["options"]):
                    r = _resolve_option(o)
                    r["active"] = (o is active)
                    opts_out.append(r)
                meal_groups.append({"options": opts_out, "totals": _round(meal_tot)})
            day_meals.append({"meal": meal["meal"], "groups": meal_groups, "totals": _round(meal_tot)})
        out_days.append({"day": day["day"], "meals": day_meals, "totals": _round(day_tot)})
    week = _week_totals(out_days)
    return {"days": out_days, "week": week}


def _round(d):
    return {k: round(v, 1) for k, v in d.items()}


def _week_totals(days):
    tot = {"kcal": 0, "p": 0, "c": 0, "f": 0, "fib": 0}
    n = 0
    for d in days:
        for k in tot:
            tot[k] += d["totals"][k]
        n += 1
    avg = {k: round(v / n, 1) if n else 0 for k, v in tot.items()}
    return {"total": _round(tot), "avg_day": avg, "days": n}


def build_shopping_list(diet, selections=None):
    """Aggrega grammature per alimento su tutta la settimana.

    Somma SOLO l'opzione attiva di ogni gruppo (non tutte le alternative),
    così la spesa riflette il piano effettivo.
    """
    computed = compute_diet(diet, selections)
    agg = {}
    for day in computed["days"]:
        for meal in day["meals"]:
            for grp in meal["groups"]:
                for o in grp["options"]:
                    if not o.get("active"):
                        continue
                    name = o["food"]
                    g = o["grams"] or 0
                    if name not in agg:
                        agg[name] = {"grams": 0, "matched": o["matched"]}
                    agg[name]["grams"] += g
    # ordina per grammi decrescenti
    items = [{"food": k, "grams": round(v["grams"], 1), "matched": v["matched"]}
             for k, v in agg.items() if v["grams"] > 0]
    items.sort(key=lambda x: x["grams"], reverse=True)
    return items


def weekly_summary(diet, selections=None, client=None, bia=None):
    """Riepilogo esportabile: dati cliente, BIA, conteggi settimanali."""
    computed = compute_diet(diet, selections)
    return {
        "client": client,
        "bia": bia,
        "week": computed["week"],
        "days": computed["days"],
    }


if __name__ == "__main__":
    import diet_parser as dp, json
    res = dp.parse_diet_pdf(r"C:\Users\Siviglino\Desktop\Filippo estate.pdf")
    diet = res["diet"]
    comp = compute_diet(diet)
    print("Settimana — kcal totali:", comp["week"]["total"]["kcal"],
          "| media/giorno:", comp["week"]["avg_day"]["kcal"])
    print("Lunedì colazione:", comp["days"][0]["meals"][0]["meal"],
          "kcal:", comp["days"][0]["meals"][0]["totals"]["kcal"])
    sl = build_shopping_list(diet)
    print("\nLista spesa (top 8):")
    for s in sl[:8]:
        print(f"  {s['food']}: {s['grams']} g")
