"""NutriCoach — Logica follow-up (VISTA sui check-in salvati).

Analizza i check-in del cliente (peso, compliance, energia) e produce un
consiglio di aggiustamento coerente con l'obiettivo:
- trend peso (kg/settimana) da regressione semplice sulle ultime misure
- compliance media
- suggerimento kcal: se obiettivo 'Dimagrimento' e peso stabile con buona
  compliance -> ridurre ~10%; se perdita troppo rapida (>1%/sett) -> aumentare;
  se obiettivo 'Massa' e peso stabile -> aumentare ~5-10%.

Le soglie seguono le linee guida standard su tassi di variazione sicuri
(0.5-1% peso corporeo/settimana in cut; 0.25-0.5% in bulk).
Non è consulenza medica: è un suggerimento per il nutrizionista.
"""

from datetime import date


def _parse_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def weight_trend(checkins):
    """kg/settimana da regressione lineare su (giorni, peso). None se <2 punti."""
    pts = []
    for c in checkins:
        d = _parse_date(c.get("date"))
        w = c.get("weight_kg")
        if d and w:
            pts.append((d.toordinal(), float(w)))
    if len(pts) < 2:
        return None
    pts.sort()
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den == 0:
        return None
    slope_per_day = sum((p[0] - mx) * (p[1] - my) for p in pts) / den
    return round(slope_per_day * 7, 3)  # kg/settimana


def analyze(checkins, goal="", current_kcal=None):
    """Ritorna {trend_kg_week, compliance_avg, energy_avg, advice, kcal_suggested}."""
    if not checkins:
        return {"trend_kg_week": None, "compliance_avg": None, "energy_avg": None,
                "advice": "Nessun check-in registrato: chiedi al cliente peso e compliance.",
                "kcal_suggested": current_kcal}
    trend = weight_trend(checkins)
    comps = [float(c["compliance_pct"]) for c in checkins if c.get("compliance_pct") is not None]
    comp_avg = round(sum(comps) / len(comps), 1) if comps else None
    energies = [float(c["energy_level"]) for c in checkins if c.get("energy_level") is not None]
    en_avg = round(sum(energies) / len(energies), 1) if energies else None
    last_w = next((float(c["weight_kg"]) for c in reversed(checkins) if c.get("weight_kg")), None)

    goal_l = (goal or "").lower()
    cutting = any(k in goal_l for k in ("dimagr", "cut", "perdita", "peso"))
    bulking = any(k in goal_l for k in ("massa", "bulk", "aument"))
    adj = 0.0
    advice = []

    if comp_avg is not None and comp_avg < 60:
        advice.append(f"Compliance bassa ({comp_avg}%): prima di toccare le kcal, semplifica il piano o rivedi le preferenze.")
    if trend is None:
        advice.append("Servono almeno 2 pesate per stimare il trend.")
    else:
        pct_week = (trend / last_w * 100) if last_w else None
        if cutting:
            if trend >= -0.1 and (comp_avg is None or comp_avg >= 70):
                adj = -0.10
                advice.append(f"Peso stabile ({trend:+.2f} kg/sett) con buona compliance: riduci le kcal del ~10%.")
            elif pct_week is not None and pct_week < -1.0:
                adj = +0.07
                advice.append(f"Perdita troppo rapida ({pct_week:.1f}%/sett, oltre l'1%): aumenta le kcal del ~5-10% per preservare massa magra.")
            else:
                advice.append(f"Trend in linea ({trend:+.2f} kg/sett): mantieni le kcal attuali.")
        elif bulking:
            if trend <= 0.05:
                adj = +0.07
                advice.append(f"Peso stabile ({trend:+.2f} kg/sett) in fase di massa: aumenta le kcal del ~5-10%.")
            elif pct_week is not None and pct_week > 0.5:
                adj = -0.05
                advice.append(f"Aumento troppo rapido ({pct_week:.1f}%/sett): riduci leggermente le kcal (~5%).")
            else:
                advice.append(f"Trend in linea ({trend:+.2f} kg/sett): mantieni le kcal attuali.")
        else:
            advice.append(f"Trend peso {trend:+.2f} kg/sett. Definisci l'obiettivo del cliente per un consiglio kcal.")
    if en_avg is not None and en_avg <= 3:
        advice.append(f"Energia bassa (media {en_avg}/10): valuta più carboidrati intorno all'attività o un refeed.")

    kcal_suggested = round(current_kcal * (1 + adj)) if current_kcal else None
    return {"trend_kg_week": trend, "compliance_avg": comp_avg, "energy_avg": en_avg,
            "last_weight_kg": last_w, "advice": " ".join(advice),
            "kcal_adjustment_pct": round(adj * 100), "kcal_suggested": kcal_suggested}
