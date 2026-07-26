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
- SIBO: PMC 2025 Nutrients 17:01410, ACG 2020, Cleveland Clinic
- Istamina/MCAS: SIGHI list, MDPI Nutrients 2025, MastCell360 evidence
- Dysbiosis: ISAPP Nature 2026, PMC 2025 precision nutrition
- Calcoli renali: AUA 2024 stones guidelines
"""

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONDIZIONI CLINICHE
# Ogni condizione ha: nome, categoria, evidenza, strategie, alimenti, fonti.
# ─────────────────────────────────────────────────────────────────────────────

import json
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
    },

    # ══════════════════════════════════════════════════════════════════════
    # NUOVE CONDIZIONI CLINICHE (aggiunte)
    # ══════════════════════════════════════════════════════════════════════

    # ── SIBO ──────────────────────────────────────────────────────────────
    "sibo": {
        "name": "Sindrome da Sovraccrescita Batterica Intestinale (SIBO)",
        "category": "gastrointestinal",
        "evidence_level": "alta",
        "description": (
            "Crescita eccessiva di batteri nel tenue (>10^5 CFU/mL). "
            "Presenta tre sottotipi principali: idrogeno (diarrea), metano (stitichezza), "
            "idrogeno-solfuro (misto). Colpisce fino al 50% dei pazienti IBS. "
            "I PPI aumentano il rischio di SIBO."
        ),
        "strategies": [
            {
                "name": "Dieta elementare / low-fermentabile",
                "description": (
                    "Fase acuta: dieta elementare (2 settimane) o semi-elementare. "
                    "Fase successiva: low-FODMAP phased con monitoraggio. "
                    "Evitare fibre fermentabili durante l'attivo."
                ),
                "note": "La dieta elementare ha tassi di remissione del 70-80% in studi clinici"
            },
            {
                "name": "Procinetici",
                "description": (
                    "Prucalopride, eritromicina a basse dosi, 5-HT4 agonisti. "
                    "Migliorano la motilità interdigestiva (MMC)."
                ),
                "note": "Essenziale per prevenire recidive post-trattamento"
            },
            {
                "name": "Spaziatura dei pasti",
                "description": (
                    "Almeno 3-4 ore tra un pasto e il successivo. "
                    "Lasciare 12h di digiuno notturno. "
                    "Favorisce il ciclo motorio migrante (MMC)."
                )
            }
        ],
        "foods_avoid": [
            "Cibi ad alto FODMAP durante fase attiva",
            "Fibre fermentabili (inulina, frutto-oligosaccaridi)",
            "Zuccheri fermentabili (sorbitolo, xilitolo)",
            "Bevande gassate",
            "Alcolici (alterano motilità e microflora)",
            "Cibi ricchi di fibre insolubili in fase acuta"
        ],
        "foods_safe": [
            "Verdure ben cotte (zucchine, carote, peperoni)",
            "Riso bianco, patate, polenta",
            "Proteine magre (pollo, tacchino, pesce, uova)",
            "Brodo d'osso",
            "Olio d'oliva, burro",
            "Erbe fresche (basilico, prezzemolo)"
        ],
        "nutrients_monitor": ["Ferro", "B12", "Vitamina D", "Zinco", "Magnesio"],
        "note_important": (
            "⚠️ ATTENZIONE PPI: gli inibori di pompa protonica aumentano significativamente "
            "il rischio di SIBO (OR 1.5-2.0). Valutare con il medico la sospensione se possibile."
        ),
        "probiotics": (
            "Probiotici selezionati: Saccharomyces boulardii (non fermenta), "
            "Lactobacillus reuteri DSM 17938. "
            "⚠️ Evitare probiotici polifermmentati durante fase acuta."
        ),
        "fonti": [
            "PMC 2025 - Nutrients 17:01410 - SIBO dietary management",
            "ACG 2020 - SIBO Clinical Guidelines",
            "Cleveland Clinic 2024 - SIBO Diet and Treatment",
            "Pimentel M et al. (2024) - SIBO pathophysiology update",
            "Lombardo L et al. (2025) - Prokinetics SIBO recurrence"
        ]
    },

    # ── SIBO - Sottotipo Idrogeno ────────────────────────────────────────
    "sibo_hydrogen": {
        "name": "SIBO - Sottotipo Idrogeno",
        "category": "gastrointestinal",
        "evidence_level": "alta",
        "description": (
            "SIBO con predominanza di produzione di idrogeno. "
            "Tipicamente associato a diarrea. Il gas idrogeno accelera il transito intestinale."
        ),
        "strategies": [
            {
                "name": "Dieta specifica per SIBO idrogeno",
                "description": (
                    "Evitare carboidrati fermentabili a catena corta (FOS, inulina). "
                    "Privilegiare amidi raffinati. "
                    "Limitare frutta ad alto fruttosio."
                )
            }
        ],
        "foods_avoid": [
            "Cipolla, aglio (FOS)",
            "Legumi (galattani)",
            "Cavolfiore, cavolo (FOS)",
            "Miele, sciroppo d'agave",
            "Frutta ad alto fruttosio: mele, pere, mango",
            "Cereali integrali"
        ],
        "foods_safe": [
            "Riso bianco, patate, polenta",
            "Verdure cotte: carote, zucchine, peperoni",
            "Proteine magre",
            "Frutta: kiwi, banane (non troppo mature), mirtilli",
            "Olio d'oliva, burro"
        ],
        "fonti": [
            "PMC 2025 - Nutrients 17:01410",
            "ACG 2020 - SIBO guidelines",
            "Pimentel M et al. - Hydrogen SIBO subtype"
        ]
    },

    # ── SIBO - Sottotipo Metano ──────────────────────────────────────────
    "sibo_methane": {
        "name": "SIBO - Sottotipo Metano",
        "category": "gastrointestinal",
        "evidence_level": "alta",
        "description": (
            "SIBO con predominanza di metano (IMO - Intestinal Methane Overgrowth). "
            "Tipicamente associato a stipsi. Il metano rallenta il transito intestinale."
        ),
        "strategies": [
            {
                "name": "Dieta specifica per SIBO metano",
                "description": (
                    "Meno restrittiva rispetto al sottotipo idrogeno. "
                    "Evitare eccesso di fibre fermentabili. "
                    "Favorire l'idratazione e l'attività fisica per stimolare la motilità."
                )
            }
        ],
        "foods_avoid": [
            "Eccesso di fibre fermentabili (legumi, crusca)",
            "Bevande gassate (aggiungono gas)",
            "Dolcificanti polialcolici",
            "Cibi che rallentano ulteriormente il transito"
        ],
        "foods_safe": [
            "Verdure cotte, fibre soluble (avena, semi di chia in moderazione)",
            "Proteine magre",
            "Grassi salutari (olio d'oliva, avocado in moderazione)",
            "Acqua abbondante (≥2L/giorno)"
        ],
        "fonti": [
            "PMC 2025 - Nutrients 17:01410",
            "Pimentel M et al. - Methanogen overgrowth treatment",
            "ACG 2020 - IMO management"
        ]
    },

    # ── Intolleranza all'Istamina ────────────────────────────────────────
    "histamine_intolerance": {
        "name": "Intolleranza all'Istamina (HIT)",
        "category": "intolerance",
        "evidence_level": "media",
        "description": (
            "Accumulo di istamina dovuto a carenza dell'enzima diamino ossidasi (DAO) "
            "o eccesso di istamina alimentare. Sintomi: cefalea, orticaria, disturbi "
            "gastrointestinali, congestione nasale. Spesso confusa con MCAS."
        ),
        "strategies": [
            {
                "name": "Dieta a basso contenuto di istamina (fasi)",
                "phases": [
                    "Fase 1 - Eliminazione (2-4 settimane): eliminare alimenti ad alto istamina",
                    "Fase 2 - Reinserimento (4-8 settimane): testare singoli alimenti",
                    "Fase 3 - Mantenimento: soglia individuale"
                ],
                "note": "Solo il 50% dei pazienti risponde alla dieta; considerare integratori DAO"
            },
            {
                "name": "Cofattori DAO",
                "description": (
                    "Vitamina C (500-1000 mg/day), Vitamina B6 (25-50 mg/day), "
                    "Rame (2 mg/day), Zinco (15-30 mg/day). "
                    "Supportano l'attività dell'enzima DAO."
                )
            }
        ],
        "foods_avoid": [
            "Alimenti fermentati: crauti, kimchi, miso, salsa di soia, aceto",
            "Formaggi stagionati e affumicati",
            "Salumi, insaccati, carni conservate",
            "Pesce conservato (in scatola, affumicato, marinato)",
            "Alcolici (vino, birra) - contengono istamina e rilasciano istamina",
            "Spinaci, pomodori, melanzane, avocado",
            "Agrumi, fragole, banane (mature)",
            "Cibi avanzati/avanzi >24h (istamina si forma con il tempo)",
            "Salsa Worcestershire, ketchup",
            "Bevande energetizzanti"
        ],
        "foods_safe": [
            "Carne fresca (cottura immediata dopo l'acquisto)",
            "Pesce fresco (cottura immediata, surgelato OK)",
            "Verdure fresche (carote, zucca, cetriolo, broccoli, lattuga)",
            "Riso, avena, quinoa",
            "Olio d'oliva extravergine, olio di cocco",
            "Erbe fresche (basilico, prezzemolo, coriandolo)",
            "Formaggi freschi: mozzarella, ricotta",
            "Latte fresco"
        ],
        "probiotics": (
            "Probiotici con evidenza in HIT: Lactobacillus rhamnosus GG, "
            "Bifidobacterium longum (supportano l'attività DAO). "
            "⚠️ Evitare fermenti lattici tradizionali (possono aggravare)."
        ),
        "fonti": [
            "SIGHI (Swiss Interest Group Histamine Intolerance) - lista alimenti aggiornata 2024",
            "MDPI Nutrients 2025 - Histamine intolerance dietary management",
            "MastCell360 2025 - Evidence-based histamine guidance",
            "Maintz L et al. (2023) - Histamine intolerance revisited",
            "Sánchez-Pérez S et al. (2025) - DAO cofactors systematic review"
        ]
    },

    # ── Dysbiosis / Squilibrio Microbioma ────────────────────────────────
    "dysbiosis": {
        "name": "Dysbiosis / Squilibrio del Microbioma Intestinale",
        "category": "gastrointestinal",
        "evidence_level": "media",
        "description": (
            "Alterazione della composizione e/o funzione del microbiota intestinale. "
            "Riduzione della biodiversità batterica, diminuzione batteri benefici "
            "(Bifidobacterium, Lactobacillus), aumento di patobionti. "
            "Associata a IBS, malattie infiammatorie, obesità, autoimmune."
        ),
        "strategies": [
            {
                "name": "Fibre diverse e abbondanti",
                "description": (
                    "25-30 g/giorno da fonti varie (non solo una tipologia). "
                    "Fibre solubili: avena, semi di lino, legumi. "
                    "Fibre insolubili: verdure a foglia, cereali integrali. "
                    "La diversità nella fibra alimenta diversità microbica."
                )
            },
            {
                "name": "Alimenti fermentati",
                "description": (
                    "Kefir (lattiero), crauti fermentati, kimchi, kombucha, miso. "
                    "Il randomized trial Stanford 2021 ha mostrato aumento biodiversità "
                    "con dieta ricca di alimenti fermentati (6 porzioni/giorno per 10 settimane)."
                )
            },
            {
                "name": "Prebiotici naturali",
                "description": (
                    "Cipolla, aglio, porri, asparagi, banana, avena, crusca, cicoria. "
                    "Alimentano Bifidobacterium e Lactobacillus."
                )
            },
            {
                "name": "Polifenoli",
                "description": (
                    "Frutti di bosco, tè verde, cioccolato fondente (>70%), "
                    "olio extra vergine d'oliva, spezie (curcuma, zenzero). "
                    "I polifenoli sono metabolizzati dai batteri intestinali e agiscono come prebiotici."
                )
            },
            {
                "name": "Ridurre cibi ultra-processati",
                "description": (
                    "Gli emulsionanti (E466, E433, E463) alterano la barriera mucosa. "
                    "I dolcificanti artificiali (saccarina, sucralosio, aspartame) modificano "
                    "il microbiota in modo indesiderato."
                )
            }
        ],
        "foods_avoid": [
            "Cibi ultra-processati (NOVA 4)",
            "Dolcificanti artificiali (saccarina, sucralosio, aspartame)",
            "Eccesso di alcol (modifica microbiota in 4 settimane)",
            "Eccesso di carne rossa",
            "Emulsionanti nei cibi processati (E466, E433, E463)",
            "Grassi trans"
        ],
        "foods_safe": [
            "Frutta e verdura diversificate (≥5 porzioni/giorno)",
            "Legumi (≥3 volte/settimana)",
            "Cereali integrali",
            "Latticini fermentati (yogurt, kefir)",
            "Brodo d'osso",
            "Frutti di bosco, mirtilli, more",
            "Tè verde, caffè in moderazione",
            "Spezie: curcuma, zenzero, cannella",
            "Olio extra vergine d'oliva"
        ],
        "probiotics": (
            "Probiotici con evidenza in dysbiosis: "
            "Lactobacillus rhamnosus GG, Bifidobacterium longum BB536, "
            "Lactobacillus plantarum 299v, Saccharomyces boulardii. "
            "La meta-analisi 2025 (PMC) mostra aumento biodiversità con "
            "probiotici multi-ceppo. Preferire prodotti con almeno 10^9 CFU/giorno."
        ),
        "fonti": [
            "ISAPP (2026) - Nature Reviews Gastroenterology: probiotics & microbiome",
            "PMC 2025 - Precision nutrition & gut microbiota",
            "Gut Microbiota for Health (2025) - Expert consensus",
            "Sonnenburg JL et al. (2021) - Fermented foods RCT (Stanford)",
            "Zhao L et al. (2025) - Dietary fiber microbiome diversity",
            "Sánchez-Rodríguez MA et al. (2025) - Dysbiosis review"
        ]
    },

    # ── Calcoli Renali (Calcolo Oxalato di Calcio) ────────────────────────
    "kidney_stones": {
        "name": "Calcoli Renali (Calcolo Oxalato di Calcio)",
        "category": "renal",
        "evidence_level": "alta",
        "description": (
            "Formazione di calcoli renali, prevalentemente oxalato di calcio (70-80% dei casi). "
            "Fattori di rischio: disidratazione, eccesso di ossalati, ipercalciuria, "
            "ridotto citrato urinario, eccesso di sodio. Prevalenza ~10% nella vita."
        ),
        "strategies": [
            {
                "name": "Idratazione adeguata",
                "description": (
                    "Almeno 2 litri di acqua al giorno, preferibilmente 2,5-3L. "
                    "Urine chiaro-palestrina come indicatore. "
                    "L'acqua alcalina (pH > 8.0) può essere utile."
                )
            },
            {
                "name": "Calcio con i pasti",
                "description": (
                    "900-1200 mg/giorno da ALIMENTI (non integratori a stomaco vuoto). "
                    "Il calcio con i pasti lega l'ossalato intestinale e ne riduce l'assorbimento."
                ),
                "note": "Riduzione del 50% rischio recidive con calcio dietetico adeguato"
            },
            {
                "name": "Limitare ossalati",
                "description": (
                    "Ridurre alimenti ad alto contenuto di ossalato. "
                    "Non eliminare completamente (rischio carenze). "
                    "Cuocere le verdure per ridurre ossalato solubile."
                )
            },
            {
                "name": "Ridurre sodio",
                "description": (
                    "Meno di 2300 mg/giorno, idealmente <1500 mg. "
                    "Il sodio aumenta l'escrezione renale di calcio."
                )
            }
        ],
        "foods_avoid": [
            "Spinaci (ossalato ~970 mg/100g - massimo rischio)",
            "Rabarbaro (ossalato ~860 mg/100g)",
            "Barbabietola (ossalato ~675 mg/100g)",
            "Mandorle e noci (ossalato elevato)",
            "Cioccolato fondente (ossalato ~228 mg/100g)",
            "Tè nero (ossalato elevato)",
            "Stella frutto/star fruit (nefrotossico)",
            "Soya/edamame (ossalato elevato)",
            "Cacao in polvere",
            "Aragosta (oxalato)"
        ],
        "foods_safe": [
            "Latticini (fonte di calcio che lega ossalato)",
            "Agrumi (citrato naturale - inibisce cristallizzazione)",
            "Acqua",
            "Verdure a basso ossalato: carote, zucchine, cetrioli, patate, cavolfiore",
            "Riso, pasta, pane",
            "Proteine magre (moderate)",
            "Mela, pera, anguria"
        ],
        "nutrients_monitor": ["Calcio", "Ossalato", "Sodio", "Citrato"],
        "fonti": [
            "AUA 2024 - Stones Guideline (Recurrent Stone Formers)",
            "Borghi L et al. (NEJM 2002) - Dietary calcium & kidney stones",
            "Kang DE et al. (2024) - Citrate & stone prevention",
            "Mitchell T et al. (2019) - Dietary oxalate & kidney stones"
        ]
    },

    # ── MCAS / Mast Cell Activation Syndrome ──────────────────────────────
    "mcas": {
        "name": "Sindrome da Attivazione dei Mastociti (MCAS)",
        "category": "allergy",
        "evidence_level": "media",
        "description": (
            "Attivazione inappropriata dei mastociti con rilascio di mediatori "
            "(istamina, triptasi, prostaglandine). Sintomi multi-sistemici: cutanei, "
            "GI, cardiovascolari, neurologici. Spesso comorbida con HIT. "
            "Prevalenza stimata: 1/10.000-20.000."
        ),
        "strategies": [
            {
                "name": "Dieta multi-restrittiva",
                "description": (
                    "Combinazione: low-histamine + low-lectina + low-oxalato + low-salicylato. "
                    "Evitare i degranulatori dei mastociti. "
                    "Frequenza delle reazioni dose-dipendente."
                ),
                "note": "Spesso si sovrappone con HIT; la restrizione istamina è fondamentale"
            },
            {
                "name": "Evitare degranulatori dei mastociti",
                "description": (
                    "Alcol, conservanti (benzoati, solfiti, nitrati), coloranti artificiali, "
                    "alistamine naturali (alici), salicilati, istamina alta, lectine."
                )
            }
        ],
        "foods_avoid": [
            "Tutti gli alimenti ad alto istamina (vedi histamine_intolerance)",
            "Legumi (lectine - fagioli, lenticchie, ceci)",
            "Nightshade: pomodoro, peperoni, melanzane, patata dolce",
            "Cereali con glutine (lectine wheat germ agglutinin)",
            "Alti ossalati: spinaci, rabarbaro, mandorle",
            "Alti salicilati: frutta secca, spezie, menta, miele",
            "Alcolici",
            "Cibi fermentati",
            "Alimenti affumicati e conservati",
            "Bevande gassate",
            "Formaggi stagionati"
        ],
        "foods_safe": [
            "Carne fresca cotta immediatamente (pollo, tacchino)",
            "Verdure a basso ossalato e basso istamina: carote, zucca, cetriolo",
            "Riso bianco",
            "Olio di cocco, olio d'oliva (basso salicylato)",
            "Erbe fresche (basilico, prezzemolo)",
            "Frutta: mela, pera (non acide)",
            "Olio di oliva extravergine (basso grado di reazione)",
            "Alimenti biochimicamente neutri: riso, patata dolce (moderata)"
        ],
        "note_importante": (
            "⚠️ MCAS si sovrappone frequentemente con histamine_intolerance. "
            "La gestione è più complessa e richiede spesso approccio multidisciplinare "
            "(allergologo + dietista specializzato). Monitorare triptasi sierica."
        ),
        "fonti": [
            "MastCell360 (2024) - MCAS dietary management evidence",
            "SIGHI (2024) - MCAS & histamine management protocol",
            "Afrin LB et al. (2024) - MCAS diagnostic criteria & management",
            "Hamilton MJ et al. (2023) - MCAS prevalence & symptoms"
        ]
    },

    # ── IBD: Malattia di Crohn / Colite Ulcerosa ──────────────────────────
    "ibd": {
        "name": "Malattia Infiammatoria Cronica Intestinale (IBD: Crohn / Colite Ulcerosa)",
        "category": "gastrointestinal",
        "evidence_level": "media",
        "description": (
            "Patologie infiammatorie croniche immuno-mediate del tratto GI. La nutrizione "
            "è terapia di supporto: gestisce sintomi, previene malnutrizione e sostiene "
            "la remissione. La EEN (nutrizione enterale esclusiva) è prima linea per "
            "indurre remissione nel Crohn pediatrico (efficacia pari agli steroidi)."
        ),
        "strategies": [
            {
                "name": "EEN - Nutrizione Enterale Esclusiva",
                "phases": [
                    "6-8 settimane di formula liquida polimerica esclusiva",
                    "Reintroduzione graduale del cibo (partial enteral nutrition)"
                ],
                "efficacy": "Induzione remissione Crohn pediatrico ~80% (pari a corticosteroidi, senza effetti collaterali)",
                "note": "Gold standard pediatrico; nell'adulto compliance più bassa"
            },
            {
                "name": "CDED - Crohn's Disease Exclusion Diet",
                "description": "Esclude alimenti pro-infiammatori (grassi animali, emulsionanti, glutine, latticini processati) + PEN parziale",
                "efficacy": "Remissione + migliore compliance vs EEN (Levine 2019, uso confermato 2024-2025)",
                "note": "Approccio strutturato in 3 fasi con reintroduzione"
            },
            {
                "name": "SCD - Specific Carbohydrate Diet",
                "description": "Elimina carboidrati complessi/raffinati e zuccheri (tranne monosaccaridi); ammette carne, pesce, verdure, frutta, yogurt fermentato 24h",
                "efficacy": "Efficace in casistiche pediatriche IBD; migliora sintomi e marker infiammatori",
                "note": "Restrittiva: rischio carenze, richiede supervisione dietetica"
            },
            {
                "name": "AIP - Autoimmune Protocol",
                "description": "Estensione della paleo: elimina cereali, legumi, latticini, uova, solanacee, noci, semi, alcol, additivi; reintroduzione strutturata",
                "efficacy": "Migliora QOL e sintomi in IBD (Inflamm Bowel Dis); evidenza preliminare ma promettente",
                "note": "Molto restrittiva; solo con dietista, rischio deficit nutrizionali"
            },
            {
                "name": "Dieta mediterranea (mantenimento)",
                "description": "Pattern anti-infiammatorio per la fase di remissione: ricca in fibre solubili, omega-3, polifenoli",
                "efficacy": "Riduce infiammazione sistemica; sostenibile a lungo termine",
                "note": "Preferita in remissione; in fase acuta ridurre fibra insolubile"
            }
        ],
        "foods_avoid_high": [
            "Fase acuta: fibra insolubile (crusca, verdure crude filamentose, bucce, semi)",
            "Emulsionanti e additivi (carbossimetilcellulosa, polisorbato-80) — pro-infiammatori sul microbiota",
            "Carni processate e grassi saturi animali in eccesso",
            "Zuccheri raffinati e ultra-processati",
            "Alcol; latticini se lattosio-intolleranza associata"
        ],
        "foods_safe": [
            "Proteine magre: pesce (omega-3), pollame, uova (se tollerate)",
            "Carboidrati facilmente digeribili in fase acuta: riso bianco, patate, pasta ben cotta",
            "Fibra solubile: avena, banana matura, carota cotta",
            "Verdure cotte, sbucciate e senza semi",
            "Omega-3 (EPA/DHA) da pesce azzurro"
        ],
        "probiotics": (
            "Colite ulcerosa: VSL#3/De Simone (8 ceppi) con evidenza per mantenimento remissione "
            "e pouchite. E. coli Nissle 1917 non-inferiore alla mesalazina in CU. "
            "Crohn: evidenza probiotici più debole."
        ),
        "fonti": [
            "Levine A et al. (2019, uso 2024-25) - CDED + PEN Crohn",
            "Inflamm Bowel Dis (2024) - AIP migliora QOL in IBD",
            "Suskind DL et al. - SCD pediatrico IBD",
            "ESPEN (2023-2024) - linee guida nutrizione clinica IBD",
            "Chande N (Cochrane) - EEN induzione remissione Crohn"
        ]
    },

    # ── Endometriosi ──────────────────────────────────────────────────────
    "endometriosis": {
        "name": "Endometriosi",
        "category": "hormonal_inflammatory",
        "evidence_level": "media",
        "description": (
            "Patologia infiammatoria estrogeno-dipendente. La nutrizione è terapia di "
            "SUPPORTO (non curativa): riduce l'infiammazione, modula gli estrogeni e "
            "allevia i sintomi GI e il dolore pelvico. Evidenza più solida per il "
            "pattern mediterraneo/anti-infiammatorio."
        ),
        "strategies": [
            {
                "name": "Dieta mediterranea / anti-infiammatoria (DII basso)",
                "description": "Alta in verdura, frutta, legumi, cereali integrali, olio EVO, pesce; bassa in carne rossa e carboidrati raffinati",
                "efficacy": "Riduzione significativa di dispareunia (p=0.002) e dischezia (p<0.001) a 6 mesi; DII alto ≈ rischio endometriosi ~3x",
                "note": "Prima linea evidence-based; ricca in antiossidanti, omega-3, polifenoli (inibiscono COX, riducono IL-6/TNF-α, aumentano SHBG)"
            },
            {
                "name": "Low-FODMAP (per sintomi GI/IBS associati)",
                "description": "Per la componente IBS-like (gonfiore, dolore addominale)",
                "efficacy": "Miglioramento nel 72% delle donne con endometriosi+IBS vs 49% IBS senza endometriosi (p=0.001)",
                "note": "Mirata ai sintomi intestinali, non all'infiammazione pelvica diretta"
            },
            {
                "name": "Dieta senza glutine (opzionale)",
                "description": "Esclusione del glutine",
                "efficacy": "Riduzione del dolore nel 75% a 12 mesi in uno studio (VAS>4); meccanismo incerto, possibile effetto placebo",
                "note": "Non prima linea; valutare caso per caso"
            }
        ],
        "foods_avoid_high": [
            "Carne rossa e processata (associata a rischio e infiammazione)",
            "Grassi trans e cibi ultra-processati",
            "Alcol (meccanismi infiammatori/ormonali)",
            "Caffeina in eccesso (>300 mg/die) se peggiora sintomi",
            "Carboidrati raffinati e zuccheri"
        ],
        "foods_safe": [
            "Verdura e frutta ricche di antiossidanti (ORAC elevato)",
            "Pesce azzurro (omega-3 EPA/DHA)",
            "Olio extravergine d'oliva, noci, semi (con moderazione)",
            "Legumi e cereali integrali",
            "Tè verde (EGCG - agente potenzialmente terapeutico, Markowska 2025)"
        ],
        "probiotics": "Evidenza limitata; l'asse microbiota-estrogeni (estroboloma) è area di ricerca emergente.",
        "fonti": [
            "PMC 2025 (Nutrients 18:00142) - Role of Lifestyle and Diet in Endometriosis",
            "Neri LCL et al. (Foods 2025, MDPI) - Diet and Endometriosis: Umbrella Review",
            "Noormohammadi et al. (Sci Rep 2025) - MedDiet adherence & endometriosis",
            "Viganò et al. (BMJ Open 2025) - anti-inflammatory diet pre-IVF RCT protocol",
            "Markowska A et al. (Nutrients 2025 17:2068) - EGCG in endometriosis"
        ]
    },

    # ── MASLD (ex NAFLD): steatosi epatica metabolica ─────────────────────
    "masld": {
        "name": "MASLD - Steatosi Epatica Associata a Disfunzione Metabolica (ex NAFLD)",
        "category": "metabolic",
        "evidence_level": "alta",
        "description": (
            "Accumulo di grasso epatico associato a disfunzione metabolica. La perdita di "
            "peso è il cardine terapeutico: -5% riduce la steatosi, -7-10% migliora "
            "steatoepatite e fibrosi. Pattern mediterraneo di prima scelta."
        ),
        "strategies": [
            {
                "name": "Calo ponderale graduale",
                "phases": [
                    "-5% peso: riduzione del grasso epatico",
                    "-7-10% peso: miglioramento di steatoepatite (MASH) e fibrosi"
                ],
                "efficacy": "Effetto dose-dipendente su steatosi, infiammazione e fibrosi",
                "note": "Perdita di 0.5-1 kg/settimana; evitare cali troppo rapidi"
            },
            {
                "name": "Dieta mediterranea",
                "description": "Prima scelta: olio EVO, pesce, verdura, frutta, cereali integrali; bassa in zuccheri e carne rossa",
                "efficacy": "Riduce grasso epatico anche indipendentemente dal calo di peso",
                "note": "Raccomandata dalle linee guida EASL/AASLD"
            },
            {
                "name": "Riduzione fruttosio e zuccheri aggiunti",
                "description": "Eliminare bevande zuccherate e sciroppi di fruttosio (lipogenesi epatica de novo)",
                "efficacy": "Riduzione della lipogenesi e del grasso epatico",
                "note": "Il fruttosio delle bevande è il target principale"
            },
            {
                "name": "Attività fisica",
                "description": "150-300 min/settimana aerobica + resistenza",
                "efficacy": "Riduce grasso epatico anche senza calo di peso significativo",
                "note": "Sinergica con la dieta"
            }
        ],
        "foods_avoid_high": [
            "Bevande zuccherate e succhi (fruttosio → lipogenesi epatica)",
            "Cibi ultra-processati e zuccheri aggiunti",
            "Carne rossa e processata",
            "Grassi saturi e trans; fritture",
            "Alcol (co-fattore, da limitare o eliminare)"
        ],
        "foods_safe": [
            "Olio extravergine d'oliva (grassi monoinsaturi)",
            "Pesce azzurro (omega-3)",
            "Verdura, legumi, cereali integrali (fibra)",
            "Caffè (2-3 tazze/die associato a minore fibrosi epatica)",
            "Frutta intera con moderazione (non succhi)"
        ],
        "probiotics": "Evidenza emergente su asse intestino-fegato; probiotici/simbiotici possono ridurre transaminasi (dati preliminari).",
        "fonti": [
            "EASL-EASD-EASO (2024) - clinical practice guidelines MASLD",
            "AASLD (2023-2024) - NAFLD/MASLD nutrition guidance",
            "Meta-analisi 2025 - MedDiet & hepatic fat reduction"
        ]
    },

    # ── PCOS: sindrome dell'ovaio policistico ─────────────────────────────
    "pcos": {
        "name": "PCOS - Sindrome dell'Ovaio Policistico",
        "category": "hormonal_inflammatory",
        "evidence_level": "media",
        "description": (
            "Disordine endocrino-metabolico con insulino-resistenza frequente. La "
            "nutrizione mira a migliorare la sensibilità insulinica, il peso e "
            "l'assetto ormonale. Inositolo e pattern a basso indice glicemico hanno "
            "l'evidenza migliore."
        ),
        "strategies": [
            {
                "name": "Dieta a basso indice/carico glicemico",
                "description": "Carboidrati a basso IG, ricca in fibre, proteine adeguate; distribuzione bilanciata",
                "efficacy": "Migliora insulino-resistenza, ciclo mestruale e marker androgenici",
                "note": "Cardine dietetico; sinergica con calo di peso se sovrappeso"
            },
            {
                "name": "Inositolo (myo + D-chiro 40:1)",
                "description": "Myo-inositolo 2-4 g/die ± D-chiro-inositolo in rapporto fisiologico 40:1",
                "efficacy": "Migliora sensibilità insulinica, ovulazione e parametri metabolici (evidenza robusta)",
                "note": "Ben tollerato; rapporto 40:1 è quello fisiologico ottimale"
            },
            {
                "name": "Calo ponderale (se sovrappeso)",
                "description": "-5-10% del peso corporeo",
                "efficacy": "Ripristina l'ovulazione e migliora l'assetto metabolico/ormonale",
                "note": "Anche modesto è efficace"
            },
            {
                "name": "Pattern mediterraneo/anti-infiammatorio",
                "description": "Riduce l'infiammazione cronica di basso grado associata a PCOS",
                "efficacy": "Migliora marker infiammatori e cardiometabolici",
                "note": "Complementare alle strategie glicemiche"
            }
        ],
        "foods_avoid_high": [
            "Zuccheri raffinati e bevande zuccherate (picchi insulinici)",
            "Carboidrati ad alto IG (pane bianco, dolci, riso raffinato)",
            "Cibi ultra-processati e grassi trans",
            "Eccesso di grassi saturi"
        ],
        "foods_safe": [
            "Carboidrati a basso IG: legumi, cereali integrali, verdura",
            "Proteine magre e pesce (omega-3)",
            "Grassi buoni: olio EVO, frutta secca, avocado",
            "Fibra abbondante (rallenta l'assorbimento glucidico)",
            "Alimenti ricchi di inositolo (agrumi, legumi, cereali integrali)"
        ],
        "probiotics": "Evidenza preliminare: probiotici/simbiotici possono migliorare marker metabolici e ormonali in PCOS.",
        "fonti": [
            "International PCOS Guideline (2023, uso 2024-25) - diet & lifestyle first-line",
            "Meta-analisi 2024-2025 - inositolo myo+DCI 40:1 in PCOS",
            "Review 2025 - low-GI diet & insulin resistance PCOS"
        ]
    }
}


# ═════════════════════════════════════════════════════════════════════════════
# CONFLITTI TRA CONDIZIONI
# Regole per quando due o più condizioni coesistono nello stesso paziente.
# ═════════════════════════════════════════════════════════════════════════════

CONDITION_CONFLICTS = {
    ("ibs", "sibo"): (
        "IBS+SIBO: Low-FODMAP potrebbe non essere sufficiente; "
        "valutare fase di dieta elementare. Lo SIBO è causa frequente di IBS refrattario."
    ),
    ("histamine_intolerance", "sibo"): (
        "HIST+SIBO: Alimenti fermentati (probiotici classici) possono peggiorare l'istamina; "
        "usare ceppi non fermentanti (S. boulardii, L. rhamnosus GG)."
    ),
    ("ibs", "histamine_intolerance"): (
        "IBS+IST: Molti alimenti sicuri per IBS sono ad alto istamina "
        "(avocado, pomodoro, spinaci). Serve filtro duplice."
    ),
    ("celiac", "dysbiosis"): (
        "CELIAC+DISBIOSIS: La dieta senza glutine può ridurre Bifidobacterium; "
        "integrare con prebiotici e alimenti fermentati."
    ),
    ("diabetes_t2", "sibo"): (
        "DM2+SIBO: Lo SIBO peggiora l'insulino-resistenza; "
        "trattare prima lo SIBO prima della gestione dietetica DM2."
    ),
    ("mcas", "histamine_intolerance"): (
        "MCAS+IST: Solitamente protocollo unico; "
        "massimizzare la restrizione di istamina e valutare terapia farmacologica."
    ),
    ("ibs", "kidney_stones"): (
        "IBS+STONES: Low-FODMAP + low-ossalato è molto restrittivo; "
        "garantire adeguato apporto di calcio e fibra solubile."
    ),
    ("obesity", "dysbiosis"): (
        "OBESITY+DISBIOSIS: La restrizione calorica può peggiorare il dysbiosis; "
        "prioritizzare la diversità della fibra e alimenti fermentati."
    ),
    ("celiac", "lactose_intolerance"): (
        "Co-occorrenza frequente; "
        "integrare calcio e vitamina D, verificare tolleranza latticini fermentati."
    ),
    ("eoe", "food_allergy"): (
        "EoE+ALLERGY: La dieta 4FED potrebbe necessitare espansione; "
        "monitoraggio specialistico con endoscopia di controllo."
    ),
    ("ibd", "ibs"): (
        "IBD+IBS: sintomi IBS-like frequenti in IBD in remissione. Distinguere "
        "l'infiammazione attiva (calprotectina) dai sintomi funzionali prima di "
        "restringere la dieta; il low-FODMAP aiuta i sintomi funzionali ma NON tratta l'infiammazione."
    ),
    ("ibd", "lactose_intolerance"): (
        "IBD+INTOLLERANZA LATTOSIO: intolleranza al lattosio comune (specie Crohn ileale). "
        "Evitare restrizioni non necessarie: garantire calcio e vitamina D con alternative."
    ),
    ("masld", "diabetes_t2"): (
        "MASLD+DM2: fortemente co-occorrenti (asse cardiometabolico). Priorità al calo "
        "ponderale e alla dieta mediterranea/basso-IG; considerare GLP-1 RA/SGLT2i con il medico."
    ),
    ("masld", "obesity"): (
        "MASLD+OBESITÀ: il calo ponderale -7-10% è il target terapeutico condiviso. "
        "Un unico piano ipocalorico mediterraneo copre entrambe."
    ),
    ("pcos", "obesity"): (
        "PCOS+OBESITÀ: insulino-resistenza comune. Dieta a basso IG + calo del 5-10% "
        "migliora sia l'assetto metabolico sia quello ormonale/ovulatorio."
    ),
    ("pcos", "diabetes_t2"): (
        "PCOS+DM2: gestione glicemica prioritaria; inositolo 40:1 e basso-IG sinergici. "
        "Coordinare con eventuale terapia (metformina)."
    ),
    ("endometriosis", "ibs"): (
        "ENDOMETRIOSI+IBS: sintomi GI sovrapposti. Il low-FODMAP ha efficacia superiore "
        "(72% vs 49%) in questa combinazione; abbinare al pattern anti-infiammatorio."
    )
}


# ═════════════════════════════════════════════════════════════════════════════
# INTEGRATORI (SUPPLEMENTS) PER CONDIZIONE
# ═════════════════════════════════════════════════════════════════════════════

SUPPLEMENTS = {
    "ibs": [
        {
            "name": "Psillio (Psyllium)",
            "dose": "5-10 g/day",
            "rationale": "Fibra solubile, primo trattamento IBS",
            "warning": "Iniziare basso, aumentare gradualmente per evitare gonfiore"
        },
        {
            "name": "Probiotico (L. plantarum 299v)",
            "dose": "10^10 CFU/day",
            "rationale": "Meta-analisi 2024: riduce dolore IBS",
            "warning": ""
        },
        {
            "name": "Menta piperita (capsule enteriche)",
            "dose": "0,2-0,4 ml 3x/giorno",
            "rationale": "Riduce gonfiore e dolore (ACG 2024)",
            "warning": "Non per pazienti con GERD (rilassa sfintere)"
        }
    ],
    "sibo": [
        {
            "name": "Rifaximina",
            "dose": "550 mg 3x/giorno per 14 gg",
            "rationale": "Prima linea SIBO idrogeno (ACG)",
            "warning": "Solo su prescrizione medica"
        },
        {
            "name": "Neomicina",
            "dose": "500 mg 2x/giorno per 14 gg (associata a rifaximina)",
            "rationale": "Prima linea SIBO metano/IMO — la combinazione rifaximina+neomicina supera rifaximina da sola sul metano (Pimentel, Cedars-Sinai 2025)",
            "warning": "Solo su prescrizione medica; ototossicità/nefrotossicità a dosi elevate"
        },
        {
            "name": "Procinetici (Prucalopride / LDN / Iberogast)",
            "dose": "Prucalopride 1-2 mg/die la sera; oppure LDN (low-dose naltrexone) 2.5-4.5 mg/die; oppure Iberogast 20 gtt 3x/die",
            "rationale": "ESSENZIALI nel MANTENIMENTO: stimolano il complesso motorio migrante (MMC) durante il digiuno notturno, prevenendo le recidive. LDN ritarda la recidiva nel ~62% dei casi (siboinfo 2025). La recidiva a 9 mesi è ~44% senza procinetico.",
            "warning": "Su prescrizione; il procinetico va iniziato DOPO il ciclo antibiotico e proseguito per mesi"
        },
        {
            "name": "Dieta elementare (opzione food-free)",
            "dose": "Formula elementare esclusiva per 14-21 giorni",
            "rationale": "Alternativa/aggiunta agli antibiotici per SIBO refrattario: normalizza il breath test nell'~80% dei casi (Cedars-Sinai 2025, versione 'palatable'). Nutre l'ospite, non i batteri distali.",
            "warning": "Solo sotto supervisione clinica/nutrizionale; rischio di ipoglicemia e monotonia; reintrodurre cibo gradualmente (transition diet: brodi → zuppe → pasti solidi in 3-4 gg, i villi rigenerano rapidamente)"
        },
        {
            "name": "Nistatina",
            "dose": "come prescritto",
            "rationale": "Per SIFO/SIBO fungino (candida overgrowth) sospetto",
            "warning": "Solo su prescrizione medica"
        }
    ],
    "histamine_intolerance": [
        {
            "name": "DAO suina (diamino ossidasi)",
            "dose": "4.2 mg (≈20.000 HDU) 20 min prima dei 3 pasti principali",
            "rationale": "TRATTAMENTO PRIMARIO evidence-based: la DAO di origine suina (kidney) alla dose di 4.2 mg pre-pasto ha ridotto significativamente TUTTI i sintomi HIT in tutti gli studi disponibili (review Comas-Basté, IJMS 2025 26:9198; O'Connor 82 pz DAOgest 2023). Efficace anche su emicrania (Izquierdo-Casas, Clin Nutr 2019, 100 pz) e orticaria cronica.",
            "warning": "Non assorbita in circolo (agisce solo nel lume intestinale); assumere a stomaco relativamente vuoto pre-pasto"
        },
        {
            "name": "Vitamina C",
            "dose": "500-1000 mg/day (co-formulata con la DAO quando possibile)",
            "rationale": "Cofattore DAO + decompone l'H2O2 prodotta dalla degradazione dell'istamina: le formulazioni DAO+Vit C degradano più istamina della sola DAO (IJMS 2025)",
            "warning": ""
        },
        {
            "name": "Vitamina B6 (P5P)",
            "dose": "25-50 mg/day",
            "rationale": "Cofattore essenziale della DAO",
            "warning": "Non superare 100 mg/day (neuropatia periferica)"
        },
        {
            "name": "Rame",
            "dose": "2 mg/day",
            "rationale": "Cofattore metallico della DAO (rame-dipendente)",
            "warning": ""
        },
        {
            "name": "Quercetina",
            "dose": "250-500 mg 2x/day",
            "rationale": "Stabilizzatore dei mastociti (flavonolo): inibisce il rilascio di mediatori proinfiammatori e la degranulazione (utile per la componente MCAS)",
            "warning": ""
        }
    ],
    "lactose_intolerance": [
        {
            "name": "Lattasi enzima",
            "dose": "1 compressa prima di latticini",
            "rationale": "Digerisce il lattosio prima dell'assorbimento",
            "warning": ""
        }
    ],
    "celiac": [
        {
            "name": "Ferro",
            "dose": "come prescritto",
            "rationale": "Malassorbimento comune nei celiaci",
            "warning": "Monitorare ferritina; non integrare senza dosaggio"
        },
        {
            "name": "Vitamina D",
            "dose": "1000-2000 UI/day",
            "rationale": "Deficit frequente in celiaci non trattati",
            "warning": ""
        },
        {
            "name": "Calcio",
            "dose": "1000-1200 mg/day",
            "rationale": "Se non assume latticini (malassorbimento intestinale)",
            "warning": ""
        },
        {
            "name": "Zinco",
            "dose": "15-30 mg/day",
            "rationale": "Malassorbimento nel duodeno",
            "warning": ""
        },
        {
            "name": "Vitamina B12",
            "dose": "1000 mcg/day",
            "rationale": "Se malassorbimento ileale",
            "warning": ""
        }
    ],
    "diabetes_t2": [
        {
            "name": "Monitoraggio Vitamina B12",
            "dose": "B12 ematica ogni 6-12 mesi",
            "rationale": "Metformina riduce assorbimento B12",
            "warning": ""
        },
        {
            "name": "Omega-3",
            "dose": "2-4 g EPA+DHA/day",
            "rationale": "Protezione cardiovascolare + effetto antinfiammatorio",
            "warning": ""
        }
    ],
    "hypertension": [
        {
            "name": "Potassio",
            "dose": "da alimenti preferibilmente; integratore solo con controllo medico",
            "rationale": "Dieta DASH; il potassio abbassa la PA",
            "warning": "Attenzione in caso di nefropatia o farmaci risparmiatori di K+"
        },
        {
            "name": "Magnesio",
            "dose": "200-400 mg/day",
            "rationale": "Supporto pressione arteriosa + sonno",
            "warning": ""
        },
        {
            "name": "Omega-3",
            "dose": "2-4 g/day",
            "rationale": "Riduce PA sistolica di 2-5 mmHg",
            "warning": ""
        }
    ],
    "osteoporosis": [
        {
            "name": "Vitamina D3",
            "dose": "1000-2000 UI/day",
            "rationale": "Essenziale per assorbimento calcio",
            "warning": "Monitorare 25(OH)D; target >30 ng/mL"
        },
        {
            "name": "Vitamina K2 (MK-7)",
            "dose": "100-200 mcg/day",
            "rationale": "Dirige il calcio nelle ossa, allontanato dalle arterie",
            "warning": "Controindicata con anticoagulanti (warfarin)"
        },
        {
            "name": "Calcio",
            "dose": "1000-1200 mg/day da alimenti",
            "rationale": "Prima linea: latticini, sardine con lische, broccoli",
            "warning": "Non superare 1500 mg/day totale (dieta + integratori)"
        },
        {
            "name": "Magnesio",
            "dose": "300-400 mg/day",
            "rationale": "Supporta densità minerale ossea",
            "warning": ""
        }
    ],
    "obesity": [
        {
            "name": "Fibra solubile",
            "dose": "25-30 g/day",
            "rationale": "Sazietà + supporto microbioma",
            "warning": "Aumentare gradualmente"
        },
        {
            "name": "Proteine elevate",
            "dose": "1,6-2,2 g/kg/day",
            "rationale": "Preservare massa magra in deficit calorico",
            "warning": "Valutare funzionalità renale"
        }
    ],
    "kidney_stones": [
        {
            "name": "Citrato di potassio",
            "dose": "come prescritto",
            "rationale": "Alcalinizza urine, riduce cristallizzazione ossalato di calcio",
            "warning": ""
        },
        {
            "name": "Vitamina D",
            "dose": "monitoraggio 25(OH)D",
            "rationale": "Necessaria per metabolismo calcio, ma non iperdosare",
            "warning": "Eccesso di VitD può aumentare assorbimento ossalati (Verdana 2024)"
        }
    ],
    "dysbiosis": [
        {
            "name": "Probiotico multi-ceppo",
            "dose": "≥10^9 CFU/day",
            "rationale": "Ripristino biodiversità microbica (meta-analisi 2025)",
            "warning": "Iniziare a basso dosaggio e aumentare gradualmente"
        },
        {
            "name": "Prebiotici (FOS/GOS)",
            "dose": "5-10 g/day",
            "rationale": "Nutrono batteri benefici (Bifidobacterium)",
            "warning": "Possono causare gonfiore iniziale"
        }
    ],
    "eoe": [
        {
            "name": "Vitamina D",
            "dose": "600-1000 UI/day",
            "rationale": "Se 4FED e ridotto consumo latticini",
            "warning": ""
        },
        {
            "name": "Calcio",
            "dose": "1000-1200 mg/day",
            "rationale": "Se latte vaccino eliminato nella 4FED",
            "warning": ""
        }
    ],
    "ncgs": [
        {
            "name": "Psillio (Psyllium)",
            "dose": "5-10 g/day",
            "rationale": "Fibra solubile per regolarità intestinale",
            "warning": ""
        },
        {
            "name": "Vitamina D",
            "dose": "1000-2000 UI/day",
            "rationale": "Carenza frequente anche in NCGS",
            "warning": ""
        }
    ],
    "mcas": [
        {
            "name": "Vitamina C",
            "dose": "500-1000 mg/day",
            "rationale": "Stabilizzatore mastocitario naturale + cofattore DAO",
            "warning": ""
        },
        {
            "name": "Quercetina",
            "dose": "500 mg 2-3x/day",
            "rationale": "Stabilizzatore mastocitario naturale (evidenza in vitro e clinica)",
            "warning": ""
        }
    ],
    "ibd": [
        {
            "name": "Vitamina D",
            "dose": "1000-2000 UI/die (target 25-OH-D >30 ng/ml)",
            "rationale": "Deficit comune in IBD; immunomodulante, associata ad attività di malattia",
            "warning": "Monitorare la 25-OH-vitamina D"
        },
        {
            "name": "Ferro",
            "dose": "Orale se tollerato; EV in caso di malassorbimento/intolleranza o malattia attiva",
            "rationale": "Anemia sideropenica frequente (perdite ematiche + malassorbimento)",
            "warning": "Il ferro orale può peggiorare i sintomi GI in fase attiva → preferire EV"
        },
        {
            "name": "Vitamina B12",
            "dose": "Come da deficit (IM o orale ad alte dosi)",
            "rationale": "Malassorbimento nel Crohn ileale o dopo resezione ileale",
            "warning": ""
        },
        {
            "name": "Omega-3 (EPA/DHA)",
            "dose": "2-3 g/die",
            "rationale": "Anti-infiammatorio di supporto",
            "warning": "Evidenza sul mantenimento remissione modesta"
        },
        {
            "name": "Probiotici (VSL#3 / E. coli Nissle 1917)",
            "dose": "Come da prodotto",
            "rationale": "Colite ulcerosa: mantenimento remissione e pouchite (evidenza migliore che nel Crohn)",
            "warning": ""
        }
    ],
    "endometriosis": [
        {
            "name": "Omega-3 (EPA/DHA)",
            "dose": "1-2 g/die",
            "rationale": "Anti-infiammatorio; ottimizza rapporto omega-3/omega-6, riduce prostaglandine pro-infiammatorie",
            "warning": ""
        },
        {
            "name": "Vitamina D",
            "dose": "1000-2000 UI/die (secondo livelli)",
            "rationale": "Immunomodulante; livelli bassi associati a maggiore severità",
            "warning": "Monitorare la 25-OH-vitamina D"
        },
        {
            "name": "Magnesio",
            "dose": "200-400 mg/die",
            "rationale": "Riduzione del dolore/crampi mestruali",
            "warning": ""
        },
        {
            "name": "NAC (N-acetilcisteina)",
            "dose": "600 mg 3x/die (protocolli a cicli)",
            "rationale": "Antiossidante; dati preliminari su riduzione dimensioni endometriomi",
            "warning": "Evidenza preliminare"
        }
    ],
    "masld": [
        {
            "name": "Vitamina E",
            "dose": "800 UI/die (solo in MASH non diabetici, su indicazione)",
            "rationale": "Migliora istologia nella steatoepatite non-diabetica (AASLD)",
            "warning": "Solo su indicazione medica; discussione su rischi a lungo termine"
        },
        {
            "name": "Omega-3 (EPA/DHA)",
            "dose": "2-4 g/die",
            "rationale": "Riduce i trigliceridi epatici e sierici",
            "warning": ""
        },
        {
            "name": "Vitamina D",
            "dose": "Secondo livelli",
            "rationale": "Deficit comune; associato a severità della steatosi",
            "warning": ""
        }
    ],
    "pcos": [
        {
            "name": "Myo-inositolo + D-chiro-inositolo (40:1)",
            "dose": "Myo 2 g x2/die + D-chiro in rapporto 40:1",
            "rationale": "Migliora sensibilità insulinica, ovulazione e parametri metabolici (evidenza robusta)",
            "warning": "Rapporto fisiologico 40:1; ben tollerato"
        },
        {
            "name": "Vitamina D",
            "dose": "1000-2000 UI/die (secondo livelli)",
            "rationale": "Deficit frequente; coinvolta in insulino-resistenza e funzione ovarica",
            "warning": "Monitorare la 25-OH-vitamina D"
        },
        {
            "name": "Omega-3 (EPA/DHA)",
            "dose": "1-2 g/die",
            "rationale": "Migliora profilo lipidico e infiammazione; possibile riduzione androgeni",
            "warning": ""
        },
        {
            "name": "Berberina",
            "dose": "500 mg 2-3x/die prima dei pasti",
            "rationale": "Insulino-sensibilizzante (effetto simil-metformina in alcuni studi)",
            "warning": "Interazioni farmacologiche; non in gravidanza"
        }
    ]
}


# ═════════════════════════════════════════════════════════════════════════════
# PROTOCOLLI A FASI (PHASED PROTOCOLS)
# ═════════════════════════════════════════════════════════════════════════════

PHASED_PROTOCOLS = {
    "ibs": {
        "elimination": {
            "duration_weeks": "4-8",
            "description": (
                "Fase 1: Eliminazione completa dei FODMAP. "
                "Ridurre fruttosio, lattosio, fruttani, galattani, polialcoli. "
                "Durata: 4-8 settimane; non oltre 8 settimane per rischio carenze."
            )
        },
        "reintroduction": {
            "duration_weeks": "6-8",
            "description": (
                "Fase 2: Reinserimento graduale di un gruppo FODMAP alla volta "
                "(6-7 giorni per gruppo). Testare tolleranza individuale. "
                "Priorità: fruttani, galattani, fruttosio, lattosio, polialcoli."
            )
        },
        "maintenance": {
            "description": (
                "Fase 3: Personalizzazione basata sulla tolleranza individuale. "
                "Mantenere il minor numero di restrizioni possibile. "
                "Rivalutare ogni 6-12 mesi con professionista."
            )
        }
    },
    "sibo": {
        "elimination": {
            "duration_weeks": "2-4",
            "description": (
                "Dieta elementare o semi-elementare per 2 settimane "
                "(riduce substrato fermentabile). "
                "Alternativa: low-FODMAP stretta per 3-4 settimane. "
                "Contemporaneamente: trattamento antibiotico/probiotico."
            )
        },
        "reintroduction": {
            "duration_weeks": "4-6",
            "description": (
                "Reintro graduale di carboidrati complessi. "
                "Iniziare con amidi raffinati (riso, patate). "
                "Aggiungere gradualmente verdure, frutta, legumi. "
                "Monitorare sintomi (gonfiore, dolore, altered bowel habits)."
            )
        },
        "maintenance": {
            "description": (
                "Procinetici per prevenire recidive. "
                "Spaziatura pasti 3-4 ore. "
                "Digiuno notturno 12h. "
                "Monitoraggio periodico con breath test."
            )
        }
    },
    "histamine_intolerance": {
        "elimination": {
            "duration_weeks": "2-4",
            "description": (
                "Dieta low-histamine stretta per 2-4 settimane. "
                "Eliminare tutti gli alimenti con istamina elevata e rilascianti. "
                "Mangiare solo cibo fresco cucinato immediatamente."
            )
        },
        "reintroduction": {
            "duration_weeks": "4-8",
            "description": (
                "Reintro di un alimento alla volta ogni 3-4 giorni. "
                "Testare prima gli alimenti a basso rischio (frutta fresca non tropicale). "
                "Documentare soglia individuale per ogni alimento."
            )
        },
        "maintenance": {
            "description": (
                "Mantenere sotto la soglia individuale. "
                "Sempre cibo fresco, cucinato al momento. "
                "Attenzione a leftovers (>24h = rischio). "
                "Integratori DAO/fitici come supporto."
            )
        }
    },
    "food_allergy": {
        "elimination": {
            "duration_weeks": "permanente",
            "description": (
                "Eliminazione permanente dell'allergene identificato. "
                "Non esiste fase di reintroduzione per allergia IgE-verificata. "
                "Lettura sistematica delle etichette. "
                "Adrenalina auto-iniettabile disponibile (se anafilassi)."
            )
        },
        "reintroduction": {
            "duration_weeks": "N/A",
            "description": (
                "Nessuna reintroduzione senza valutazione allergologica. "
                "In caso di desensibilizzazione orale (OIT): solo in ambiente ospedaliero."
            )
        },
        "maintenance": {
            "description": (
                "Evitamento permanente. "
                "Verifica periodica con allergologo. "
                "Sostituzione nutrizionale dell'allergene eliminato."
            )
        }
    },
    "eoe": {
        "elimination": {
            "duration_weeks": "6",
            "description": (
                "4FED (Four Food Elimination Diet) per 6 settimane: "
                "eliminare latte vaccino, soia, grano/glutine, uovo. "
                "Monitorare sintomi. Endoscopia di controllo dopo 6 settimane."
            )
        },
        "reintroduction": {
            "duration_weeks": "3",
            "description": (
                "Reintro di un alimento ogni 3 settimane (ordine: latte, soia, uovo, grano). "
                "Se sintomi ricompaiono, eliminare l'albero e continuare con il prossimo. "
                "Endoscopia dopo ogni reintroduzione positiva."
            )
        },
        "maintenance": {
            "description": (
                "Dieta personalizzata trigger-free basata sui risultati. "
                "Monitoraggio endoscopico periodico. "
                "Alcuni pazienti necessitano terapia farmacologica (PPI, corticosteroidi topici)."
            )
        }
    },
    "kidney_stones": {
        "elimination": {
            "duration_weeks": "cronica",
            "description": (
                "Protocollo cronico, non a fasi temporali. "
                "Idratazione ≥2L/giorno permanente. "
                "Limitare ossalati alimentari. "
                "Calcio con i pasti (900-1200 mg/day)."
            )
        },
        "reintroduction": {
            "duration_weeks": "N/A",
            "description": (
                "Non applicabile - il protocollo è continuativo. "
                "Eventuale reintroduzione graduale di alimenti ossalati "
                "solo dopo stabilizzazione e con monitoraggio."
            )
        },
        "maintenance": {
            "description": (
                "Mantenere idratazione adeguata (urine chiaro-palestrina). "
                "Calcio con pasti. "
                "Ridurre sodio (<2300 mg/day). "
                "Proteine moderate. "
                "Citrato (limone, agrumi) per alcalinizzazione urine."
            )
        }
    },
    "ibd": {
        "elimination": {
            "duration_weeks": "6-8",
            "description": (
                "Induzione remissione: EEN (nutrizione enterale esclusiva) 6-8 settimane "
                "OPPURE CDED (Crohn's Disease Exclusion Diet) fase 1-2 con PEN parziale. "
                "In fase acuta ridurre la fibra insolubile (crusca, verdure crude, bucce, semi). "
                "Eliminare emulsionanti/additivi e cibi ultra-processati."
            )
        },
        "reintroduction": {
            "duration_weeks": "6-12",
            "description": (
                "Reintroduzione graduale del cibo (partial enteral nutrition → dieta completa). "
                "Reinserire fibra solubile, poi verdure cotte, poi progressivamente crude. "
                "Monitorare calprotectina fecale e sintomi ad ogni step."
            )
        },
        "maintenance": {
            "description": (
                "Mantenimento in remissione: pattern mediterraneo anti-infiammatorio, "
                "ricco di fibre solubili, omega-3 e polifenoli. "
                "Evitare emulsionanti e ultra-processati. "
                "Correggere carenze (ferro, B12, vitamina D, folati). "
                "Colite ulcerosa: considerare VSL#3 / E. coli Nissle."
            )
        }
    }
}


# ═════════════════════════════════════════════════════════════════════════════
# PATTERN DIETETICI EVIDENCE-BASED (non legati a una singola condizione)
# Diete "orizzontali" utilizzabili come cornice per più condizioni.
# ═════════════════════════════════════════════════════════════════════════════

DIET_PATTERNS = {
    "mediterranean": {
        "name": "Dieta Mediterranea",
        "goal": "Salute cardiovascolare, anti-infiammatoria, longevità",
        "description": (
            "Alta in verdura, frutta, legumi, cereali integrali, olio EVO, frutta secca "
            "e pesce; moderata in latticini e pollame; bassa in carne rossa/processata e zuccheri."
        ),
        "evidence": (
            "Evidenza di massimo livello: riduce eventi cardiovascolari, diabete t2 e "
            "mortalità; base delle linee guida AHA/ACC 2026 e ADA 2026. Efficace anche "
            "in MASLD, endometriosi, PCOS, IBD (mantenimento)."
        ),
        "applies_to": ["hypertension", "diabetes_t2", "masld", "endometriosis", "pcos", "ibd", "obesity"],
        "fonti": [
            "AHA/ACC (2026) - Dietary Guidance to Improve Cardiovascular Health (CIR.0000000000001435)",
            "ADA Standards of Care (2026) - eating patterns for T2D prevention"
        ]
    },
    "dash": {
        "name": "DASH (Dietary Approaches to Stop Hypertension)",
        "goal": "Riduzione della pressione arteriosa",
        "description": (
            "Ricca in frutta, verdura e latticini magri; povera di sodio (<2300 mg, "
            "idealmente <1500 mg), grassi saturi e zuccheri. Enfasi su potassio, magnesio, calcio, fibra."
        ),
        "evidence": (
            "Riduce la sistolica di 1-13 mmHg e la diastolica di 1-10 mmHg entro poche "
            "settimane, indipendentemente dal calo di peso (linee guida AHA/ACC 2025 ipertensione). "
            "Riduce anche colesterolo totale/LDL (Zare 2025)."
        ),
        "applies_to": ["hypertension", "diabetes_t2", "obesity", "masld"],
        "fonti": [
            "2025 AHA/ACC Hypertension Guideline (HYP.0000000000000249)",
            "Zare P et al. (2025) - DASH & lipid profile meta-analysis"
        ]
    },
    "mind": {
        "name": "MIND (Mediterranean-DASH Intervention for Neurodegenerative Delay)",
        "goal": "Prevenzione del declino cognitivo",
        "description": (
            "Ibrido Mediterranea+DASH con enfasi su verdure a foglia verde, frutti di "
            "bosco (berries), noci, olio EVO, pesce, legumi, cereali integrali; limita "
            "carne rossa, burro/margarina, formaggi, dolci e fritti."
        ),
        "evidence": (
            "Associata a declino cognitivo più lento (cognitive age ~7.5 anni più giovane "
            "nel tertile alto; Morris 2015 MAP) e minore patologia amiloide; evidenza "
            "osservazionale forte, RCT misti (systematic review CNR 2025)."
        ),
        "applies_to": [],
        "fonti": [
            "Morris MC et al. (2015) - MIND diet slows cognitive decline (MAP cohort)",
            "Systematic review (Clin Nutr Res 2025 14:318) - MIND & cognition in older adults"
        ]
    },
    "portfolio": {
        "name": "Portfolio Diet",
        "goal": "Riduzione del colesterolo LDL",
        "description": (
            "Pattern plant-based che combina 4 elementi cardioprotettivi: proteine "
            "vegetali (soia, legumi), fibra viscosa (avena, orzo, psyllium), frutta secca "
            "e steroli vegetali."
        ),
        "evidence": (
            "Riduce LDL e marker cardiovascolari; utile in dislipidemia e DM2 (glycemicindex.com 2025)."
        ),
        "applies_to": ["hypertension", "diabetes_t2", "masld"],
        "fonti": [
            "Portfolio Diet for T2D (2025) - LDL & cardiovascular risk"
        ]
    },
    "low_gi": {
        "name": "Dieta a Basso Indice / Carico Glicemico",
        "goal": "Controllo glicemico e insulino-resistenza",
        "description": (
            "Predilige carboidrati a basso indice glicemico (legumi, cereali integrali, "
            "verdura) e ad alto contenuto di fibra; limita zuccheri e amidi raffinati."
        ),
        "evidence": (
            "Diete ad alto IG/GL associate a rischio maggiore di DM2 (HR 1.15-1.21, "
            "PURE 2024, >127k soggetti); benefici sul controllo cardiometabolico simili "
            "a fibra/cereali integrali."
        ),
        "applies_to": ["diabetes_t2", "pcos", "obesity", "masld"],
        "fonti": [
            "PURE study (Lancet Diab Endo 2024) - GI/GL & incident T2D",
            "GI/GL meta-analysis mega-cohorts (>100k participants)"
        ]
    },
    "rpah_failsafe": {
        "name": "RPAH / FAILSAFE (Elimination of Food Chemicals)",
        "goal": "Intolleranze ai chimici alimentari (salicilati, amine, glutammati)",
        "description": (
            "Dieta di eliminazione dei chimici alimentari naturali e additivi: "
            "salicilati, amine biogene, glutammati (MSG), oltre a coloranti/conservanti. "
            "Fase di eliminazione stretta seguita da challenge sistematici per identificare i trigger."
        ),
        "evidence": (
            "Elevata frequenza di miglioramento (~88%) con dieta low-food-chemical in "
            "pazienti con sintomi multipli (cefalea, prurito, sintomi GI); i salicilati "
            "sono il trigger più comune (J Hum Nutr Diet 2024). Richiede supervisione dietetica."
        ),
        "applies_to": ["mcas", "histamine_intolerance"],
        "phases": {
            "elimination": "3-6 settimane di dieta a bassissimo contenuto di chimici alimentari",
            "challenge": "Challenge separati per salicilati, amine, glutammati (uno alla volta, con wash-out)",
            "maintenance": "Dieta personalizzata sotto la soglia individuale per ciascun chimico"
        },
        "fonti": [
            "RPAH Allergy Unit - Elimination Diet Handbook",
            "J Hum Nutr Diet (2024) - low food-chemical diet & symptom improvement"
        ]
    },
    "gut_barrier_support": {
        "name": "Supporto Barriera Intestinale ('leaky gut')",
        "goal": "Rinforzo della barriera epiteliale e delle tight junctions",
        "description": (
            "Approccio NUTRIZIONALE di supporto (NON un test diagnostico): la zonulina "
            "come biomarcatore NON è validata. Enfasi su nutrienti che sostengono la "
            "barriera: glutammina, zinco, vitamina D, butirrato/SCFA e amido resistente "
            "(che nutre i batteri produttori di butirrato), polifenoli."
        ),
        "evidence": (
            "Vitamina D e glutammina migliorano l'integrità della barriera; il butirrato "
            "rinforza le tight junctions (Nutrients 2023; Nature 2025). L'assay della "
            "zonulina è metodologicamente criticato e NON va usato per la diagnosi."
        ),
        "applies_to": ["ibd", "ibs", "dysbiosis", "sibo"],
        "supports": [
            "Glutammina (5 g 1-2x/die)",
            "Zinco (carnosina) — integrità mucosa",
            "Vitamina D (secondo livelli)",
            "Butirrato / amido resistente (banana verde, patata raffreddata, legumi)",
            "Polifenoli (tè verde, frutti di bosco, olio EVO)"
        ],
        "fonti": [
            "Nutrients (2023) - intestinal permeability, zonulin assay limitations",
            "Nature (2025) / PMC (2026) - butyrate/SCFA & gut barrier"
        ]
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# FUNZIONI DI UTILITÀ
# ─────────────────────────────────────────────────────────────────────────────

def normalize_condition_keys(conditions):
    """
    Normalizza una lista/stringa di condizioni nel formato chiave canonico
    (lowercase, con underscore). Accetta sia stringhe CSV sia liste.
    """
    if conditions is None:
        return []
    if isinstance(conditions, str):
        conditions = [c.strip() for c in conditions.split(",") if c.strip()]
    out = []
    for c in conditions:
        if not c:
            continue
        key = c.strip().lower().replace(" ", "_").replace("-", "_")
        out.append(key)
    return out


def parse_pathologies(raw):
    """
    SINGLE SOURCE OF TRUTH per leggere le condizioni cliniche del cliente.

    Il campo `pathologies` del DB puo' arrivare in due formati storicamente
    divergenti:
      1) stringa CSV  -> "sibo, ibs, histamine_intolerance"
      2) JSON dict    -> '{"clinical_conditions": ["sibo","ibs"], "anamnesis_notes": "..."}'
                         (salvato da /api/clients/{cid}/anamnesis)

    Ritorna sempre {'conditions': [...], 'notes': str} in modo uniforme,
    cosi' il resto dell'app non deve piu' gestire il formato.
    """
    if not raw:
        return {"conditions": [], "notes": ""}
    if isinstance(raw, dict):
        return {
            "conditions": normalize_condition_keys(raw.get("clinical_conditions", [])),
            "notes": raw.get("anamnesis_notes", "") or ""
        }
    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                data = json.loads(s)
                if isinstance(data, dict):
                    return {
                        "conditions": normalize_condition_keys(data.get("clinical_conditions", [])),
                        "notes": data.get("anamnesis_notes", "") or ""
                    }
                if isinstance(data, list):
                    return {"conditions": normalize_condition_keys(data), "notes": ""}
            except Exception:
                pass
        # stringa CSV
        return {"conditions": normalize_condition_keys(s), "notes": ""}
    if isinstance(raw, list):
        return {"conditions": normalize_condition_keys(raw), "notes": ""}
    return {"conditions": [], "notes": ""}


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


# ═════════════════════════════════════════════════════════════════════════════
# FUNZIONI AVANZATE — Conflitti, Integratori, Protocolli, FODMAP
# ═════════════════════════════════════════════════════════════════════════════

def get_condition_conflicts(condition_keys):
    """
    Analizza una lista di condizioni e ritorna i conflitti trovati.

    Args:
        condition_keys: lista di chiavi condizione (es. ['ibs', 'sibo'])

    Returns:
        Lista di stringhe con i warning di conflitto.
    """
    warnings = []
    condition_set = set(condition_keys)

    for pair, message in CONDITION_CONFLICTS.items():
        # Controlla se entrambe le condizioni della coppia sono presenti
        if pair[0] in condition_set and pair[1] in condition_set:
            warnings.append(message)
        # Controlla anche l'ordine invertito (il dizionario potrebbe avere solo un ordine)
        elif pair[1] in condition_set and pair[0] in condition_set:
            warnings.append(message)

    return warnings


def get_supplements(condition_keys):
    """
    Fonde gli integratori per più condizioni, segnalando duplicati.

    Args:
        condition_keys: lista di chiavi condizione

    Returns:
        Dict con:
          - 'all': lista completa di integratori (con campo 'conditions' aggiunto)
          - 'duplicates': lista di nomi duplicati con le condizioni
          - 'unique': lista senza duplicati (prima occorrenza)
    """
    all_supplements = []
    seen = {}  # name -> [conditions]

    for k in condition_keys:
        supps = SUPPLEMENTS.get(k, [])
        for s in supps:
            supp_copy = dict(s)
            supp_copy["condition"] = k
            supp_copy["condition_name"] = CLINICAL_CONDITIONS.get(k, {}).get("name", k)
            all_supplements.append(supp_copy)

            name_lower = s["name"].lower().strip()
            if name_lower not in seen:
                seen[name_lower] = []
            seen[name_lower].append(k)

    # Trova duplicati
    duplicates = []
    for name, conds in seen.items():
        if len(conds) > 1:
            cond_names = [CLINICAL_CONDITIONS.get(c, {}).get("name", c) for c in conds]
            duplicates.append({
                "name": name,
                "conditions": conds,
                "condition_names": cond_names,
                "message": (
                    f"⚠️ Integratore '{name}' raccomandato per: "
                    f"{', '.join(cond_names)}. Verificare dosaggio totale."
                )
            })

    # Unici (prima occorrenza per ogni nome)
    unique = []
    seen_names = set()
    for s in all_supplements:
        name_lower = s["name"].lower().strip()
        if name_lower not in seen_names:
            seen_names.add(name_lower)
            unique.append(s)

    return {
        "all": all_supplements,
        "duplicates": duplicates,
        "unique": unique
    }


def get_phased_protocol(condition_key):
    """
    Ritorna il protocollo a fasi per una condizione.

    Args:
        condition_key: chiave della condizione (es. 'ibs', 'sibo')

    Returns:
        Dict con chiavi 'elimination', 'reintroduction', 'maintenance' oppure None.
    """
    protocol = PHASED_PROTOCOLS.get(condition_key)
    if protocol:
        return {
            "condition": CLINICAL_CONDITIONS.get(condition_key, {}).get("name", condition_key),
            "elimination": protocol["elimination"],
            "reintroduction": protocol["reintroduction"],
            "maintenance": protocol["maintenance"]
        }
    return None


def get_all_diet_patterns():
    """Ritorna tutti i pattern dietetici evidence-based (Mediterranea, DASH, MIND, ...)."""
    return {k: {"name": v["name"], "goal": v["goal"]} for k, v in DIET_PATTERNS.items()}


def get_diet_pattern(pattern_key):
    """Ritorna il dettaglio completo di un pattern dietetico, o None."""
    return DIET_PATTERNS.get(pattern_key)


def get_diet_patterns_for_conditions(condition_keys):
    """
    Suggerisce i pattern dietetici rilevanti per una o più condizioni.

    Args:
        condition_keys: lista di chiavi condizione (es. ['diabetes_t2', 'masld'])

    Returns:
        Lista di dict {key, name, goal, evidence} ordinata per numero di match.
    """
    if isinstance(condition_keys, str):
        condition_keys = [condition_keys]
    cset = set(condition_keys)
    results = []
    for key, pattern in DIET_PATTERNS.items():
        matches = cset & set(pattern.get("applies_to", []))
        if matches:
            results.append({
                "key": key,
                "name": pattern["name"],
                "goal": pattern["goal"],
                "evidence": pattern["evidence"],
                "matched_conditions": sorted(matches),
                "match_count": len(matches)
            })
    results.sort(key=lambda x: x["match_count"], reverse=True)
    return results


def calculate_fodmap_load(food_items):
    """
    Calcola il carico FODMAP stimato per una lista di alimenti.

    Args:
        food_items: lista di tuple (nome_alimento, grammi)
                    es. [("mela", 200), ("riso bianco", 150)]

    Returns:
        Dict con:
          - 'total_fodmap_g': totale FODMAP stimato in grammi
          - 'breakdown': dict con grammi per gruppo FODMAP
          - 'high_fodmap_items': lista di alimenti con alto carico
          - 'low_fodmap_items': lista di alimenti a basso carico
          - 'items_detail': dettaglio per ogni alimento
    """
    # Database FODMAP per 100g (dai dati Monash University e letteratura)
    # Formato: {nome_alimento: {fructans_g, gos_g, lactose_g, sorbitol_g, mannitol_g, fructose_g}}
    FOOD_FODMAP = {
        # Frutta
        "mela": {"fructans_g": 0.09, "sorbitol_g": 0.53, "fructose_g": 0.35, "fructose_excess_g": 0.15},
        "pere": {"fructans_g": 0.06, "sorbitol_g": 0.34, "fructose_g": 0.38, "fructose_excess_g": 0.15},
        "mele": {"fructans_g": 0.09, "sorbitol_g": 0.53, "fructose_g": 0.35, "fructose_excess_g": 0.15},
        "mango": {"fructose_g": 0.63, "fructose_excess_g": 0.50},
        "anguria": {"fructose_g": 0.15, "fructose_excess_g": 0.10},
        "fragole": {"fructose_g": 0.24, "fructose_excess_g": 0.10},
        "kiwi": {"fructose_g": 0.23, "fructose_excess_g": 0.08},
        "banane": {"sorbitol_g": 0.15, "fructose_g": 0.08},
        "mirtilli": {"fructans_g": 0.04, "fructose_g": 0.21},
        "arance": {"fructose_g": 0.14, "fructose_excess_g": 0.06},
        "limoni": {"fructose_g": 0.15, "fructose_excess_g": 0.08},
        "uva": {"fructose_g": 0.12, "fructose_excess_g": 0.07},
        "ananas": {"fructose_g": 0.15, "fructose_excess_g": 0.08},
        "papaya": {"fructose_g": 0.10, "fructose_excess_g": 0.05},
        "pomelo": {"fructose_g": 0.12, "fructose_excess_g": 0.06},
        "mandarini": {"fructose_g": 0.14, "fructose_excess_g": 0.07},
        "clementine": {"fructose_g": 0.14, "fructose_excess_g": 0.07},
        # Verdura
        "aglio": {"fructans_g": 1.40},
        "cipolla": {"fructans_g": 0.94},
        "cipolle": {"fructans_g": 0.94},
        "porri": {"fructans_g": 0.70},
        "cavolfiore": {"fructans_g": 0.15, "sorbitol_g": 0.21, "mannitol_g": 0.11},
        "broccoli": {"fructans_g": 0.12},
        "zucchine": {"sorbitol_g": 0.07, "mannitol_g": 0.04},
        "carote": {"fructose_g": 0.03, "fructose_excess_g": 0.02},
        "patate": {},
        "pomodori": {"fructose_g": 0.14, "fructose_excess_g": 0.08},
        "spinaci": {"fructans_g": 0.04, "mannitol_g": 0.04},
        "melanzane": {},
        "peperoni": {},
        "cetrioli": {},
        "lattuga": {"fructans_g": 0.02},
        "sedano": {"mannitol_g": 0.04},
        "asparagi": {"fructans_g": 0.18, "mannitol_g": 0.15},
        "cavolo": {"fructans_g": 0.10},
        "cavolo rosso": {"fructans_g": 0.12},
        "fagiolini": {"mannitol_g": 0.06},
        "piselli": {"gos_g": 0.15},
        "mais": {},
        # Cereali
        "riso bianco": {},
        "riso": {},
        "riso integrale": {"fructans_g": 0.15},
        "avena": {"fructans_g": 0.20},
        "pane": {"fructans_g": 0.22},
        "pane integrale": {"fructans_g": 0.31},
        "pasta": {"fructans_g": 0.15},
        "pasta integrale": {"fructans_g": 0.25},
        "orzo": {"fructans_g": 0.30},
        "segale": {"fructans_g": 0.35},
        "quinoa": {},
        "cous cous": {"fructans_g": 0.18},
        # Legumi (alto FODMAP)
        "lenticchie": {"gos_g": 0.56, "fructans_g": 0.15},
        "fagioli": {"gos_g": 0.44, "fructans_g": 0.18},
        "ceci": {"gos_g": 0.38, "fructans_g": 0.15},
        "fagioli neri": {"gos_g": 0.40, "fructans_g": 0.16},
        "soia": {"gos_g": 0.35},
        "tofu": {"gos_g": 0.05},
        "edamame": {"gos_g": 0.25},
        # Latticini
        "latte": {"lactose_g": 4.70},
        "latte vaccino": {"lactose_g": 4.70},
        "latte intero": {"lactose_g": 4.70},
        "yogurt": {"lactose_g": 1.80},
        "gelato": {"lactose_g": 1.40},
        "panna": {"lactose_g": 2.50},
        "formaggio bianco": {"lactose_g": 2.50},
        "ricotta": {"lactose_g": 3.00},
        "mozzarella": {"lactose_g": 0.10},
        "parmigiano": {"lactose_g": 0.0},
        "formaggi stagionati": {"lactose_g": 0.0},
        "burro": {"lactose_g": 0.10},
        "yogurt greco": {"lactose_g": 1.00},
        # Noci e semi
        "noci": {"gos_g": 0.15, "fructans_g": 0.05},
        "mandorle": {"gos_g": 0.10},
        "nocciole": {"gos_g": 0.12},
        "semi di girasole": {},
        "semi di lino": {},
        "semi di chia": {},
        # Altro
        "miele": {"fructose_g": 0.69, "fructose_excess_g": 0.40},
        "sciroppo d'agave": {"fructose_g": 1.30, "fructose_excess_g": 1.10},
        "dolcificanti": {"sorbitol_g": 1.00, "mannitol_g": 1.00},
        "xilitolo": {"sorbitol_g": 1.00},
        "sorbitolo": {"sorbitol_g": 1.00},
        "mannitolo": {"mannitol_g": 1.00},
    }

    total_fodmap = 0.0
    breakdown = {
        "fructans_g": 0.0,
        "gos_g": 0.0,
        "lactose_g": 0.0,
        "sorbitol_g": 0.0,
        "mannitol_g": 0.0,
        "fructose_g": 0.0,
        "fructose_excess_g": 0.0
    }
    high_fodmap_items = []
    low_fodmap_items = []
    items_detail = []

    for food_name, grams in food_items:
        food_lower = food_name.lower().strip()
        grams_factor = grams / 100.0

        # Cerca nel database (corrispondenza esatta o parziale)
        fodmap_data = FOOD_FODMAP.get(food_lower)
        if fodmap_data is None:
            # Prova corrispondenza parziale
            for key in FOOD_FODMAP:
                if key in food_lower or food_lower in key:
                    fodmap_data = FOOD_FODMAP[key]
                    break

        if fodmap_data is None:
            # Alimento non trovato, assume basso FODMAP
            items_detail.append({
                "food": food_name,
                "grams": grams,
                "fodmap_g": 0.0,
                "status": "non_database"
            })
            low_fodmap_items.append({"food": food_name, "grams": grams})
            continue

        # Calcola FODMAP per questa porzione
        food_fodmap = 0.0
        food_breakdown = {}
        for group, value in fodmap_data.items():
            grams_val = value * grams_factor
            food_breakdown[group] = round(grams_val, 3)
            if group in breakdown:
                breakdown[group] += grams_val
            food_fodmap += grams_val

        food_fodmap = round(food_fodmap, 3)
        total_fodmap += food_fodmap

        detail = {
            "food": food_name,
            "grams": grams,
            "fodmap_g": food_fodmap,
            "breakdown": food_breakdown,
            "status": "alto" if food_fodmap > 0.5 else ("medio" if food_fodmap > 0.1 else "basso")
        }
        items_detail.append(detail)

        if food_fodmap > 0.5:
            high_fodmap_items.append({"food": food_name, "grams": grams, "fodmap_g": food_fodmap})
        else:
            low_fodmap_items.append({"food": food_name, "grams": grams, "fodmap_g": food_fodmap})

    # Arrotonda il totale
    total_fodmap = round(total_fodmap, 3)
    for k in breakdown:
        breakdown[k] = round(breakdown[k], 3)

    return {
        "total_fodmap_g": total_fodmap,
        "breakdown": breakdown,
        "high_fodmap_items": high_fodmap_items,
        "low_fodmap_items": low_fodmap_items,
        "items_detail": items_detail
    }


# ═════════════════════════════════════════════════════════════════
# AI PATTERN DETECTION DAL DIARIO SINTOMI (loop chiuso piano→diario→piano)
# ═════════════════════════════════════════════════════════════════

# Ordine di reintroduzione FODMAP raccomandato (Monash University / King's College London):
# si inizia dai gruppi meglio tollerati, un gruppo alla volta, 3 giorni per alimento.
FODMAP_REINTRODUCTION_ORDER = [
    {"group": "fructans_vegetables", "label": "Fruttani (verdura)",
     "test_foods": ["scalogno (1/2 cucchiaino polvere)", "aglio (1/8 spicchio)", "porro (solo parte verde)"],
     "rationale": "Spesso i piu' tollerati all'inizio dell challenge."},
    {"group": "fructans_grains", "label": "Fruttani (cereali)",
     "test_foods": ["frumento (1 fetta pane)", "segale (1 fetta)"],
     "rationale": "Dose dipendente; testare porzioni modeste."},
    {"group": "galacto_oligos", "label": "GOS (legumi)",
     "test_foods": ["lenticchie (1/4 tazza)", "ceci (1/4 tazza)", "fagioli (1/4 tazza)"],
     "rationale": "Gas/fermentazione tipici; valutare tolleranza progressiva."},
    {"group": "polyols_sorbitol", "label": "Polioli (sorbitolo)",
     "test_foods": ["mela (1/2)", "pera (1/2)", "prugna (1)"],
     "rationale": "Effetto osmotico marcato; testare separatamente da mannitolo."},
    {"group": "polyols_mannitol", "label": "Polioli (mannitolo)",
     "test_foods": ["funghi (1/2 tazza)", "cavolfiore (1/2 tazza)"],
     "rationale": "Separato da sorbitolo per isolare il trigger."},
    {"group": "lactose", "label": "Lattosio",
     "test_foods": ["latte (1 bicchiere)", "yogurt (1 vasetto)"],
     "rationale": "Deficit lattasi molto comune; spesso ben tollerato in piccole dosi."},
    {"group": "fructose_excess", "label": "Fruttosio in eccesso",
     "test_foods": ["mango (1/2)", "ciliegie (10)", "melata (1 cucchiaino)"],
     "rationale": "Testare per ultimo: fruttosio in eccesso e' il piu' difficile da tollerare."},
]


def detect_symptom_patterns(symptoms, threshold=2):
    """
    Rileva pattern dai log sintomi del cliente.

    Args:
        symptoms: lista di dict con chiavi bloating/pain/gas/nausea/heartburn/
                  constipation/diarrhea/brain_fog/fatigue (scale 0-4) e foods_eaten.
        threshold: severita' minima (0-4) considerata "evento rilevante".

    Returns:
        dict con:
          - avg_symptoms: medie per sintomo
          - top_symptoms: sintomi piu' frequenti/severi
          - high_days: numero di giorni con sintomi rilevanti
          - food_hypotheses: se foods_eaten presente, alimenti citati nei giorni
                              a sintomi alti (candidati trigger)
    """
    if not symptoms:
        return {"avg_symptoms": {}, "top_symptoms": [], "high_days": 0, "food_hypotheses": []}
    sym_keys = ["bloating", "pain", "gas", "nausea", "heartburn",
                "constipation", "diarrhea", "brain_fog", "fatigue"]
    sums = {k: 0 for k in sym_keys}
    counts = {k: 0 for k in sym_keys}
    high_days = 0
    food_high = {}
    for s in symptoms:
        day_max = 0
        for k in sym_keys:
            v = s.get(k) or 0
            sums[k] += v
            if v > 0:
                counts[k] += 1
            day_max = max(day_max, v)
        if day_max >= threshold:
            high_days += 1
            foods = s.get("foods_eaten") or ""
            if foods:
                for f in [x.strip().lower() for x in foods.replace(",", " ").split() if x.strip()]:
                    food_high[f] = food_high.get(f, 0) + 1
    n = len(symptoms)
    avg = {k: round(sums[k] / n, 2) for k in sym_keys if sums[k] > 0}
    sorted_sym = sorted(((k, sums[k]) for k in sym_keys if sums[k] > 0),
                        key=lambda x: x[1], reverse=True)
    top = [k for k, _ in sorted_sym[:3]]
    food_hyp = sorted(food_high.items(), key=lambda x: x[1], reverse=True)[:8]
    return {
        "avg_symptoms": avg,
        "top_symptoms": top,
        "high_days": high_days,
        "total_days": n,
        "food_hypotheses": [{"food": f, "hits": c} for f, c in food_hyp]
    }


def fodmap_reintroduction_plan(start_group_index=0):
    """
    Ritorna il piano di reintroduzione FODMAP guidato (ordine Monash),
    a partire dal gruppo indicato.
    """
    steps = FODMAP_REINTRODUCTION_ORDER[start_group_index:]
    return {
        "method": "Un gruppo alla volta, un alimento alla volta. 3 giorni di test, "
                  "poi 3-4 giorni di wash-out (dieta low-FODMAP) prima del gruppo successivo. "
                  "Annotare sintomi 0-4 entro 24h.",
        "steps": steps
    }


def suggest_next_reintroduction(client_phases, symptoms):
    """
    Suggerisce il prossimo passo di reintroduzione FODMAP in base alla fase
    registrata e ai sintomi recenti.

    Args:
        client_phases: lista di dict {condition_key, phase, ...} da get_diet_phases
        symptoms: lista log sintomi recenti

    Returns:
        dict {ready, reason, next_step}
    """
    # determina se il cliente e' in fase di eliminazione low-FODMAP
    fodmap_phase = None
    for p in (client_phases or []):
        if p.get("condition_key") in ("ibs", "sibo", "histamine_intolerance", "dysbiosis"):
            fodmap_phase = p.get("phase")
    if fodmap_phase and fodmap_phase not in ("elimination", "reintroduction", "maintenance"):
        fodmap_phase = None
    # pattern sintomi
    pat = detect_symptom_patterns(symptoms, threshold=2)
    if fodmap_phase in ("reintroduction", "maintenance"):
        return {"ready": True,
                "reason": f"Fase '{fodmap_phase}' gia' avviata.",
                "next_step": fodmap_reintroduction_plan(0)}
    if fodmap_phase == "elimination":
        if pat["high_days"] == 0:
            return {"ready": True,
                    "reason": "In eliminazione e sintomi sotto soglia: puoi iniziare la reintroduzione.",
                    "next_step": fodmap_reintroduction_plan(0)}
        return {"ready": False,
                "reason": f"Ancora sintomi rilevanti in {pat['high_days']}/{pat['total_days']} giorni: "
                          "continua l'eliminazione low-FODMAP prima di introdurre FODMAP.",
                "next_step": None}
    # nessuna fase FODMAP registrata
    if pat["top_symptoms"]:
        return {"ready": pat["high_days"] == 0,
                "reason": "Nessuna fase FODMAP registrata; sintomi rilevanti rilevati: "
                          + ", ".join(pat["top_symptoms"]) + ". Valuta una fase di eliminazione low-FODMAP.",
                "next_step": fodmap_reintroduction_plan(0) if pat["high_days"] == 0 else None}
    return {"ready": False,
            "reason": "Nessuna fase dieta FODMAP registrata e pochi sintomi: non e' indicata la reintroduzione.",
            "next_step": None}
