"""
NutriCoach — Clinical Nutrition Reference Module

Modulo di riferimento per condizioni cliniche e strategie dietetiche
evidence-based. Ogni condizione include: descrizione, evidenza, strategie
alimentari, alimenti da evitare, alimenti consigliati, fonti.

Le raccomandazioni vengono applicate in base all'anamnesi del cliente
(campi: conditions/health_issues nel profilo).

FONTI PRINCIPALI (2024-2026):
- FODMAP: umbrella review PMC 2025, Cuffe Lancet Gastro 2025, Haghbin JCM 2024
- GERD: PMC 2023 functional foods, systematic review Nutrients 2024
- Allergie: EAACI guidelines 2022, GA2LEN 2022, FDA 2025, Leone PMC 2023
- Celiachia: ESSCD 2025 guidelines, Abdi PMC 2023
- IBS/microbioma: Li PMC 2025, ISAPP Nature 2026, Kezer Frontiers 2025
- Intolleranza lattosio: Mayo Clinic 2024, NIDDK
"""

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONDIZIONI CLINICHE
# Ogni condizione ha: nome, categoria, evidenza, strategie, alimenti, fonti.
# ─────────────────────────────────────────────────────────────────────────────

CLINICAL_CONDITIONS = {

    # ── IBS / FODMAP ──────────────────────────────────────────────────────
    "ibs": {
        "name": "Sindrome dell'Intestino Irritabile (IBS)",
        "category": "gastrointestinal",
        "evidence_level": "alta",
        "description": (
            "Disordine funzionale gastrointestinale caratterizzato da dolore addominale "
            "ricorrente associato a altered bowel habits (diarrea, stitichezza o misto). "
            "Colpisce circa il 10-15% della popolazione adulta."
        ),
        "strategies": [
            {
                "name": "Dieta Low-FODMAP (3 fasi)",
                "phases": [
                    "Fase 1 - Eliminazione (4-8 settimane): ridurre tutti i FODMAP",
                    "Fase 2 - Reinserimento (6-8 settimane): testare singoli gruppi FODMAP",
                    "Fase 3 - Personalizzazione: tolleranza individuale"
                ],
                "efficacy": "55-76% dei pazienti con riduzione sintomi ≥50 punti IBS-SSS",
                "note": "Dieta sotto supervisione dietetica; non mantenuta a lungo termine per rischio carenze"
            },
            {
                "name": "Consigli dietetici tradizionali",
                "description": "Pasti regolari, porzioni ridotte, ridurre caffè/alcol, fibra solubile",
                "efficacy": "~50% dei pazienti miglioramento sintomi",
                "note": "Prima linea prima del low-FODMAP"
            }
        ],
        "foods_avoid_high": [
            "Fruttosio: mele, pere, mango, miele, sciroppo d'agave, cipolla, aglio",
            "Lattosio: latte vaccino, gelato, yogurt (non fermentato)",
            "Fruttani: grano, orzo, segale, cipolla, aglio, cavolfiore",
            "Galattani: legumi (lenticchie, ceci, fagioli)",
            "Polialcoli: sorbitolo, xilitolo, mannitolo (dolcificanti, gomme)"
        ],
        "foods_safe": [
            "Frutti: fragole, kiwi, arance, banane, mirtilli",
            "Verdure: carote, zucchine, melanzane, peperoni, spinaci, patate",
            "Cereali: riso, avena (senza glutine), quinoa, mais",
            "Proteine: carne, pesce, uova, tofu",
            "Latticini: formaggi stagionati (parmesan, cheddar), latticini senza lattosio"
        ],
        "probiotics": (
            "Probiotici con evidenza in IBS: Lactobacillus plantarum 299v, "
            "Bifidobacterium infantis 35624, Saccharomyces boulardii. "
            "Meta-analisi 2024-2025 mostrano miglioramento dolore, gonfiore, abitudini intestinali."
        ),
        "fonti": [
            "Chu P et al. (PMC 2025) - umbrella review low-FODMAP microbiota",
            "Haghbin H et al. (JCM 2024) - network meta-analysis dietary interventions IBS",
            "Khan Z et al. (Cureus 2025) - systematic review + meta-analysis",
            "Zeraattalab-Motlagh S et al. (2025) - umbrella review 8 meta-analyses",
            "Cuffe MS (Lancet Gastro 2025) - efficacy dietary interventions IBS",
            "Lomer MCE (2024) - FODMAP personalization",
            "Li X et al. (PMC 2025) - gut microbiota IBS narrative review"
        ]
    },

    # ── GERD / Reflusso ──────────────────────────────────────────────────
    "gerd": {
        "name": "Malattia da Reflusso Gastroesofageo (GERD)",
        "category": "gastrointestinal",
        "evidence_level": "alta",
        "description": (
            "Condizione cronica in cui il contenuto gastrico refluisce nell'esofago causando "
            "sintomi (bruciore, rigurgito) e potenziali danni alla mucosa. Prevalenza ~13% "
            "globalmente, fino a 25% in alcune regioni."
        ),
        "strategies": [
            {
                "name": "Dieta anti-reflusso",
                "description": (
                    "Pasti piccoli e frequenti, evitare cibi trigger, non sdraiarsi "
                    "dopo i pasti (min 2h), mantenere peso sano"
                ),
                "efficacy": "Miglioramento sintomi documentato in studi prospettici 2024-2025"
            },
            {
                "name": "Dieta Mediterranea",
                "description": (
                    "Elevato apporto di frutta, verdura, cereali integrali, grassi buoni. "
                    "Effetto simile ai PPI in alcuni studi."
                ),
                "efficacy": "Riduzione 33% rischio GERD con alto consumo frutta/verdura"
            }
        ],
        "foods_avoid": [
            "Cibi ad alto contenuto di grassi (fritti, salumi, formaggi grassi)",
            "Cioccolata, menta, caffè (possono rilassare lo sfintere esofageo inferiore)",
            "Bevande gassate, alcolici",
            "Agrumi, pomodori, cipolle, aglio",
            "Cibi piccanti",
            "Pasti abbondanti soprattutto la sera"
        ],
        "foods_safe": [
            "Frutta non acida: banane, mele, pere, meloni",
            "Verdure: carote, broccoli, cetrioli, patate, spinaci",
            "Cereali integrali: avena, riso integrale, pane integrale",
            "Proteine magre: petto di pollo, pesce, uova",
            "Latticini magri: yogurt magro, latte scremato",
            "Acqua alcalina (pH > 8.0) - denatura pepsina"
        ],
        "lifestyle": [
            "Non mangiare 2-3 ore prima di coricarsi",
            "Sollevare la testata del letto (15-20 cm)",
            "Mantenere peso sano",
            "Evitare vestiti stretti alla vita",
            "Masticare gomma senza menta dopo i pasti (aumenta saliva)"
        ],
        "fonti": [
            "PMC 2023 - Functional Food in Relation to GERD (Nutrients 15:3583)",
            "Systematic review Nutrients 2024 - Dietary Interventions GERD",
            "Nutrients 2025 - Natural Products GERD Management",
            "Alqahtani NS (2025) - Dietary Intervention GERD prospective study",
            "Morozov S et al. (WJG 2018) - Fiber-enriched diet GERD"
        ]
    },

    # ── Intolleranza Lattosio ────────────────────────────────────────────
    "lactose_intolerance": {
        "name": "Intolleranza al Lattosio",
        "category": "intolerance",
        "evidence_level": "alta",
        "description": (
            "Mancanza dell'enzima lattasi che digerisce il lattosio (zucchero del latte). "
            "Prevalenza: 65-70% della popolazione mondiale, più alta in Asia/Africa/America Latina."
        ),
        "strategies": [
            {
                "name": "Riduzione/eliminazione lattosio",
                "description": (
                    "Eliminare o ridurre latticini freschi. Formaggi stagionati (parmesan, "
                    "gruyère, cheddar) hanno pochissimo lattosio. Yogurt fermentati sono "
                    "generalmente tollerati."
                )
            },
            {
                "name": "Integratori enzimatici (lattasi)",
                "description": "Assumere lattasi prima di consumare latticini"
            },
            {
                "name": "Sostituti del latte",
                "description": "Latte di soia, avena, mandorla, cocco (verificare integrazione calcio)"
            }
        ],
        "foods_avoid": [
            "Latte vaccino fresco",
            "Gelato",
            "Yogurt non fermentato",
            "Panna, cacao in polvere con latte"
        ],
        "foods_safe": [
            "Formaggi stagionati: parmesan, gruyère, cheddar, emmental",
            "Yogurt fermentati (il batterio digerisce parte del lattosio)",
            "Latte senza lattosio (trattato con lattasi)",
            "Latte di soia, avena, mandorla, cocco (integrati con calcio)",
            "Burro (contiene tracce di lattosio, generalmente tollerato)",
            "Panna acida fermentata"
        ],
        "nutrients_monitor": ["Calcio", "Vitamina D", "Vitamina B12"],
        "fonti": [
            "Mayo Clinic 2024 - Lactose intolerance diagnosis & treatment",
            "NIDDK - Lactose Intolerance (niddk.nih.gov)",
            "Day M et al. (Nursing 2024) - Food intolerances",
            "Hammer HF et al. (UpToDate 2024) - Clinical manifestations"
        ]
    },

    # ── Celiachia ────────────────────────────────────────────────────────
    "celiac": {
        "name": "Celiachia",
        "category": "autoimmune",
        "evidence_level": "alta",
        "description": (
            "Malattia autoimmune scatenata dall'ingestione di glutine nei soggetti "
            "predisposti. Danno della mucosa intestinale con malassorbimento. "
            "Prevalenza ~1% nella popolazione generale."
        ),
        "strategies": [
            {
                "name": "Dieta senza glutine (GFD) - per tutta la vita",
                "description": (
                    "Eliminazione completa di glutine (grano, orzo, segale, avena non certificata). "
                    "Soglia di sicurezza: ≤10 mg glutine/giorno (linee guida ESSCD 2025)."
                ),
                "efficacy": "Unica terapia efficace; guarigione completa in 2-5 anni"
            }
        ],
        "foods_avoid": [
            "Grano, farina di grano, pane/pasta non senza glutine",
            "Orzo, segale, triticale",
            "Avena (solo se certificata senza glutine)",
            "Salse: soia tradizionale, Worcestershire (contengono glutine)",
            "Birra tradizionale, Whisky (orceva filtrata su malto)",
            "Cibi processati con addensanti a base di glutine"
        ],
        "foods_safe": [
            "Riso, mais, quinoa, amaranto, grano saraceno, miglio",
            "Patate, legumi, frutta, verdura",
            "Carne, pesce, uova",
            "Latte, yogurt, formaggi naturali",
            "Farine: riso, mandorla, cocco, granturco",
            "Salsa di soia senza glutine (tamari)",
            "Birra senza glutine"
        ],
        "nutrients_monitor": ["Ferro", "Calcio", "Vitamina D", "Vitamina B12", "Folati", "Zinco"],
        "fonti": [
            "ESSCD 2025 Updated Guidelines (Part 1 & 2)",
            "Abdi F et al. (PMC 2023) - Nutritional Considerations Celiac/NCGS",
            "Wall E (2024) - Celiac Disease Diet Management",
            "FDA 2025 - Gluten-free labeling guidance update"
        ]
    },

    # ── Sensibilità al Glutine non celiaca ───────────────────────────────
    "ncgs": {
        "name": "Sensibilità al Glutine Non Celiaca (NCGS)",
        "category": "intolerance",
        "evidence_level": "media",
        "description": (
            "Sintomi gastrointestinali ed extra-intestinali dopo assunzione di glutine, "
            "senza celiachia né allergia al grano. Diagnosi di esclusione."
        ),
        "strategies": [
            {
                "name": "Riduzione/glutine-free trial",
                "description": (
                    "Eliminare glutine per 4-6 settimane e rivalutare. "
                    "Molti casi sono in realtà sensibilità ai FODMAP (fruttani del grano), "
                    "non al glutine stesso."
                ),
                "note": "L'umbrella review 2025 mostra che i fruttani del grano, non il glutine, causano sintomi nella maggior parte dei casi"
            }
        ],
        "foods_avoid": ["Grano, orzo, segale (stessa celiachia)"],
        "foods_safe": ["Stessi alimenti della celiachia"],
        "fonti": [
            "Catassi C et al. (2015) - Salerno Experts' Criteria NCGS",
            "Caio G et al. (Nutrients 2020) - GFD gut microbiota",
            "Nutrients 2025 - IBS-GERD: fruttani, non glutine"
        ]
    },

    # ── Allergie alimentari IgE-mediate ──────────────────────────────────
    "food_allergy": {
        "name": "Allergie Alimentari (IgE-mediate)",
        "category": "allergy",
        "evidence_level": "alta",
        "description": (
            "Reazione immunitaria IgE-mediata a proteine alimentari. "
            "I 14 allergeni principali EU: latte, uovo, pesce, crostacei, frutta a guscio, "
            "arachidi, soia, grano, sedano, senape, sesamo, lupini, molluschi, biossido di zolfo."
        ),
        "strategies": [
            {
                "name": "Eliminazione completa dell'allergene",
                "description": (
                    "Evitare l'allergene e i prodotti derivati. Leggere sempre le etichette. "
                    "Attenzione a 'può contenere tracce di'. "
                    "La gestione deve essere personalizzata (linee guida EAACI 2022)."
                )
            },
            {
                "name": "Sostituzione nutrizionale",
                "description": (
                    "Compensare le carenze nutrizionali dell'eliminazione "
                    "(es. ferro se si elimina la carne, calcio se si elimina il latte)."
                )
            }
        ],
        "common_allergens": {
            "latte": "Sostituti: latte di soia, avena, riso, mandorla (integrati con calcio+D)",
            "uovo": "Sostituti per cucina: aquafaba, farina di lino, banana schiacciata",
            "grano": "Cereali alternativi: riso, quinoa, mais, amaranto, grano saraceno",
            "arachidi/frutta_guscio": "Sostituti proteici: semi di girasole, zucca, legumi",
            "pesce": "Omega-3 da: semi di lino, chia, olio di alghe (DHA)",
            "soia": "Altre fonti proteiche vegetali: legumi, quinoa, semi"
        },
        "fonti": [
            "EAACI Guidelines IgE-mediated food allergy (Allergy 2022)",
            "GA2LEN Guideline 2022 - Managing food allergy",
            "FDA 2025 - Food Allergies labeling update",
            "Leone L et al. (PMC 2023) - Nutritional management food allergies",
            "Venter C et al. (JACI 2024) - Growth/nutrient deficiencies food allergy"
        ]
    },

    # ── Esofagite Eosinofila ─────────────────────────────────────────────
    "eoe": {
        "name": "Esofagite Eosinofila (EoE)",
        "category": "allergy",
        "evidence_level": "media",
        "description": (
            "Malattia infiammatoria immuno-mediata dell'esofago caratterizzata da "
            "infiltrazione eosinofila. Spesso associata ad altre allergie. ~1/1000 persone."
        ),
        "strategies": [
            {
                "name": "Dieta 4FED (Four Food Elimination Diet)",
                "description": (
                    "Eliminare 4 gruppi: latte vaccino, soia, grano/glutine, uovo. "
                    "Riintroduzione graduale sotto controllo. "
                    "ASCIA Dietary Guide 2023."
                ),
                "efficacy": "Riduzione significativa sintomi e counts eosinofili"
            }
        ],
        "foods_avoid": ["Latte vaccino e derivati", "Soya e derivati", "Grano/glutine", "Uovo"],
        "foods_safe": [
            "Tutti gli altri: carne, pesce, frutta, verdura, riso, mais, legumi",
            "Latte di cocco/avena/riso (integrato con calcio)",
            "Prodotti senza latte, soia, grano, uovo"
        ],
        "fonti": [
            "ASCIA 2023 - Dietary Guide 4FED for EoE",
            "Allergy.org.au - EoE management"
        ]
    },

    # ── Dispepsia Funzionale ─────────────────────────────────────────────
    "dyspepsia": {
        "name": "Dispepsia Funzionale",
        "category": "gastrointestinal",
        "evidence_level": "media",
        "description": (
            "Sintomi epigastrici (pienezza, dolore, nausea) senza patologia organica "
            "identificabile. Spesso associata a IBS."
        ),
        "strategies": [
            {
                "name": "Pasti piccoli e frequenti",
                "description": "Porzioni ridotte, 5-6 pasti/giorno, masticare lentamente"
            },
            {
                "name": "Ridurre cibi che rallentano lo svuotamento gastrico",
                "description": "Evitare grassi ad alto contenuto, cibi molto elaborati"
            }
        ],
        "foods_avoid": ["Cibi grassi/fritti", "Cibi molto elaborati", "Bevande gassate", "Caffè a stomaco vuoto"],
        "foods_safe": ["Cibi leggeri cotti al vapore/griglia", "Verdure cotte", "Riso", "Pesce magro"],
        "fonti": [
            "ScienceDirect 2026 - Dietary interventions functional dyspepsia",
            "Evidence favors small, regular, lower-fat meals"
        ]
    },

    # ── Obesità / Sovrappeso ────────────────────────────────────────────
    "obesity": {
        "name": "Obesità / Sovrappeso",
        "category": "metabolic",
        "evidence_level": "alta",
        "description": (
            "BMI ≥ 30 (obesità) o 25-29.9 (sovrappeso). "
            "Fattori: dieta ipercalorica, sedentarietà, genetica, fattori psicologici."
        ),
        "strategies": [
            {
                "name": "Deficit calorico controllato",
                "description": "Riduzione 300-500 kcal/giorno rispetto al fabbisogno, senza restrizioni eccessive"
            },
            {
                "name": "Dieta mediterranea",
                "description": "Elevato apporto verdura, fibre, grassi buoni, proteine magre"
            }
        ],
        "foods_avoid": ["Bevande zuccherate", "Snack processati", "Cibi fritti", "Alcolici"],
        "foods_safe": ["Verdure (libere)", "Frutta (2-3 porzioni)", "Proteine magre", "Cereali integrali"],
        "fonti": [
            "Linee guida LARN/SINU 2014 (aggiornamento in corso)",
            "2025 Dietary Guidelines Advisory Committee (USDA)"
        ]
    },

    # ── Diabete Tipo 2 ──────────────────────────────────────────────────
    "diabetes_t2": {
        "name": "Diabete di Tipo 2",
        "category": "metabolic",
        "evidence_level": "alta",
        "description": (
            "Insulino-resistenza con iperglicemia. Gestione alimentare cruciale."
        ),
        "strategies": [
            {
                "name": "Controllo glicemico",
                "description": (
                    "Cereali a basso indice glicemico, distribuzione carboidrati nei pasti, "
                    "fibre solubili (avena, legumi), evitare picchi glicemici"
                )
            }
        ],
        "foods_avoid": ["Zuccheri semplici", "Bevande zuccherate", "Raffinati (pane bianco, riso bianco)"],
        "foods_safe": ["Cereali integrali", "Legumi", "Verdure", "Frutta con moderação", "Pesce"],
        "fonti": [
            "ADA Standards of Care 2025",
            "LARN/SINU linee guida italiane"
        ]
    },

    # ── Ipertensione ────────────────────────────────────────────────────
    "hypertension": {
        "name": "Ipertensione Arteriosa",
        "category": "cardiovascular",
        "evidence_level": "alta",
        "description": (
            "PA ≥ 130/80 mmHg. Dieta DASH (Dietary Approaches to Stop Hypertension) efficace."
        ),
        "strategies": [
            {
                "name": "Dieta DASH",
                "description": (
                    "Ridurre sodio (< 2300 mg/giorno, idealmente < 1500 mg), "
                    "aumentare potassio, magnesio, calcio. "
                    "Elevato apporto frutta, verdura, latticini magri, cereali integrali."
                ),
                "efficacy": "Riduzione PA sistolica di 8-14 mmHg"
            }
        ],
        "foods_avoid": ["Sale e cibi salati", "Insaccati", "Cibi in scatola", "Snack processati"],
        "foods_safe": ["Frutta", "Verdura", "Latticini magri", "Cereali integrali", "Pesce", "Noci"],
        "fonti": [
            "AHA 2024 - DASH diet guidelines",
            "LARN/SINU linee guida italiane"
        ]
    },

    # ── Osteoporosi ──────────────────────────────────────────────────────
    "osteoporosis": {
        "name": "Osteoporosi",
        "category": "skeletal",
        "evidence_level": "alta",
        "description": (
            "Riduzione densità minerale ossea con aumentato rischio fratture. "
            "Ruolo cruciale di calcio, vitamina D, proteine."
        ),
        "strategies": [
            {
                "name": "Adeguato apporto di calcio e vitamina D",
                "description": (
                    "Calcio 1000-1200 mg/giorno da alimenti. "
                    "Vitamina D 600-800 UI/giorno. "
                    "Proteine 1.0-1.2 g/kg/giorno."
                )
            }
        ],
        "foods_avoid": ["Bevande gassate (acido fosforico)", "Eccesso di sale", "Caffeina eccessiva"],
        "foods_safe": [
            "Latticini (latte, yogurt, formaggio)", "Sardine con lische", "Broccoli",
            "Frutta secca", "Tofu al calcio", "Farina di mandorle"
        ],
        "nutrients_focus": ["Calcio", "Vitamina D", "Proteine", "Vitamina K", "Magnesio"],
        "fonti": [
            "ESCEO 2023 - Nutritional management osteoporosis",
            "LARN/SINU linee guida italiane"
        ]
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# FUNZIONI DI UTILITÀ
# ─────────────────────────────────────────────────────────────────────────────

def get_all_conditions():
    """Ritorna la lista di tutte le condizioni disponibili."""
    return {k: {"name": v["name"], "category": v["category"], "evidence_level": v["evidence_level"]}
            for k, v in CLINICAL_CONDITIONS.items()}


def get_condition(condition_key):
    """Ritorna i dettagli completi di una condizione."""
    return CLINICAL_CONDITIONS.get(condition_key)


def get_conditions_by_category(category):
    """Filtra condizioni per categoria."""
    return {k: v for k, v in CLINICAL_CONDITIONS.items() if v["category"] == category}


def get_foods_to_avoid(condition_keys):
    """Ritorna un unico elenco di alimenti da evitare per più condizioni."""
    avoid = set()
    for k in condition_keys:
        cond = CLINICAL_CONDITIONS.get(k, {})
        for f in cond.get("foods_avoid", []):
            avoid.add(f)
        for f in cond.get("foods_avoid_high", []):
            avoid.add(f)
    return sorted(avoid)


def get_foods_safe(condition_keys):
    """Ritorna un unico elenco di alimenti sicuri per più condizioni."""
    safe = set()
    for k in condition_keys:
        cond = CLINICAL_CONDITIONS.get(k, {})
        for f in cond.get("foods_safe", []):
            safe.add(f)
    return sorted(safe)


def get_dietary_recommendations(condition_keys):
    """
    Data una lista di condizioni cliniche (dall'anamnesi del cliente),
    ritorna un riassunto delle raccomandazioni dietetiche.
    """
    recommendations = []
    for k in condition_keys:
        cond = CLINICAL_CONDITIONS.get(k)
        if not cond:
            continue
        rec = {
            "condition": cond["name"],
            "strategies": [s["name"] for s in cond.get("strategies", [])],
            "foods_avoid_count": len(cond.get("foods_avoid", [])) + len(cond.get("foods_avoid_high", [])),
            "foods_safe_count": len(cond.get("foods_safe", [])),
            "key_nutrients": cond.get("nutrients_monitor", cond.get("nutrients_focus", [])),
            "probiotics": cond.get("probiotics", ""),
            "fonti": cond.get("fonti", [])[:3]  # prime 3 fonti
        }
        recommendations.append(rec)
    return recommendations


def generate_anamnesis_report(conditions, client_info=None):
    """
    Genera un report completo basato sulle condizioni del cliente.
    Ritorna un dizionario strutturato per il PDF/UI.
    """
    client_info = client_info or {}
    avoid_all = get_foods_to_avoid(conditions)
    safe_all = get_foods_safe(conditions)
    recs = get_dietary_recommendations(conditions)

    return {
        "client_name": client_info.get("name", ""),
        "conditions": conditions,
        "total_conditions": len(conditions),
        "recommendations": recs,
        "foods_avoid": avoid_all,
        "foods_safe": safe_all,
        "combined_strategies": list(set(
            s["name"]
            for c in CLINICAL_CONDITIONS.values()
            if c.get("category") in ["gastrointestinal", "intolerance", "allergy", "autoimmune"]
            for s in c.get("strategies", [])
        )),
        "all_fonti": list(set(
            f
            for k in conditions
            for f in CLINICAL_CONDITIONS.get(k, {}).get("fonti", [])
        ))
    }
