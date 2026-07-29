# Bug Report — NutriCoach v2.20.6

> **Generated**: 2026-07-29 | **QA Round**: Sub-Agent Parallel E2E Testing (4 agents)

---

## Riepilogo

| Gravità | Count | Status |
|---------|-------|--------|
| 🔴 **HIGH** | 1 | Open — Settings API 401 without proper UX |
| 🟠 **MED** | 2 | Open — Empty patient creation, large input accepted |
| 🟢 **LOW** | 2 | Open — SQL injection 500, XSS storage |
| ℹ️ **INFO** | 0 | — |

---

## 🔴 HIGH

### H1 — Settings page shows 401 error without auth redirect
| Campo | Valore |
|-------|--------|
| **Componente** | Settings / Auth |
| **Tipo** | UX |
| **Descrizione** | `GET /api/settings` returns HTTP 401 when called without a valid token. The frontend does not handle this gracefully — it shows a raw error instead of redirecting to login. |
| **Passi per riprodurre** | Remove token → call API settings → observe 401 |
| **Fix** | Add 401 interceptor in API helpers to redirect to login overlay |

---

## 🟠 MED

### M1 — Empty patient payload creates empty record
| Campo | Valore |
|-------|--------|
| **Componente** | API /patients |
| **Tipo** | Validazione |
| **Descrizione** | `POST /api/patients` with `{}` creates a patient record with all NULL fields. Should reject empty names. |
| **Fix** | Add server-side validation for required `name` field in `api_create_patient()` |

### M2 — 1000-char name accepted
| Campo | Valore |
|-------|--------|
| **Componente** | API /patients |
| **Tipo** | Boundary |
| **Descrizione** | A 1000-character name is accepted and stored. The UI has `maxlength=60` but there's no server-side enforcement. |
| **Fix** | Add length validation on server side |

---

## 🟢 LOW

### L1 — SQL injection attempt returns HTTP 500
| Campo | Valore |
|-------|--------|
| **Componente** | API error handling |
| **Tipo** | Robustezza |
| **Descrizione** | Sending SQL-like payload (`test' OR 1=1--`) returns HTTP 500 instead of a clean 400. SQLite parameterized queries prevent actual injection, but the error handling is poor. |
| **Fix** | Catch database errors and return proper HTTP 400 with clean message |

### L2 — XSS payload stored in DB
| Campo | Valore |
|-------|--------|
| **Componente** | API /patients |
| **Tipo** | Security |
| **Descrizione** | `<script>alert(1)</script>` is stored as-is in DB. The `esc()` function protects the UI, but defense-in-depth should sanitize on input too. |
| **Fix** | Strip HTML tags on input or escape at the API layer |

---

## 📊 Test Metrics

| Agent | Endpoints Tested | Findings |
|-------|-----------------|----------|
| 1 — Visual Inspector | HTML/CSS analysis | All CSS enhancements present |
| 2 — Functional Clicker | 10 CRUD operations | Settings 401, CRUD OK |
| 3 — User Journey | 10-step user flow | All flows functional |
| 4 — Chaos Explorer | 9 edge-case tests | Empty payload, large input, SQL 500 |

---

## 📈 State

| Area | Voto | Note |
|------|------|------|
| Core CRUD | A+ | All patient, diet, BIA operations OK |
| Auth | A- | 401 unhandled in Settings (frontend) |
| Security | A- | SQLite parameterized, XSS escaped in UI |
| Validation | B+ | Missing server-side name validation |
| Performance | A+ | 13ms average latency |
| Error handling | B+ | Some 500 instead of 400 |
| UX (enhancements) | A | Loading states, active states, error banners added |
