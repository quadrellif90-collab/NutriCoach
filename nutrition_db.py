"""NutriCoach — Database alimenti di riferimento (valori per 100 g).

Fonti: tabelle di composizione degli alimenti INRAN (Banco dati di
composizione degli alimenti), LARN (Livelli di Assunzione di Riferimento di
Nutrienti ed energia, IV Revisione 2014, SINU) e USDA FoodData Central.
Valori medi di riferimento (kcal, proteine g, carboidrati g, grassi g,
fibre g, zuccheri g, sale g). Per gli alimenti con acqua/età diverse i
valori sono approssimati per 100 g edibili.

Interfaccia:
    nutrition_for(name, grams) -> {food, matched, kcal, p, c, f, fib, sug, salt,
                                    ca, fe, vitc, k, mg}
    search_foods(query, limit) -> [name, ...]
"""

import re

# (nome, kcal, proteine, carboidrati, grassi, fibre, zuccheri, sale)
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

# Micronutrienti principali per 100 g (Ca mg, Fe mg, VitC mg, K mg, Mg mg).
# Copertura dei piu' comuni; alimenti non presenti -> 0.
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

# tabella di normalizzazione (singolare/plurale, sinonimi)
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


def nutrition_for(name: str, grams):
    """Ritorna nutrienti per `grams` g dell'alimento `name`."""
    grams = float(grams or 0)
    key = _norm(name)
    if key is None:
        return {"food": name, "matched": False, "kcal": 0.0, "p": 0.0, "c": 0.0,
                "f": 0.0, "fib": 0.0, "sug": 0.0, "salt": 0.0,
                "ca": 0.0, "fe": 0.0, "vitc": 0.0, "k": 0.0, "mg": 0.0}
    kcal, p, c, f, fib, sug, salt = FOODS[key]
    factor = grams / 100.0
    ca, fe, vitc, k, mg = MICROS.get(key, (0, 0, 0, 0, 0))
    return {
        "food": key, "matched": True,
        "kcal": round(kcal * factor, 1), "p": round(p * factor, 1),
        "c": round(c * factor, 1), "f": round(f * factor, 1),
        "fib": round(fib * factor, 1), "sug": round(sug * factor, 1),
        "salt": round(salt * factor, 2),
        "ca": round(ca * factor, 1), "fe": round(fe * factor, 2),
        "vitc": round(vitc * factor, 1), "k": round(k * factor, 1),
        "mg": round(mg * factor, 1),
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


if __name__ == "__main__":
    for t in ["Uova di gallina", "Latte di Soia", "Pane di segale", "Avocado", "zucchine", "proteine del siero"]:
        n = nutrition_for(t, 100)
        print(f"{t:22s} -> {n['food']:22s} kcal={n['kcal']} p={n['p']} ca={n['ca']} fe={n['fe']} matched={n['matched']}")
    print("Totale alimenti:", len(FOODS))
