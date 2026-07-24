"""Test NutriCoach — parser dieta (gruppi alternativa), BIA, motore nutrizione."""

import os
import tempfile
import shutil
import diet_parser
import bia_parser
import nutrition_engine
import nutrition_db
import db
import meal_planner

DESKTOP = r"C:\Users\Siviglino\Desktop"
DIET_PDF = os.path.join(DESKTOP, "Filippo estate.pdf")
BIA_PDF = os.path.join(DESKTOP, "Report utente - F.Q. - 18-06-2026.pdf")


def test_diet_parser_groups():
    res = diet_parser.parse_diet_pdf(DIET_PDF)
    assert not res["scanned"]
    d = res["diet"]
    assert len(d["days"]) == 7
    day0 = d["days"][0]
    assert day0["day"] == "Lunedì"
    meal0 = day0["meals"][0]
    # struttura a GRUPPI (non items)
    assert "groups" in meal0
    # il gruppo del pane ha 1 base + 3 alternative (OR)
    bread_group = [g for g in meal0["groups"] if any("Pane comune" in o["food"] for o in g["options"])]
    assert bread_group, "gruppo pane presente"
    opts = bread_group[0]["options"]
    assert len(opts) == 4, "1 base + 3 alternative"
    assert sum(1 for o in opts if o.get("default")) == 1, "una sola base default"
    # tutti i gruppi hanno almeno 1 opzione con grammi
    assert all(any(o["grams"] for o in g["options"]) for g in meal0["groups"])


def test_bia_parser_text():
    fields = bia_parser.parse_bia_text(
        "Peso: 71.4 kg\nMassa Grassa (FM): 14.6 kg\nAngolo di Fase (PhA): 7.4 gradi"
    )["fields"]
    assert fields["peso"] == 71.4
    assert fields["fm"] == 14.6
    assert fields["pha"] == 7.4


def test_bia_parser_scanned_returns_pages():
    res = bia_parser.parse_bia_pdf(BIA_PDF)
    assert res["scanned"] is True
    assert len(res["pages"]) >= 1


def test_nutrition_db_match():
    n = nutrition_db.nutrition_for("Uova di gallina", 100)
    assert n["matched"] and n["kcal"] == 143.0
    n2 = nutrition_db.nutrition_for("Latte di Soia", 200)
    assert n2["matched"] and abs(n2["kcal"] - 86.0) < 1


def test_engine_one_option_per_group():
    """Le alternative sono OR: una sola opzione per gruppo nei conteggi."""
    res = diet_parser.parse_diet_pdf(DIET_PDF)
    comp = nutrition_engine.compute_diet(res["diet"])
    # colazione salata lunedi: 1 base + 3 alt del pane -> NON deve sommarle tutte
    meal0 = comp["days"][0]["meals"][0]
    # il gruppo pane contribuisce con UNA sola opzione (~50g pane comune)
    assert meal0["totals"]["kcal"] < 600, "non sommare tutte le alternative"
    assert comp["week"]["avg_day"]["kcal"] > 0
    assert comp["week"]["avg_day"]["kcal"] < 3000, "realistico (no doppioni alt)"


def test_engine_selection_switches_option():
    res = diet_parser.parse_diet_pdf(DIET_PDF)
    d = res["diet"]
    # trova gruppo pane in colazione salata lunedi
    grp_idx = None
    for gi, g in enumerate(d["days"][0]["meals"][0]["groups"]):
        if any("Pane comune" in o["food"] for o in g["options"]):
            grp_idx = gi
            break
    sel = {"0": {"0": {str(grp_idx): 3}}}  # scegli 4a opzione (cracker 34g)
    comp_base = nutrition_engine.compute_diet(d)
    comp_sel = nutrition_engine.compute_diet(d, sel)
    # il totale del pasto cambia in base all'opzione scelta
    assert comp_base["days"][0]["meals"][0]["totals"] != comp_sel["days"][0]["meals"][0]["totals"]


def test_shopping_uses_active_only():
    res = diet_parser.parse_diet_pdf(DIET_PDF)
    sl = nutrition_engine.build_shopping_list(res["diet"])
    assert len(sl) > 0
    names = [s["food"] for s in sl]
    assert len(names) == len(set(names)), "niente duplicati in spesa"
    # il pane comune appare (base), ma NON le 3 alternative come voci separate
    assert "pane comune" in names
    assert "cracker di segale" not in names, "l'alternativa non scelta non e' in spesa"


def test_nutrition_db_extended():
    """DB esteso (>=150 alimenti) con valori corretti."""
    import nutrition_db as ndb
    assert len(ndb.FOODS) >= 150
    n = ndb.nutrition_for("uova di gallina", 100)
    assert n["matched"] and abs(n["kcal"] - 143) < 1
    n2 = ndb.nutrition_for("pane di segale", 100)
    assert n2["matched"] and abs(n2["kcal"] - 240) < 1
    assert ndb.nutrition_for("uova", 100)["matched"]
    assert ndb.nutrition_for("zucchine", 100)["matched"]


def test_anthropometry_calculations():
    import anthropometry as ant
    prof = {"sex": "M", "age": 35, "height_cm": 180, "activity": "intenso", "athlete": True}
    meas = {"weight_kg": 75, "waist_cm": 84, "hip_cm": 98,
            "skinfolds": {"tricipite": 10, "bicipite": 8, "sottoscapolare": 12, "sovrailiaca": 14}}
    r = ant.compute_all(prof, meas)
    assert r["bmi"] == 23.1
    assert r["bmr"] == 1705
    assert r["tdee"] == 2941
    assert r["fat_pct"] == 24.4
    assert r["whr"] == 0.86
    assert r["whr_risk"] == "Rischio normale"
    assert r["ffmi"] == 17.5
    assert r["protein_g"] == 120.0


def test_db_profile_and_measurement_and_anthropometry():
    import db, tempfile, os
    tmp = tempfile.mkdtemp(prefix="hermes-test-")
    db.DB_PATH = os.path.join(tmp, "t.db")
    cid = db.add_client("Antro Test", sex="M", age=35, height_cm=180, activity="intenso", athlete=1)
    db.add_measurement(cid, "2026-07-20", weight_kg=75, waist_cm=84, hip_cm=98,
                       skinfold_triceps=10, skinfold_biceps=8, skinfold_subscapular=12, skinfold_suprailiac=14)
    r = db.compute_anthropometry(cid)
    assert r["bmi"] == 23.1
    assert r["tdee"] == 2941
    assert r["fat_pct"] == 24.4
    db.update_client(cid, allergies="lattosio", goal="cut")
    c = db.get_client(cid)
    assert c["allergies"] == "lattosio"


def test_charts_svg():
    import charts
    svg = charts.line_chart([75, 74, 73], title="Peso")
    assert svg.startswith("<svg")
    assert "73" in svg  # mostra l'ultimo valore (trend)
    block = charts.trend_block([75, 74], [20, 21], [7.0, 7.2])
    assert block.count("<svg") >= 1


def test_pdf_export_builds_valid():
    import db, pdf_export, tempfile, os
    d = tempfile.mkdtemp(prefix="hermes-pdf-")
    db.DB_PATH = os.path.join(d, "t.db")
    cid = db.add_client("PDF Test", sex="M", age=30, height_cm=175, activity="moderato")
    db.add_measurement(cid, "2026-07-20", weight_kg=70, waist_cm=80, hip_cm=95,
                       skinfold_triceps=12, skinfold_biceps=10, skinfold_subscapular=14, skinfold_suprailiac=16)
    db.add_bia(cid, "2026-07-20", {"peso": 70, "bodyFat": 18.0, "pha": 7.1, "hydration": 60})
    out = os.path.join(d, "report.pdf")
    pdf_export.build_report_pdf(cid, None, {}, out)
    assert open(out, "rb").read(4) == b"%PDF"


def test_reminders_crud():
    import db, tempfile, os
    d = tempfile.mkdtemp(prefix="hermes-rem-")
    db.DB_PATH = os.path.join(d, "t.db")
    cid = db.add_client("Rem Test", sex="M")
    rid = db.add_reminder(cid, "Controllo peso", due_date="2026-08-01", channel="whatsapp")
    rs = db.list_reminders(cid)
    assert len(rs) == 1 and rs[0]["title"] == "Controllo peso"
    assert rs[0]["channel"] == "whatsapp"
    db.set_reminder_done(rid, 1)
    assert db.list_reminders(cid) == []  # solo aperti
    db.set_reminder_done(rid, 0)
    assert len(db.list_reminders(cid)) == 1
    db.delete_reminder(rid)
    assert db.list_reminders(cid) == []


def test_compare_clients():
    import db, tempfile, os
    d = tempfile.mkdtemp(prefix="hermes-cmp-")
    db.DB_PATH = os.path.join(d, "t.db")
    c1 = db.add_client("A", sex="M", age=40, height_cm=175, activity="moderato")
    c2 = db.add_client("B", sex="M", age=28, height_cm=182, activity="intenso", athlete=1)
    db.add_measurement(c1, "2026-07-20", weight_kg=90, waist_cm=100, hip_cm=105,
                       skinfold_triceps=18, skinfold_biceps=14, skinfold_subscapular=22, skinfold_suprailiac=24)
    db.add_measurement(c2, "2026-07-20", weight_kg=75, waist_cm=84, hip_cm=98,
                       skinfold_triceps=10, skinfold_biceps=8, skinfold_subscapular=12, skinfold_suprailiac=14)
    out = db.compare_clients([c1, c2])
    assert len(out) == 2
    byname = {c["name"]: c for c in out}
    assert byname["A"]["bmi"] == 29.4
    assert byname["A"]["fat_pct"] == 33.3
    assert byname["B"]["fat_pct"] == 24.4
    assert byname["B"]["tdee"] == 3022


def test_auth_flow():
    import db, auth, tempfile, os
    d = tempfile.mkdtemp(prefix="hermes-auth-")
    db.DB_PATH = os.path.join(d, "t.db")
    assert auth.has_account() is False
    auth.set_account("nutri", "segreta123")
    assert auth.has_account() is True
    assert auth.verify_password("nutri", "segreta123") is True
    assert auth.verify_password("nutri", "errata") is False
    assert auth.verify_password("altro", "segreta123") is False
    # cambio
    auth.set_account("nutri", "nuova456")
    assert auth.verify_password("nutri", "nuova456") is True
    assert auth.verify_password("nutri", "segreta123") is False


def test_notifications_engine():
    import db, notifications, tempfile, os
    from datetime import date, timedelta
    d = tempfile.mkdtemp(prefix="hermes-notif-")
    db.DB_PATH = os.path.join(d, "t.db")
    cid = db.add_client("Notif Test", sex="M")
    # pref: riscontro settimanale + report mensile
    db.set_notification_prefs(cid, [
        {"type": "riscontro", "enabled": True, "channel": "whatsapp", "freq": "weekly"},
        {"type": "report", "enabled": True, "channel": "email", "freq": "monthly"},
    ])
    # generate_now -> 2 dovute (mai inviate)
    ids = notifications.generate_due(cid, db)
    assert len(ids) == 2, ids
    pend = db.list_notifications(cid, "pending")
    assert len(pend) == 2
    # re-generate non duplica
    ids2 = notifications.generate_due(cid, db)
    assert ids2 == []
    # mark inviato una
    db.set_notification_sent(pend[0]["id"], True)
    assert len(db.list_notifications(cid, "pending")) == 1
    # get prefs arricchito con label
    prefs = db.get_notification_prefs(cid)
    assert any(p["type"] == "riscontro" and p["enabled"] for p in prefs)
    # messaggio cliente corretto
    msg = notifications.build_message("riscontro", "Mario")
    assert "Mario" in msg


def test_bia_parser_robust():
    """Il parser BIA deve riconoscere decimali, parentesi, 2 colonne, virgola."""
    import bia_parser
    txt = ("Peso (kg) (75.2)\n"
           "Massa Grassa (%) 18.3\n"
           "Massa Magra (FFM) 56.9 kg\n"
           "Phase Angle (deg) 6.8\n"
           "BMI (kg/m2) 24.1\n"
           "TBW 54.1 %")
    f = bia_parser.parse_bia_text(txt)["fields"]
    assert f.get("peso") == 75.2
    assert f.get("fm") == 18.3
    assert f.get("ffm") == 56.9
    assert f.get("pha") == 6.8
    assert f.get("bmi") == 24.1
    assert f.get("tbw") == 54.1
    # blocco su un'unica riga (copia da PDF a 2 colonne)
    onerow = "Peso 75.2 kg Massa Grassa 18.3 % Massa Magra 56.9 kg Angolo di Fase 6.8 BMI 24.1"
    f2 = bia_parser.parse_bia_text(onerow)["fields"]
    assert f2.get("peso") == 75.2 and f2.get("pha") == 6.8 and f2.get("bmi") == 24.1
    # virgola decimale (Tanita italiano)
    virg = "Peso: 75,2 kg\nMassa grassa: 18,3 %\nAngolo di fase: 6,8°"
    f3 = bia_parser.parse_bia_text(virg)["fields"]
    assert f3.get("peso") == 75.2 and f3.get("fm") == 18.3 and f3.get("pha") == 6.8


def test_nutrition_micros_and_search():
    """Micronutrienti e ricerca alimenti (competitor parity: Cronometer/MFP)."""
    import nutrition_db as ndb
    n = ndb.nutrition_for("uova gallina", 100)
    assert n["matched"] is True
    assert n["ca"] > 0 and n["fe"] > 0  # calcio e ferro presenti
    # ricerca
    hits = ndb.search_foods("pollo")
    assert any("pollo" in h for h in hits)
    assert ndb.search_foods("") == []


def test_meal_planner_engine():
    """Il motore unico aggrega macro+micro e genera il piano dai target."""
    import db, meal_planner
    tmp = tempfile.mkdtemp(prefix="hermes-mp-")
    db.DB_PATH = os.path.join(tmp, "t.db")
    # aggregazione diario
    cid = db.add_client("MP", sex="M")
    db.add_diet_item(cid, "lun", "colazione", "uova gallina", 150)
    db.add_diet_item(cid, "lun", "colazione", "pane comune", 60)
    tot = meal_planner.diary_totals(cid, "lun")
    assert tot["kcal"] > 0 and tot["p"] > 0 and tot["ca"] > 0
    # generazione piano da target
    plan = meal_planner.generate_plan({"kcal": 2000, "p": 150, "c": 200, "f": 67})
    assert len(plan["days"]) == 7
    for d in plan["days"]:
        assert len(d["meals"]) == 5
        for m in d["meals"]:
            assert m["totals"]["kcal"] > 0
    shutil.rmtree(tmp, ignore_errors=True)
