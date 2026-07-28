# NutriCoach v2.20.1 — Manual End-to-End Test Briefing

You are QA-testing the NutriCoach web app (a nutritionist/dietitian studio app)
as a FINAL END USER clicking through the real browser UI. Your job: find BUGS.

## Target (ONLY this version)
- App: NutriCoach v2.20.1 (master, commit 1c6cd93). This is the LATEST. Do not test old versions.
- Server already running at http://127.0.0.1:8400 (FastAPI + index.html SPA).

## How to log in
- Open http://127.0.0.1:8400
- A login overlay appears (first screen).
- Credentials: username `admin`  password `admin123`
- Click login. On success the overlay hides and the Dashboard loads.

## UI map (every nav item is a section — click ALL of them)
Sidebar nav items (onclick=nav('x')):
- Dashboard (📊)        -> nav('dashboard')
- Pazienti (👥)         -> nav('pazienti')
- BIA (🔬)              -> nav('bia')      [bioelectrical impedance]
- Dieta (🍽️)           -> nav('dieta')    [diet plans]
- Agenda (📅)           -> nav('agenda')   [appointments]
- Notifiche (📨)        -> nav('notifiche')
- Archivio (📁)         -> nav('archivio')
- Ricettario (📖)       -> nav('ricettario')  [recipes]

Topbar / icons (bottom of sidebar):
- 📊 showStats()        -> studio statistics modal
- ⚙️ showSettings()     -> studio settings + brand color/logo
- 🔔 toggleNotifDropdown() -> notifications dropdown
- 🌙 toggleTheme()      -> DARK / LIGHT theme toggle
- 🚪 doLogout()         -> logout (logs you out -> login overlay reappears)

## What to test (be exhaustive)
For EACH section and EACH button/modal/form you can reach:
1. Does the section render at all? (empty? broken? spinner forever?)
2. Click EVERY button, link, tab, modal trigger, "+ Nuovo", save/cancel, close.
3. Open modals, fill forms, submit. Does it save? Does it error?
4. Theme toggle: switch DARK then LIGHT — is text readable in BOTH? (contrast check)
5. Watch the browser console for JS errors (window.onerror / red errors) at ALL times.
6. Take SCREENSHOTS of anything broken or notable.
7. Patient flow: create a patient (Pazienti -> + Nuovo), then open that patient,
   click every patient tab (anamnesi, BIA, dieta, agenda, referti, appuntamenti,
   sintomi, progressi, farmaci, diario, chat, compara, etc.) — test each tab's buttons.
8. Diet: search foods, add to plan, generate plan, export PDF if available.
9. Recipes (Ricettario): create, edit, apply to patient.
10. Notifications: create, list.
11. Settings: change clinic name / theme color / logo URL, save, verify it applies (brand).

## How to report
Produce a structured bug report:
- BUG [severity HIGH/MED/LOW]: <title>
  - Section: <where>
  - Steps: 1.. 2.. 3..
  - Expected: ...
  - Actual: ... (attach screenshot path if captured)
  - Console error (if any): <exact text>
- Also list: sections that rendered OK, buttons verified working.
- Be honest: if you could not reach something, say so (don't assume it works).
- Italian UI — describe bugs in Italian or English, your call, but be precise.

NOTE: This is a real running app. Do not modify server code. Only click & observe.
If the page is completely blank/broken, that itself is the #1 bug to report with console output.
