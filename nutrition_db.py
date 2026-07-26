"""NutriCoach — Database alimenti di riferimento (valori per 100 g).

Fonti: tabelle di composizione degli alimenti INRAN (Banco dati di
composizione degli alimenti), LARN (Livelli di Assunzione di Riferimento di
Nutrienti ed energia, IV Revisione 2014, SINU) e USDA FoodData Central.
Valori medi di riferimento (kcal, proteine g, carboidrati g, grassi g,
fibre g, zuccheri g, sale g). Per gli alimenti con acqua/età diverse i
valori sono approssimati per 100 g edibili.

Interfaccia:
    nutrition_for(name, grams) -> {food, matched, kcal, p, c, f, fib, sug, salt,
                                    ca, fe, vitc, k, mg,
                                    omega3, vit_d, zinc, b12, folate, selenium,
                                    vit_a, vit_e, fodmap_total}
    search_foods(query, limit) -> [name, ...]
    food_fodmap(name) -> {fructan, gos, ...}
    food_histamine_level(name) -> 'low'|'medium'|'high'
    food_oxalate_level(name) -> 'low'|'medium'|'high'
    food_salicylate_level(name) -> 'low'|'medium'|'high'
    food_lectin_level(name) -> 'low'|'medium'|'high'
    fodmap_load(food_items) -> {total_load, by_group, flagged_items}
"""

import re

# ──────────────────────────────────────────────────────────────────────
# FOODS — (nome, kcal, proteine, carboidrati, grassi, fibre, zuccheri, sale)
# ──────────────────────────────────────────────────────────────────────
FOODS = {
    # --- LATTICINI / UOVA ---
    "uova gallina": (143, 12.6, 0.7, 9.5, 0.0, 0.4, 0.4),
    "uova di gallina": (143, 12.6, 0.7, 9.5, 0.0, 0.4, 0.4),
    "albumi d'uovo": (52, 11.0, 0.7, 0.2, 0.0, 0.4, 0.4),
    "tuorlo d'uovo": (322, 16.0, 0.6, 28.0, 0.0, 0.1, 0.1),
    "yogurt greco": (59, 10.0, 3.6, 0.4, 0.0, 3.6, 0.1),
    "yogurt bianco intero": (61, 3.5, 4.7, 3.3, 0.0, 4.7, 0.1),
    "yogurt magro": (38, 4.0, 4.7, 0.2, 0.0, 4.7, 0.1),
    "yogurt greco 0.2": (57, 10.3, 3.4, 0.2, 0.0, 3.4, 0.1),
    "yogurt greco 2": (71, 9.0, 3.8, 2.0, 0.0, 3.8, 0.1),
    "yogurt greco 5": (92, 8.6, 3.5, 5.0, 0.0, 3.5, 0.1),
    "formaggio bianco": (98, 11.0, 3.0, 4.5, 0.0, 3.0, 0.3),
    "ricotta": (174, 11.0, 3.0, 13.0, 0.0, 3.0, 0.2),
    "ricotta vaccina": (174, 11.0, 3.0, 13.0, 0.0, 3.0, 0.2),
    "mozzarella": (280, 18.0, 1.0, 22.0, 0.0, 1.0, 0.5),
    "fiordilatte": (230, 17.0, 2.5, 17.0, 0.0, 2.5, 0.4),
    "parmigiano": (392, 33.0, 0.0, 29.0, 0.0, 0.0, 1.5),
    "grana": (392, 33.0, 0.0, 29.0, 0.0, 0.0, 1.5),
    "pecorino": (380, 26.0, 0.0, 30.0, 0.0, 0.0, 1.4),
    "formaggio fresco": (98, 11.0, 3.0, 4.5, 0.0, 3.0, 0.3),
    "latte intero": (64, 3.3, 4.7, 3.6, 0.0, 4.7, 0.1),
    "latte parzialmente scremato": (49, 3.3, 4.8, 1.7, 0.0, 4.8, 0.1),
    "latte scremato": (33, 3.3, 4.9, 0.1, 0.0, 4.9, 0.1),
    "latte di soia": (43, 3.0, 2.5, 2.0, 0.0, 0.6, 0.1),
    "latte di mandorla": (17, 0.5, 0.3, 1.3, 0.4, 0.0, 0.1),
    "latte di avena": (46, 1.0, 7.0, 1.5, 0.8, 1.0, 0.1),
    "burro": (717, 0.9, 0.1, 81.0, 0.0, 0.1, 1.4),
    "philadelphia": (339, 6.0, 4.0, 34.0, 0.0, 4.0, 0.8),
    "stracchino": (243, 13.0, 1.0, 20.0, 0.0, 1.0, 0.9),
    # --- CARNI ---
    "petto di pollo": (120, 23.0, 0.0, 2.6, 0.0, 0.0, 0.1),
    "coscia di pollo": (180, 18.0, 0.0, 12.0, 0.0, 0.0, 0.1),
    "tacchino": (135, 22.0, 0.0, 5.0, 0.0, 0.0, 0.1),
    "fesa di tacchino": (99, 21.0, 0.0, 1.5, 0.0, 0.0, 0.1),
    "manzo magro": (180, 21.0, 0.0, 10.0, 0.0, 0.0, 0.1),
    "vitello": (123, 21.0, 0.0, 4.0, 0.0, 0.0, 0.1),
    "maiale magro": (145, 20.0, 0.0, 7.0, 0.0, 0.0, 0.1),
    "lonza di maiale": (143, 21.0, 0.0, 6.0, 0.0, 0.0, 0.1),
    "coniglio": (133, 21.0, 0.0, 5.0, 0.0, 0.0, 0.1),
    "agnello": (220, 17.0, 0.0, 17.0, 0.0, 0.0, 0.1),
    "bresaola": (151, 29.0, 0.0, 3.0, 0.0, 0.0, 3.5),
    "prosciutto crudo": (212, 24.0, 0.0, 12.0, 0.0, 0.0, 4.0),
    "prosciutto cotto": (114, 15.0, 1.0, 5.0, 0.0, 1.0, 2.0),
    "salame": (335, 18.0, 1.0, 28.0, 0.0, 1.0, 3.5),
    "mortadella": (287, 13.0, 2.0, 25.0, 0.0, 2.0, 2.5),
    "carpaccio": (125, 21.0, 0.0, 4.0, 0.0, 0.0, 0.1),
    "salsiccia": (280, 14.0, 1.0, 24.0, 0.0, 1.0, 2.2),
    "hamburger carne": (250, 18.0, 0.0, 20.0, 0.0, 0.0, 0.2),
    # --- PESCI / FRUTTI DI MARE ---
    "salmone": (208, 20.0, 0.0, 13.0, 0.0, 0.0, 0.1),
    "salmone affumicato": (150, 18.0, 0.0, 8.0, 0.0, 0.0, 2.5),
    "tonno": (130, 23.0, 0.0, 4.0, 0.0, 0.0, 0.1),
    "tonno in scatola": (116, 20.0, 0.0, 2.0, 0.0, 0.0, 0.6),
    "orata": (97, 18.0, 0.0, 2.5, 0.0, 0.0, 0.1),
    "spigola": (88, 17.0, 0.0, 1.8, 0.0, 0.0, 0.1),
    "merluzzo": (82, 18.0, 0.0, 0.7, 0.0, 0.0, 0.1),
    "platessa": (85, 18.0, 0.0, 1.0, 0.0, 0.0, 0.1),
    "sgombro": (205, 19.0, 0.0, 14.0, 0.0, 0.0, 0.1),
    "acciughe": (131, 17.0, 0.0, 5.0, 0.0, 0.0, 1.5),
    "gamberi": (85, 18.0, 0.2, 1.0, 0.0, 0.2, 0.4),
    "gamberetti": (85, 18.0, 0.2, 1.0, 0.0, 0.2, 0.4),
    "cozze": (86, 12.0, 4.0, 2.2, 0.0, 4.0, 0.4),
    "vongole": (54, 9.0, 2.0, 1.0, 0.0, 2.0, 0.3),
    "calamari": (80, 15.0, 2.0, 1.3, 0.0, 2.0, 0.3),
    "seppie": (76, 16.0, 1.0, 1.2, 0.0, 1.0, 0.3),
    "trota": (119, 20.0, 0.0, 4.0, 0.0, 0.0, 0.1),
    # --- CEREALI / DERIVATI ---
    "pane comune": (265, 8.0, 49.0, 2.5, 2.7, 2.0, 1.0),
    "pane di segale": (240, 8.5, 45.0, 2.0, 6.0, 2.0, 0.9),
    "pane integrale": (250, 9.0, 43.0, 3.5, 7.0, 2.0, 1.0),
    "pane di farro": (255, 8.0, 48.0, 2.5, 4.0, 1.5, 0.9),
    "pane ai cereali": (258, 9.0, 47.0, 3.0, 5.0, 2.0, 0.9),
    "cracker di segale": (410, 10.0, 62.0, 13.0, 10.0, 1.0, 1.2),
    "crackers": (460, 9.0, 65.0, 18.0, 2.5, 1.0, 1.5),
    "fette biscottate": (400, 10.0, 67.0, 10.0, 3.0, 4.0, 0.8),
    "riso basmati": (350, 7.0, 78.0, 0.9, 1.0, 0.5, 0.0),
    "riso brillato": (360, 7.0, 79.0, 0.8, 0.6, 0.2, 0.0),
    "riso integrale": (345, 7.2, 75.0, 2.8, 1.8, 0.7, 0.0),
    "riso venere": (350, 8.0, 74.0, 2.5, 2.5, 0.5, 0.0),
    "pasta": (350, 12.0, 70.0, 1.5, 3.0, 1.0, 0.0),
    "pasta di semola": (350, 12.0, 70.0, 1.5, 3.0, 1.0, 0.0),
    "pasta integrale": (345, 13.0, 64.0, 2.5, 6.0, 2.0, 0.0),
    "spaghetto": (350, 12.0, 70.0, 1.5, 3.0, 1.0, 0.0),
    "avena": (370, 13.0, 60.0, 7.0, 10.0, 1.0, 0.0),
    "fiocchi d'avena": (365, 13.0, 61.0, 6.5, 9.0, 1.0, 0.0),
    "farro": (335, 12.0, 62.0, 2.5, 8.0, 1.0, 0.0),
    "orzo": (340, 11.0, 68.0, 1.5, 7.0, 1.0, 0.0),
    "cous cous": (360, 12.0, 75.0, 1.0, 5.0, 0.5, 0.0),
    "quinoa": (368, 14.0, 64.0, 6.0, 7.0, 0.5, 0.0),
    "mais": (86, 3.3, 19.0, 1.2, 2.7, 3.0, 0.0),
    "polenta": (90, 2.0, 19.0, 0.5, 1.5, 0.0, 0.0),
    "gnocchi": (130, 3.0, 28.0, 0.5, 1.5, 0.0, 0.0),
    "pizza margherita": (250, 10.0, 33.0, 9.0, 2.0, 2.0, 1.2),
    "gallette di riso": (380, 7.0, 82.0, 2.5, 4.0, 0.5, 0.0),
    "cracker integrali": (430, 11.0, 60.0, 14.0, 9.0, 1.0, 1.0),
    # --- LEGUMI ---
    "lenticchie": (116, 9.0, 20.0, 0.4, 8.0, 1.5, 0.0),
    "ceci": (164, 8.5, 27.0, 2.6, 8.0, 1.5, 0.0),
    "fagioli": (132, 8.0, 24.0, 0.5, 8.0, 1.0, 0.0),
    "fagioli borlotti": (130, 8.0, 24.0, 0.5, 8.0, 1.0, 0.0),
    "piselli": (81, 5.4, 14.0, 0.4, 5.0, 3.0, 0.0),
    "fave": (88, 7.0, 16.0, 0.4, 8.0, 1.5, 0.0),
    "soia": (173, 16.0, 9.0, 9.0, 6.0, 2.0, 0.0),
    "tofu": (76, 8.0, 1.5, 4.8, 0.3, 0.6, 0.0),
    "hummus": (166, 7.0, 14.0, 9.6, 6.0, 0.5, 0.4),
    "ceci cotti": (164, 8.5, 27.0, 2.6, 8.0, 1.5, 0.0),
    # --- VERDURE ---
    "verdure miste": (30, 2.0, 5.0, 0.3, 3.0, 3.0, 0.0),
    "insalata mista": (17, 1.4, 2.9, 0.2, 1.3, 0.8, 0.0),
    "pomodori": (18, 0.9, 3.5, 0.2, 1.2, 2.6, 0.0),
    "pomodoro": (18, 0.9, 3.5, 0.2, 1.2, 2.6, 0.0),
    "zucchine": (17, 1.2, 3.1, 0.2, 1.0, 2.5, 0.0),
    "courgette": (17, 1.2, 3.1, 0.2, 1.0, 2.5, 0.0),
    "melanzane": (25, 1.0, 6.0, 0.2, 3.0, 3.5, 0.0),
    "peperoni": (26, 1.0, 6.0, 0.3, 2.1, 4.0, 0.0),
    "carote": (41, 0.9, 10.0, 0.2, 2.8, 5.0, 0.0),
    "broccoli": (34, 2.8, 7.0, 0.4, 2.6, 1.7, 0.0),
    "cavolfiore": (25, 1.9, 5.0, 0.3, 2.0, 2.0, 0.0),
    "spinaci": (23, 2.9, 3.6, 0.4, 2.2, 0.4, 0.0),
    "verza": (19, 1.4, 4.0, 0.2, 2.0, 2.0, 0.0),
    "cavolo": (25, 2.5, 5.0, 0.3, 3.0, 2.5, 0.0),
    "cime di rapa": (27, 3.0, 4.0, 0.4, 3.0, 0.5, 0.0),
    "asparagi": (20, 2.2, 3.9, 0.1, 2.1, 1.5, 0.0),
    "fagiolini": (31, 1.8, 7.0, 0.2, 3.4, 3.0, 0.0),
    "sedano": (16, 0.7, 3.0, 0.2, 1.6, 1.5, 0.0),
    "finocchi": (31, 1.2, 7.0, 0.2, 2.7, 3.5, 0.0),
    "cetrioli": (15, 0.7, 3.6, 0.1, 0.5, 1.7, 0.0),
    "radicchio": (13, 1.2, 2.5, 0.2, 1.0, 0.5, 0.0),
    "rucola": (25, 2.6, 3.7, 0.7, 1.6, 1.0, 0.0),
    "lattuga": (15, 1.4, 2.9, 0.2, 1.3, 0.8, 0.0),
    "cipolle": (40, 1.1, 9.3, 0.1, 1.7, 4.5, 0.0),
    "aglio": (149, 6.4, 33.0, 0.5, 2.1, 1.0, 0.0),
    "funghi": (22, 3.1, 3.3, 0.3, 1.0, 1.5, 0.0),
    "funghi champignon": (22, 3.1, 3.3, 0.3, 1.0, 1.5, 0.0),
    "porri": (61, 1.5, 14.0, 0.3, 1.8, 4.0, 0.0),
    "pomodori ciliegino": (18, 0.9, 3.5, 0.2, 1.2, 2.6, 0.0),
    "pomodori pelati": (22, 1.0, 4.5, 0.2, 1.0, 3.0, 0.0),
    "passata di pomodoro": (29, 1.4, 5.8, 0.2, 1.5, 4.0, 0.1),
    "zucca": (26, 1.0, 6.5, 0.1, 1.1, 3.0, 0.0),
    "barbabietola": (43, 1.6, 10.0, 0.2, 2.8, 7.0, 0.0),
    # --- TUBERI ---
    "patate": (77, 2.0, 17.0, 0.1, 2.2, 0.8, 0.0),
    "patate dolci": (86, 1.6, 20.0, 0.1, 3.0, 4.2, 0.0),
    # --- FRUTTA ---
    "frutta fresca": (50, 0.8, 12.0, 0.3, 2.4, 10.0, 0.0),
    "mela": (52, 0.3, 14.0, 0.2, 2.4, 11.0, 0.0),
    "pera": (57, 0.4, 15.0, 0.1, 3.1, 10.0, 0.0),
    "banana": (89, 1.1, 23.0, 0.3, 2.6, 12.0, 0.0),
    "arancia": (47, 0.9, 12.0, 0.1, 2.4, 9.0, 0.0),
    "mandarino": (53, 0.8, 13.0, 0.2, 1.8, 10.0, 0.0),
    "kiwi": (61, 1.1, 15.0, 0.5, 3.0, 9.0, 0.0),
    "fragole": (33, 0.7, 7.7, 0.3, 2.0, 5.0, 0.0),
    "uva": (69, 0.7, 18.0, 0.2, 0.9, 16.0, 0.0),
    "pesca": (39, 0.9, 10.0, 0.3, 1.5, 8.0, 0.0),
    "albicocca": (28, 0.8, 7.0, 0.1, 2.0, 6.0, 0.0),
    "melagrana": (83, 1.7, 19.0, 1.2, 4.0, 14.0, 0.0),
    "anguria": (30, 0.6, 7.6, 0.2, 0.4, 7.0, 0.0),
    "melone": (34, 0.8, 8.0, 0.2, 0.9, 8.0, 0.0),
    "ananas": (50, 0.5, 13.0, 0.1, 1.4, 10.0, 0.0),
    "limone": (29, 1.1, 9.3, 0.3, 2.8, 2.5, 0.0),
    "ciliegie": (63, 1.1, 16.0, 0.2, 2.1, 13.0, 0.0),
    "mirtilli": (57, 0.7, 14.0, 0.3, 2.4, 10.0, 0.0),
    "lamponi": (52, 1.2, 12.0, 0.7, 6.5, 4.0, 0.0),
    "fichi": (74, 0.8, 19.0, 0.3, 2.9, 16.0, 0.0),
    "prugne": (46, 0.7, 11.0, 0.3, 1.4, 10.0, 0.0),
    "frutta secca": (300, 3.0, 60.0, 4.0, 8.0, 50.0, 0.0),
    "frutta disidratata": (250, 2.5, 60.0, 1.0, 8.0, 50.0, 0.0),
    # --- FRUTTA SECCA / SEMI / OLI ---
    "mandorle": (579, 21.0, 22.0, 50.0, 12.0, 4.0, 0.0),
    "noci": (654, 15.0, 14.0, 65.0, 7.0, 2.5, 0.0),
    "nocciole": (628, 15.0, 17.0, 61.0, 10.0, 4.0, 0.0),
    "pistacchi": (562, 20.0, 28.0, 45.0, 10.0, 7.0, 0.0),
    "anacardi": (553, 18.0, 30.0, 44.0, 3.3, 5.0, 0.0),
    "arachidi": (567, 26.0, 16.0, 49.0, 8.0, 4.0, 0.0),
    "semi di girasole": (584, 21.0, 20.0, 51.0, 9.0, 2.5, 0.0),
    "semi di zucca": (559, 30.0, 11.0, 49.0, 6.0, 1.5, 0.0),
    "semi di chia": (486, 17.0, 42.0, 31.0, 34.0, 0.0, 0.0),
    "olio extravergine d'oliva": (899, 0.0, 0.0, 99.9, 0.0, 0.0, 0.0),
    "olio evo": (899, 0.0, 0.0, 99.9, 0.0, 0.0, 0.0),
    "olio di semi": (900, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0),
    "burro di arachidi": (588, 25.0, 20.0, 50.0, 6.0, 5.0, 0.4),
    "tahin": (595, 17.0, 23.0, 53.0, 9.0, 1.0, 0.1),
    "avocado": (160, 2.0, 9.0, 15.0, 7.0, 0.7, 0.0),
    # --- GRASSI / CONDIMENTI ---
    "olive": (115, 0.8, 6.0, 11.0, 3.2, 0.0, 1.0),
    "maionese": (700, 1.0, 1.0, 75.0, 0.0, 0.5, 0.8),
    "aceto balsamico": (88, 0.5, 17.0, 0.0, 0.0, 15.0, 0.0),
    "senape": (100, 5.0, 7.0, 6.0, 3.0, 2.0, 0.8),
    "ketchup": (112, 1.0, 27.0, 0.1, 0.3, 22.0, 1.0),
    "zucchero": (387, 0.0, 99.8, 0.0, 0.0, 99.8, 0.0),
    "miele": (304, 0.3, 82.0, 0.0, 0.2, 82.0, 0.0),
    "cacao amaro": (228, 20.0, 11.0, 14.0, 33.0, 1.0, 0.0),
    "cioccolato fondente": (546, 5.0, 46.0, 35.0, 11.0, 40.0, 0.1),
    "cioccolato al latte": (535, 8.0, 59.0, 30.0, 2.0, 52.0, 0.2),
    "crema di nocciole": (530, 7.0, 56.0, 32.0, 4.0, 54.0, 0.1),
    # --- DOLCI / COLAZIONE ---
    "muesli": (380, 11.0, 65.0, 8.0, 9.0, 18.0, 0.2),
    "cornflakes": (375, 7.0, 83.0, 1.0, 3.0, 8.0, 0.8),
    "cereali integrali": (360, 10.0, 68.0, 5.0, 9.0, 10.0, 0.5),
    "biscotti": (450, 7.0, 70.0, 17.0, 2.5, 25.0, 0.4),
    "fette biscottate integrali": (395, 10.0, 65.0, 9.0, 8.0, 3.0, 0.6),
    "pane proteinico": (260, 22.0, 25.0, 5.0, 12.0, 2.0, 1.0),
    "yogurt greco con miele": (80, 9.0, 8.0, 1.5, 0.0, 7.0, 0.2),
    # --- BEVANDE / INTEGRATORI ---
    "integratore proteico": (380, 80.0, 8.0, 4.0, 1.0, 2.0, 0.3),
    "whey": (380, 80.0, 8.0, 4.0, 1.0, 2.0, 0.3),
    "proteine del siero": (380, 80.0, 8.0, 4.0, 1.0, 2.0, 0.3),
    "bevanda vegetale": (40, 1.0, 7.0, 1.0, 0.5, 2.0, 0.1),
    "caffè": (2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0),
    "tè": (1, 0.0, 0.2, 0.0, 0.0, 0.2, 0.0),
    "caffè d'orzo": (320, 9.0, 60.0, 3.0, 20.0, 1.0, 0.0),
    # --- ALTRO ---
    "rizo": (350, 7.0, 78.0, 0.9, 1.0, 0.5, 0.0),
    "tortilla": (300, 8.0, 50.0, 8.0, 3.0, 1.0, 0.7),
    "wrap": (290, 9.0, 45.0, 7.0, 3.0, 1.0, 0.7),
    "pollo": (120, 23.0, 0.0, 2.6, 0.0, 0.0, 0.1),
    "ragù": (120, 9.0, 4.0, 7.0, 1.0, 2.0, 0.5),
    "sugo": (50, 1.5, 6.0, 2.0, 1.5, 4.0, 0.3),
    "pesto": (450, 5.0, 5.0, 45.0, 2.0, 1.0, 1.0),
    "formaggio": (350, 25.0, 1.0, 27.0, 0.0, 1.0, 1.2),
    "grana padano": (392, 33.0, 0.0, 29.0, 0.0, 0.0, 1.5),
    "timo": (101, 5.6, 20.0, 1.7, 14.0, 0.0, 0.0),
    "basilico": (23, 3.2, 2.6, 0.6, 1.6, 0.3, 0.0),
    "prezzemolo": (36, 3.0, 6.0, 0.8, 3.3, 0.9, 0.0),
    "origano": (265, 9.0, 69.0, 4.0, 43.0, 4.0, 0.0),
}

# ──────────────────────────────────────────────────────────────────────
# MICROS — Micronutrienti principali per 100 g
# (Ca mg, Fe mg, VitC mg, K mg, Mg mg).
# ──────────────────────────────────────────────────────────────────────
MICROS = {
    "uova gallina": (50, 1.2, 0, 126, 12), "yogurt greco": (110, 0.1, 0, 141, 11),
    "yogurt bianco intero": (121, 0.1, 0, 155, 12), "ricotta": (84, 0.4, 0, 105, 9),
    "mozzarella": (505, 0.5, 0, 76, 20), "parmigiano": (1184, 0.8, 0, 110, 38),
    "latte intero": (113, 0.1, 0, 132, 10), "latte scremato": (122, 0.1, 0, 156, 11),
    "latte di soia": (25, 0.3, 0, 118, 10), "burro": (24, 0.0, 0, 24, 2),
    "petto di pollo": (15, 1.0, 0, 256, 25), "tacchino": (12, 1.4, 0, 239, 28),
    "manzo magro": (18, 2.6, 0, 318, 21), "vitello": (18, 1.0, 0, 320, 22),
    "maiale magro": (19, 1.1, 0, 423, 22), "agnello": (17, 1.8, 0, 310, 21),
    "bresaola": (8, 2.4, 0, 440, 23), "prosciutto crudo": (9, 1.0, 0, 420, 18),
    "salmone": (12, 0.3, 0, 363, 29), "tonno": (8, 1.0, 0, 252, 27),
    "orata": (22, 0.5, 0, 310, 25), "merluzzo": (16, 0.4, 0, 340, 26),
    "sgombro": (12, 1.6, 0, 314, 76), "gamberi": (70, 1.6, 0, 220, 25),
    "cozze": (28, 6.7, 13, 320, 34), "calamari": (32, 0.7, 4, 246, 33),
    "pane comune": (150, 1.9, 0, 115, 23), "pane integrale": (150, 2.5, 0, 240, 75),
    "pane di segale": (50, 2.8, 0, 200, 40), "cracker integrali": (60, 3.0, 0, 180, 50),
    "riso basmati": (15, 1.2, 0, 115, 25), "riso integrale": (23, 1.5, 0, 223, 83),
    "pasta": (20, 1.3, 0, 58, 18), "pasta integrale": (30, 2.0, 0, 180, 70),
    "avena": (54, 4.7, 0, 429, 177), "fiocchi d'avena": (54, 4.7, 0, 429, 177),
    "farro": (27, 3.2, 0, 388, 118), "quinoa": (47, 4.6, 0, 563, 197),
    "mais": (2, 0.5, 7, 270, 37), "polenta": (2, 0.3, 0, 40, 8),
    "lenticchie": (19, 3.3, 1, 369, 36), "ceci": (35, 2.9, 1, 291, 48),
    "fagioli": (27, 2.9, 0, 405, 45), "piselli": (25, 1.5, 40, 244, 33),
    "fave": (36, 1.6, 1, 332, 33), "soia": (145, 9.1, 6, 515, 280), "tofu": (350, 5.4, 0, 121, 58),
    "verdure miste": (40, 1.0, 20, 250, 18), "insalata mista": (20, 0.5, 9, 150, 9),
    "pomodori": (10, 0.3, 14, 237, 11), "zucchine": (16, 0.4, 18, 261, 18),
    "melanzane": (9, 0.2, 2, 230, 14), "peperoni": (9, 0.4, 128, 211, 12),
    "carote": (33, 0.3, 5, 320, 12), "broccoli": (47, 0.7, 89, 316, 21),
    "cavolfiore": (22, 0.4, 48, 299, 15), "spinaci": (99, 2.7, 28, 558, 79),
    "cavolo": (40, 1.0, 41, 268, 18), "asparagi": (24, 2.1, 6, 202, 14),
    "fagiolini": (37, 1.0, 12, 211, 25), "sedano": (40, 0.2, 3, 260, 11),
    "finocchi": (49, 0.7, 12, 414, 17), "cetrioli": (16, 0.3, 3, 147, 13),
    "radicchio": (19, 0.6, 8, 302, 13), "rucola": (160, 1.5, 15, 233, 32),
    "cipolle": (23, 0.2, 8, 146, 10), "aglio": (181, 1.7, 31, 401, 25),
    "funghi": (3, 0.5, 2, 318, 9), "zucca": (21, 0.8, 9, 368, 12),
    "barbabietola": (16, 0.8, 4, 325, 23), "patate": (12, 0.8, 19, 425, 23),
    "patate dolci": (30, 0.6, 2, 337, 25), "mela": (6, 0.1, 4, 107, 5),
    "pera": (9, 0.2, 4, 116, 7), "banana": (5, 0.3, 9, 358, 27),
    "arancia": (40, 0.1, 53, 181, 10), "mandarino": (37, 0.1, 27, 166, 12),
    "kiwi": (34, 0.3, 93, 312, 17), "fragole": (16, 0.4, 59, 2, 13),
    "uva": (10, 0.4, 4, 191, 7), "pesca": (6, 0.3, 7, 190, 9),
    "albicocca": (13, 0.4, 10, 259, 10), "melagrana": (10, 0.3, 10, 236, 12),
    "anguria": (7, 0.2, 8, 112, 10), "melone": (9, 0.2, 37, 267, 10),
    "ananas": (13, 0.3, 48, 109, 12), "limone": (26, 0.6, 53, 138, 8),
    "ciliegie": (13, 0.4, 7, 222, 11), "mirtilli": (12, 0.3, 10, 77, 6),
    "lamponi": (25, 0.7, 26, 151, 22), "mandorle": (269, 3.7, 0, 733, 270),
    "noci": (98, 2.9, 1, 441, 158), "nocciole": (114, 4.7, 6, 560, 163),
    "pistacchi": (107, 4.0, 5, 1025, 121), "anacardi": (37, 6.7, 0, 660, 292),
    "arachidi": (92, 4.6, 0, 705, 168), "semi di girasole": (78, 5.2, 1, 645, 325),
    "semi di zucca": (46, 8.8, 0, 809, 592), "semi di chia": (631, 7.7, 1, 407, 335),
    "olio extravergine d'oliva": (9, 0.6, 0, 1, 0), "olive": (88, 3.3, 0, 88, 0),
    "cioccolato fondente": (73, 11.9, 0, 715, 228), "cacao amaro": (125, 11.9, 0, 1500, 499),
    "miele": (6, 0.4, 1, 52, 2), "uova di gallina": (50, 1.2, 0, 126, 12),
}

# ──────────────────────────────────────────────────────────────────────
# Tabella di normalizzazione (singolare/plurale, sinonimi)
# ──────────────────────────────────────────────────────────────────────
_NORMALIZE = {
    "uova": "uova gallina", "uovo": "uova gallina", "albume": "albumi d'uovo",
    "yogurt": "yogurt bianco intero", "yogurt greco 0": "yogurt greco 0.2",
    "yogurt greco 2%": "yogurt greco 2", "yogurt greco 5%": "yogurt greco 5",
    "pane": "pane comune", "pane bianco": "pane comune", "pane di segale 62": "pane di segale",
    "riso": "riso basmati", "riso bianco": "riso brillato", "riso venere nero": "riso venere",
    "pasta": "pasta di semola", "spaghetto": "spaghetto", "spaghetti": "spaghetto",
    "avena fiocchi": "fiocchi d'avena", "fiocchi avena": "fiocchi d'avena",
    "pollo": "petto di pollo", "pollo petto": "petto di pollo",
    "salmone": "salmone", "tonno": "tonno", "fagiolo": "fagioli",
    "cece": "ceci", "lenticchia": "lenticchie", "pisello": "piselli",
    "olio oliva": "olio evo", "olio extravergine": "olio evo", "evo": "olio evo",
    "frutta": "frutta fresca", "verdura": "verdure miste", "verdure": "verdure miste",
    "insalata": "insalata mista", "pomodoro": "pomodoro", "zucchina": "zucchine",
    "melanzana": "melanzane", "peperone": "peperoni", "carota": "carote",
    "patata": "patate", "mela": "mela", "banana": "banana", "pera": "pera",
    "arancia": "arancia", "mandorla": "mandorle", "noce": "noci", "nocciola": "nocciole",
    "avocado": "avocado", "latte": "latte intero", "latte parz scremato": "latte parzialmente scremato",
    "integratore": "integratore proteico", "whey": "whey", "proteine": "proteine del siero",
    "ciliegia": "ciliegie", "mirtillo": "mirtilli", "lamponi": "lamponi",
    "uva": "uva", "ananas": "ananas", "limone": "limone",
    "cipolla": "cipolle", "porro": "porri", "finocchio": "finocchi",
    "fungho": "funghi", "mandorla": "mandorle",
}


def _norm(name: str) -> str:
    n = name.strip().lower()
    # rimuovi unità/quantità residue solo come token finale (es. "30 g", "kg")
    n = re.sub(r"\s*\d+(?:[.,]\d+)?\s*(g|gr|grammi|kg|ml|cc)\s*$", "", n, flags=re.I)
    n = " ".join(n.split())
    if n in FOODS:
        return n
    if n in _NORMALIZE:
        return _NORMALIZE[n]
    # match parziale: chiave che inizia con n o n che inizia con chiave
    for k in FOODS:
        if k.startswith(n) or n.startswith(k):
            return k
    # match contenimento (es. "pane di segale" in "pane di segale con semi")
    for k in FOODS:
        if k in n:
            return k
    return None


# ──────────────────────────────────────────────────────────────────────
# FOOD_FODMAP — Profilo FODMAP per 100 g (g/100g).
# Basato su dati Monash University FODMAP (2024-2025).
# ──────────────────────────────────────────────────────────────────────
_ZERO_FODMAP = {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0,
                "sorbitol": 0, "mannitol": 0, "mannosio": 0}

FOOD_FODMAP = {
    # --- Verdure ---
    "cipolle": {"fructan": 1.2, "gos": 0, "lactose": 0, "excess_fructose": 0,
                "sorbitol": 0, "mannitol": 0.3, "mannosio": 0},
    "cipolla": {"fructan": 1.2, "gos": 0, "lactose": 0, "excess_fructose": 0,
                "sorbitol": 0, "mannitol": 0.3, "mannosio": 0},
    "aglio": {"fructan": 1.8, "gos": 0, "lactose": 0, "excess_fructose": 0,
              "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "cavolfiore": {"fructan": 0.4, "gos": 0, "lactose": 0, "excess_fructose": 0,
                   "sorbitol": 0, "mannitol": 0.3, "mannosio": 0},
    "finocchi": {"fructan": 0.5, "gos": 0, "lactose": 0, "excess_fructose": 0,
                 "sorbitol": 0, "mannitol": 0.2, "mannosio": 0},
    "porri": {"fructan": 0.9, "gos": 0, "lactose": 0, "excess_fructose": 0,
              "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "funghi": {"fructan": 0, "gos": 0.3, "lactose": 0, "excess_fructose": 0,
               "sorbitol": 0, "mannitol": 0.4, "mannosio": 0},
    "funghi champignon": {"fructan": 0, "gos": 0.3, "lactose": 0, "excess_fructose": 0,
                          "sorbitol": 0, "mannitol": 0.4, "mannosio": 0},
    # --- Frutta ---
    "mela": {"fructan": 0.1, "gos": 0, "lactose": 0, "excess_fructose": 0.8,
             "sorbitol": 0.6, "mannitol": 0, "mannosio": 0},
    "pera": {"fructan": 0.1, "gos": 0, "lactose": 0, "excess_fructose": 0.7,
             "sorbitol": 0.9, "mannitol": 0, "mannosio": 0},
    "anguria": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0.4,
                "sorbitol": 0.4, "mannitol": 0, "mannosio": 0},
    "pesca": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0.3,
              "sorbitol": 0.3, "mannitol": 0, "mannosio": 0},
    "albicocca": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0.3,
                  "sorbitol": 0.3, "mannitol": 0, "mannosio": 0},
    "prugne": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0.4,
               "sorbitol": 0.5, "mannitol": 0, "mannosio": 0},
    "ciliegie": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0.3,
                 "sorbitol": 0.3, "mannitol": 0, "mannosio": 0},
    # --- Latticini ---
    "latte intero": {"fructan": 0, "gos": 0, "lactose": 4.7, "excess_fructose": 0,
                     "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "yogurt greco": {"fructan": 0, "gos": 0, "lactose": 0.8, "excess_fructose": 0,
                     "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    # --- Legumi ---
    "lenticchie": {"fructan": 0, "gos": 1.5, "lactose": 0, "excess_fructose": 0,
                   "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "ceci": {"fructan": 0, "gos": 1.2, "lactose": 0, "excess_fructose": 0,
             "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "fagioli": {"fructan": 0, "gos": 1.8, "lactose": 0, "excess_fructose": 0,
                "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    # --- Cereali ---
    "pane comune": {"fructan": 0.5, "gos": 0, "lactose": 0, "excess_fructose": 0,
                    "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "fiocchi d'avena": {"fructan": 0.2, "gos": 0, "lactose": 0, "excess_fructose": 0,
                        "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "farro": {"fructan": 0.4, "gos": 0, "lactose": 0, "excess_fructose": 0,
              "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    # --- Frutta secca / semi ---
    "mandorle": {"fructan": 0, "gos": 0.5, "lactose": 0, "excess_fructose": 0,
                 "sorbitol": 0, "mannitol": 0.3, "mannosio": 0},
    "anacardi": {"fructan": 0, "gos": 0.3, "lactose": 0, "excess_fructose": 0,
                 "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    "pistacchi": {"fructan": 0, "gos": 0.4, "lactose": 0, "excess_fructose": 0,
                  "sorbitol": 0, "mannitol": 0, "mannosio": 0},
    # --- Dolci / condimenti ---
    "miele": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 2.5,
              "sorbitol": 0.4, "mannitol": 0, "mannosio": 0},
    "zucchero": {"fructan": 0, "gos": 0, "lactose": 0, "excess_fructose": 0,
                 "sorbitol": 0, "mannitol": 0, "mannosio": 0},
}


# ──────────────────────────────────────────────────────────────────────
# FOOD_HISTAMINE — Livello di istamina per alimento.
# Fonte: SIGHI + dati clinici (2024-2025).
# ──────────────────────────────────────────────────────────────────────
FOOD_HISTAMINE = {
    # --- High ---
    "salame": "high",
    "prosciutto crudo": "high",
    "bresaola": "high",
    "tonno in scatola": "high",
    "sgombro": "high",
    "sardine": "high",
    "acciughe": "high",
    "parmigiano": "high",
    "pecorino": "high",
    "formaggio fresco": "high",
    "mozzarella stagionata": "high",
    "yogurt": "high",
    "yogurt bianco intero": "high",
    "yogurt greco": "high",
    "yogurt magro": "high",
    "yogurt greco 0.2": "high",
    "yogurt greco 2": "high",
    "yogurt greco 5": "high",
    "yogurt greco con miele": "high",
    "kefir": "high",
    "aceto balsamico": "high",
    "vino": "high",
    "birra": "high",
    "lievito": "high",
    "pomodori": "high",
    "pomodoro": "high",
    "spinaci": "high",
    "melanzane": "high",
    "peperoni": "high",
    "avocado": "high",
    "banana": "high",
    "noci": "high",
    "frutta secca": "high",
    "cacao amaro": "high",
    "cioccolato fondente": "high",
    "cioccolato al latte": "high",
    "caffè": "high",
    # --- Medium ---
    "prosciutto cotto": "medium",
    "formaggio bianco": "medium",
    "ricotta": "medium",
    "ricotta vaccina": "medium",
    "piselli": "medium",
    "fagioli": "medium",
    "fagioli borlotti": "medium",
    # --- Low ---
    "petto di pollo": "low",
    "tacchino": "low",
    "fesa di tacchino": "low",
    "manzo magro": "low",
    "vitello": "low",
    "uova gallina": "low",
    "uova di gallina": "low",
    "albumi d'uovo": "low",
    "tuorlo d'uovo": "low",
    "riso basmati": "low",
    "riso brillato": "low",
    "riso integrale": "low",
    "riso venere": "low",
    "patate": "low",
    "carote": "low",
    "zucchine": "low",
    "courgette": "low",
    "broccoli": "low",
    "cetrioli": "low",
    "fragole": "low",
    "mirtilli": "low",
    "arancia": "low",
    "mela": "low",
    "olive": "low",
    "olio evo": "low",
    "olio extravergine d'oliva": "low",
    "olio di semi": "low",
    "burro": "low",
}


# ──────────────────────────────────────────────────────────────────────
# FOOD_OXALATE — Livello di ossalati per alimento.
# ──────────────────────────────────────────────────────────────────────
FOOD_OXALATE = {
    # --- High ---
    "spinaci": "high",
    "barbabietola": "high",
    "mandorle": "high",
    "noci": "high",
    "semi di zucca": "high",
    "cioccolato fondente": "high",
    "cacao amaro": "high",
    "tè": "high",
    "melagrana": "high",
    "quinoa": "high",
    # --- Medium ---
    "fagioli": "medium",
    "fagioli borlotti": "medium",
    "ceci": "medium",
    "lenticchie": "medium",
    "patate dolci": "medium",
    "avena": "medium",
    "fiocchi d'avena": "medium",
    "tofu": "medium",
    "soia": "medium",
    "melanzane": "medium",
    "peperoni": "medium",
    "banana": "medium",
    "fichi": "medium",
    "prugne": "medium",
    # --- Low ---
    "latte intero": "low",
    "latte parzialmente scremato": "low",
    "latte scremato": "low",
    "yogurt greco": "low",
    "yogurt bianco intero": "low",
    "yogurt magro": "low",
    "yogurt greco 0.2": "low",
    "yogurt greco 2": "low",
    "yogurt greco 5": "low",
    "formaggio bianco": "low",
    "formaggio fresco": "low",
    "ricotta": "low",
    "ricotta vaccina": "low",
    "parmigiano": "low",
    "pecorino": "low",
    "mozzarella": "low",
    "petto di pollo": "low",
    "tacchino": "low",
    "manzo magro": "low",
    "vitello": "low",
    "salmone": "low",
    "tonno": "low",
    "merluzzo": "low",
    "sgombro": "low",
    "uova gallina": "low",
    "uova di gallina": "low",
    "riso basmati": "low",
    "riso brillato": "low",
    "riso integrale": "low",
    "pane comune": "low",
    "pane integrale": "low",
    "olio evo": "low",
    "olio extravergine d'oliva": "low",
    "burro": "low",
    "carote": "low",
    "zucchine": "low",
    "courgette": "low",
    "broccoli": "low",
    "cavolfiore": "low",
    "asparagi": "low",
    "fragole": "low",
    "mirtilli": "low",
    "arancia": "low",
    "mandarino": "low",
    "mela": "low",
}


# ──────────────────────────────────────────────────────────────────────
# FOOD_SALICYLATE — Livello di salicilati per alimento.
# ──────────────────────────────────────────────────────────────────────
FOOD_SALICYLATE = {
    # --- High ---
    "mirtilli": "high",
    "mirtilli rossi": "high",
    "lamponi": "high",
    "ribes": "high",
    "more": "high",
    "melagrana": "high",
    "uva": "high",
    "salamoia": "high",
    "curry": "high",
    "rosmarino": "high",
    "paprika": "high",
    "cannella": "high",
    "zenzero": "high",
    "curcuma": "high",
    "zenzero in polvere": "high",
    "origano": "high",
    "basilico": "high",
    # --- Medium ---
    "pomodori": "medium",
    "pomodoro": "medium",
    "peperoni": "medium",
    "melanzane": "medium",
    "anguria": "medium",
    "ciliegie": "medium",
    "ananas": "medium",
    "avocado": "medium",
    "mandorle": "medium",
    "miele": "medium",
    "timo": "medium",
    "prezzemolo": "medium",
    "senape": "medium",
    # --- Low ---
    "riso basmati": "low",
    "riso brillato": "low",
    "riso integrale": "low",
    "pasta": "low",
    "pasta di semola": "low",
    "pane comune": "low",
    "pane integrale": "low",
    "petto di pollo": "low",
    "tacchino": "low",
    "manzo magro": "low",
    "salmone": "low",
    "tonno": "low",
    "merluzzo": "low",
    "uova gallina": "low",
    "uova di gallina": "low",
    "yogurt greco": "low",
    "latte intero": "low",
    "formaggio bianco": "low",
    "burro": "low",
    "olio evo": "low",
    "olio extravergine d'oliva": "low",
    "zucchine": "low",
    "courgette": "low",
    "cetrioli": "low",
    "lattuga": "low",
    "patate": "low",
    "mela": "low",
    "pera": "low",
    "banana": "low",
    "carote": "low",
    "broccoli": "low",
    "cavolfiore": "low",
    "finocchi": "low",
    "sedano": "low",
}


# ──────────────────────────────────────────────────────────────────────
# FOOD_LECTIN — Livello di lectine per alimento (rilevante per MCAS/gut healing).
# ──────────────────────────────────────────────────────────────────────
FOOD_LECTIN = {
    # --- High ---
    "fagioli": "high",
    "fagioli borlotti": "high",
    "lenticchie": "high",
    "ceci": "high",
    "ceci cotti": "high",
    "piselli": "high",
    "fave": "high",
    "grano": "high",
    "riso basmati": "high",
    "riso brillato": "high",
    "patate": "high",
    "peperoni": "high",
    "pomodori": "high",
    "pomodoro": "high",
    "melanzane": "high",
    "cetrioli": "high",
    # --- Medium ---
    "avena": "medium",
    "fiocchi d'avena": "medium",
    "quinoa": "medium",
    "soia": "medium",
    "tofu": "medium",
    # --- Low ---
    "petto di pollo": "low",
    "coscia di pollo": "low",
    "tacchino": "low",
    "manzo magro": "low",
    "vitello": "low",
    "salmone": "low",
    "tonno": "low",
    "merluzzo": "low",
    "sgombro": "low",
    "orata": "low",
    "spigola": "low",
    "gamberi": "low",
    "uova gallina": "low",
    "uova di gallina": "low",
    "latte intero": "low",
    "latte scremato": "low",
    "yogurt greco": "low",
    "yogurt bianco intero": "low",
    "formaggio bianco": "low",
    "ricotta": "low",
    "parmigiano": "low",
    "mela": "low",
    "pera": "low",
    "banana": "low",
    "arancia": "low",
    "fragole": "low",
    "mirtilli": "low",
    "zucchine": "low",
    "courgette": "low",
    "broccoli": "low",
    "cavolfiore": "low",
    "carote": "low",
    "lattuga": "low",
    "finocchi": "low",
    "asparagi": "low",
}


# ──────────────────────────────────────────────────────────────────────
# EXTENDED_MICROS — Micronutrienti aggiuntivi per 100 g.
# omega3 mg, vit_d IU, zinc mg, b12 mcg, folate mcg, selenium mcg,
# vit_a mcg RAE, vit_e mg.
# ──────────────────────────────────────────────────────────────────────
_EXT_MICROS_DEFAULT = {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                       "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0}

EXTENDED_MICROS = {
    "salmone": {"omega3": 1.5, "vit_d": 526, "zinc": 0, "b12": 3.2,
                "folate": 0, "selenium": 36, "vit_a": 12, "vit_e": 0},
    "salmone affumicato": {"omega3": 1.5, "vit_d": 526, "zinc": 0, "b12": 3.2,
                           "folate": 0, "selenium": 36, "vit_a": 12, "vit_e": 0},
    "sgombro": {"omega3": 2.6, "vit_d": 400, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 44, "vit_a": 0, "vit_e": 0},
    "tonno": {"omega3": 0.2, "vit_d": 2.7, "zinc": 0, "b12": 8.5,
              "folate": 0, "selenium": 90, "vit_a": 0, "vit_e": 0},
    "tonno in scatola": {"omega3": 0.2, "vit_d": 2.7, "zinc": 0, "b12": 8.5,
                         "folate": 0, "selenium": 90, "vit_a": 0, "vit_e": 0},
    "uova gallina": {"omega3": 0.1, "vit_d": 82, "zinc": 1.1, "b12": 1.1,
                     "folate": 47, "selenium": 30, "vit_a": 140, "vit_e": 1.0},
    "uova di gallina": {"omega3": 0.1, "vit_d": 82, "zinc": 1.1, "b12": 1.1,
                        "folate": 47, "selenium": 30, "vit_a": 140, "vit_e": 1.0},
    "petto di pollo": {"omega3": 0, "vit_d": 0, "zinc": 0.9, "b12": 0.3,
                       "folate": 0, "selenium": 0, "vit_a": 6, "vit_e": 0},
    "manzo magro": {"omega3": 0, "vit_d": 0, "zinc": 4.8, "b12": 2.5,
                    "folate": 0, "selenium": 12, "vit_a": 0, "vit_e": 0},
    "spinaci": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 194, "selenium": 0, "vit_a": 469, "vit_e": 2.0},
    "broccoli": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 63, "selenium": 0, "vit_a": 31, "vit_e": 0},
    "mandorle": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 25.6},
    "noci": {"omega3": 0.9, "vit_d": 0, "zinc": 0, "b12": 0,
             "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0.7},
    "semi di chia": {"omega3": 17.8, "vit_d": 0, "zinc": 0, "b12": 0,
                     "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "semi di lino": {"omega3": 22.8, "vit_d": 0, "zinc": 0, "b12": 0,
                     "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "avocado": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 81, "selenium": 0, "vit_a": 0, "vit_e": 2.1},
    "banana": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
               "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "patate": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
               "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "lenticchie": {"omega3": 0, "vit_d": 0, "zinc": 1.3, "b12": 0,
                   "folate": 181, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "ceci": {"omega3": 0, "vit_d": 0, "zinc": 1.5, "b12": 0,
             "folate": 172, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "fagioli": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 130, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "mirtilli": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "arancia": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "kiwi": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
             "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "tacchino": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "vitello": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "gamberi": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "merluzzo": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "orata": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
              "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "quinoa": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
               "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "farro": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
              "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "avena": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
              "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "tofu": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
             "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "soia": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
             "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "semi di girasole": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                         "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "semi di zucca": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                      "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "piselli": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "fave": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
             "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "agnello": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "maiale magro": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                     "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "coniglio": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "nocciole": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "arachidi": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "pistacchi": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                  "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "anacardi": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                 "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "tahin": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
              "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "burro di arachidi": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                          "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "latte intero": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                     "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "latte scremato": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                       "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "parmigiano": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                   "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "mozzarella": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                   "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "ricotta": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
    "formaggio bianco": {"omega3": 0, "vit_d": 0, "zinc": 0, "b12": 0,
                         "folate": 0, "selenium": 0, "vit_a": 0, "vit_e": 0},
}


# ──────────────────────────────────────────────────────────────────────
# Funzioni di normalizzazione e accesso ai dati
# ──────────────────────────────────────────────────────────────────────

def nutrition_for(name: str, grams):
    """Ritorna nutrienti per `grams` g dell'alimento `name`.

    Include nutrienti base + micronutrienti estesi + score FODMAP totale.
    """
    grams = float(grams or 0)
    key = _norm(name)
    if key is None:
        return {"food": name, "matched": False, "kcal": 0.0, "p": 0.0, "c": 0.0,
                "f": 0.0, "fib": 0.0, "sug": 0.0, "salt": 0.0,
                "ca": 0.0, "fe": 0.0, "vitc": 0.0, "k": 0.0, "mg": 0.0,
                "omega3": 0.0, "vit_d": 0.0, "zinc": 0.0, "b12": 0.0,
                "folate": 0.0, "selenium": 0.0, "vit_a": 0.0, "vit_e": 0.0,
                "fodmap_total": 0.0}
    kcal, p, c, f, fib, sug, salt = FOODS[key]
    factor = grams / 100.0
    ca, fe, vitc, k, mg = MICROS.get(key, (0, 0, 0, 0, 0))
    ext = EXTENDED_MICROS.get(key, _EXT_MICROS_DEFAULT)
    fp = FOOD_FODMAP.get(key, _ZERO_FODMAP)
    fodmap_total = sum(fp.values())
    return {
        "food": key, "matched": True,
        "kcal": round(kcal * factor, 1), "p": round(p * factor, 1),
        "c": round(c * factor, 1), "f": round(f * factor, 1),
        "fib": round(fib * factor, 1), "sug": round(sug * factor, 1),
        "salt": round(salt * factor, 2),
        "ca": round(ca * factor, 1), "fe": round(fe * factor, 2),
        "vitc": round(vitc * factor, 1), "k": round(k * factor, 1),
        "mg": round(mg * factor, 1),
        # Extended micronutrients
        "omega3": round(ext.get("omega3", 0) * factor, 3),
        "vit_d": round(ext.get("vit_d", 0) * factor, 1),
        "zinc": round(ext.get("zinc", 0) * factor, 2),
        "b12": round(ext.get("b12", 0) * factor, 2),
        "folate": round(ext.get("folate", 0) * factor, 1),
        "selenium": round(ext.get("selenium", 0) * factor, 1),
        "vit_a": round(ext.get("vit_a", 0) * factor, 1),
        "vit_e": round(ext.get("vit_e", 0) * factor, 2),
        # FODMAP total score
        "fodmap_total": round(fodmap_total * factor, 3),
    }


def search_foods(query: str, limit: int = 20):
    """Ricerca alimenti per nome (match parziale, case-insensitive)."""
    q = (query or "").strip().lower()
    if not q:
        return []
    hits = []
    for k in FOODS:
        if q in k:
            hits.append(k)
    # priorità: inizio con query, poi contenimento
    hits.sort(key=lambda x: (not x.startswith(q), x))
    return hits[:limit]


def food_fodmap(name: str) -> dict:
    """Ritorna il profilo FODMAP per un alimento (g/100g).

    Returns dict with keys: fructan, gos, lactose, excess_fructose,
    sorbitol, mannitol, mannosio. Se non trovato, restituisce valori zero.
    """
    key = _norm(name)
    if key is None:
        return dict(_ZERO_FODMAP)
    return dict(FOOD_FODMAP.get(key, _ZERO_FODMAP))


def food_histamine_level(name: str) -> str:
    """Ritorna il livello di istamina per un alimento: 'low', 'medium', 'high'.

    Se non trovato, restituisce 'low' (assente).
    """
    key = _norm(name)
    if key is None:
        return "low"
    return FOOD_HISTAMINE.get(key, "low")


def food_oxalate_level(name: str) -> str:
    """Ritorna il livello di ossalati per un alimento: 'low', 'medium', 'high'.

    Se non trovato, restituisce 'low'.
    """
    key = _norm(name)
    if key is None:
        return "low"
    return FOOD_OXALATE.get(key, "low")


def food_salicylate_level(name: str) -> str:
    """Ritorna il livello di salicilati per un alimento: 'low', 'medium', 'high'.

    Se non trovato, restituisce 'low'.
    """
    key = _norm(name)
    if key is None:
        return "low"
    return FOOD_SALICYLATE.get(key, "low")


def food_lectin_level(name: str) -> str:
    """Ritorna il livello di lectine per un alimento: 'low', 'medium', 'high'.

    Se non trovato, restituisce 'low'.
    """
    key = _norm(name)
    if key is None:
        return "low"
    return FOOD_LECTIN.get(key, "low")


def fodmap_load(food_items: list) -> dict:
    """Calcola il carico FODMAP totale per una lista di alimenti.

    Args:
        food_items: lista di tuple (nome_alimento, grammi).

    Returns:
        {
            total_load: float,          # somma di tutti i FODMAP in grammi
            by_group: {                 # totale per gruppo FODMAP
                fructan: float,
                gos: float,
                lactose: float,
                excess_fructose: float,
                sorbitol: float,
                mannitol: float,
                mannosio: float,
            },
            flagged_items: [            # alimenti con FODMAP significativo
                {food, grams, group, value, level},
                ...
            ]
        }

    level thresholds per gruppo (g/100g): low < 0.3, medium 0.3-0.6, high > 0.6.
    """
    groups = ["fructan", "gos", "lactose", "excess_fructose", "sorbitol", "mannitol", "mannosio"]
    by_group = {g: 0.0 for g in groups}
    flagged_items = []
    total_load = 0.0

    for food_name, grams in food_items:
        grams = float(grams or 0)
        fp = food_fodmap(food_name)
        factor = grams / 100.0
        for g in groups:
            val_per_100 = fp.get(g, 0)
            load = val_per_100 * factor
            by_group[g] = round(by_group[g] + load, 4)
            total_load += load
            # Flag if per-100g value exceeds low threshold
            if val_per_100 > 0.3:
                if val_per_100 > 0.6:
                    level = "high"
                else:
                    level = "medium"
                key = _norm(food_name)
                flagged_items.append({
                    "food": key or food_name,
                    "grams": grams,
                    "group": g,
                    "value": round(val_per_100 * factor, 4),
                    "level": level,
                })

    return {
        "total_load": round(total_load, 4),
        "by_group": {g: round(by_group[g], 4) for g in groups},
        "flagged_items": flagged_items,
    }


if __name__ == "__main__":
    print("=== Test base ===")
    for t in ["Uova di gallina", "Latte di Soia", "Pane di segale", "Avocado", "zucchine", "proteine del siero"]:
        n = nutrition_for(t, 100)
        print(f"  {t:22s} -> {n['food']:22s} kcal={n['kcal']} p={n['p']} ca={n['ca']} fe={n['fe']} matched={n['matched']}")
    print("  Totale alimenti:", len(FOODS))

    print("\n=== Test FODMAP ===")
    for t in ["cipolle", "mela", "latte intero", "lenticchie", "mandorle"]:
        fp = food_fodmap(t)
        print(f"  {t:18s} -> {fp}")
        n = nutrition_for(t, 100)
        print(f"    fodmap_total: {n['fodmap_total']}")

    print("\n=== Test istamina ===")
    for t in ["salame", "petto di pollo", "yogurt greco"]:
        print(f"  {t:18s} -> histamine={food_histamine_level(t)}")

    print("\n=== Test ossalati ===")
    for t in ["spinaci", "fagioli", "latte intero"]:
        print(f"  {t:18s} -> oxalate={food_oxalate_level(t)}")

    print("\n=== Test salicilati ===")
    for t in ["mirtilli", "pomodori", "riso basmati"]:
        print(f"  {t:18s} -> salicylate={food_salicylate_level(t)}")

    print("\n=== Test lectine ===")
    for t in ["fagioli", "avena", "petto di pollo"]:
        print(f"  {t:18s} -> lectin={food_lectin_level(t)}")

    print("\n=== Test FODMAP load ===")
    items = [("cipolle", 80), ("mela", 150), ("latte intero", 250), ("petto di pollo", 150)]
    result = fodmap_load(items)
    print(f"  total_load: {result['total_load']}")
    print(f"  by_group: {result['by_group']}")
    print(f"  flagged_items ({len(result['flagged_items'])}):")
    for fi in result["flagged_items"]:
        print(f"    {fi['food']} {fi['grams']}g -> {fi['group']}: {fi['value']} ({fi['level']})")

    print("\n=== Test micronutrienti estesi ===")
    for t in ["salmone", "uova gallina", "spinaci", "avocado"]:
        n = nutrition_for(t, 100)
        print(f"  {t:18s} -> omega3={n['omega3']} vit_d={n['vit_d']} zinc={n['zinc']} "
              f"b12={n['b12']} folate={n['folate']} selenium={n['selenium']} "
              f"vit_a={n['vit_a']} vit_e={n['vit_e']}")
