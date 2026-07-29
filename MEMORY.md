# AUTO MEMORIES INDEX — NutriCoach v2.20.5

> Generated autonomously by Hermes Agent during Phase 1 (auto‑learning & persistent memory indexing).  
> This file is a living index of the project architecture, API surface, critical modules, data schemas, and procedural conventions that the agent maintains to operate the application autonomously.

## 📂 ROOT STRUCTURE (summary)
- `app/` – package of core FastAPI modules (frontend entry, backend services)
- `app/templates/` – HTML templates (SPA shell `index.html`)
- `app/static/` – CSS / assets
- `app/main.py` – FastAPI app factory (REST endpoints, file mounting)
- `app.py` – entrypoint (uvicorn runner, port and host config)
- `run_v2.py` – explicit development runner (port 8400)
- `requirements.txt` – dependencies (fastapi, uvicorn, etc.)
- `README.md` – description of usage and deployment
- `CHANGELOG.md` – changelog
- `BUG_REPORT_LATEST.md` – latest QA findings / bug inventory
- `release_validator.sh` – final validation script (Phase 5)
- `RELEASE_CERTIFICATE.md` – certificate of compliance (generated after Phase 5)
- `app/templates/index.html` – SPA shell with all UI, component logic, API calls
- `app/static/style.css` – themed CSS with utility classes and UI components
- `app/database.py` – SQLite schema, tables, and core DAOs for patients, food catalog, diet plans, BIA, recipes, notifications, etc.
- `app/main.py` – FastAPI endpoints for all entity CRUD, report generation, integrations
- `.hermes/` – Hermes Agent runtime state (memory, skills, tools)

## ⚙️ CORE ARCHITECTURE

### FastAPI Backend (`app.main` / `app.py`)
- **Framework**: FastAPI v0.104+  
- **Entry**: `/` → serves static `index.html`
- **API Base**: `/api/`  
- **CORS**: aberto apenas para `localhost` / `127.0.0.1`  
- **Mount**: `/static` → `app/static/`  
- **Auth**: token JWT em `localStorage.token`. Endpoint de login `/api/login` e validação de sessão `/api/session`

### Frontend SPA (`app/templates/index.html`)
- **Bundled**: Sem frameworks externos, CSS custom properties e componentes de UI reutilizáveis  
- **Shell**: Sidebar de navegação persistente (Dashboard, Pazienti, BIA, Dieta, Agenda, Notifiche, Archivio, Ricettario)
- **Routing**: Manipulação do DOM via JS vanilla (`nav()`, `modal()`, `toast()`, `showConfirm()`)
- **Styling**: CSS modular com variáveis `--primary`, `--card`, `--bg` etc.; suporte a modo escuro (`data-theme="dark"`)
- **Interação**: fetch para API RESTful (`jget`, `jpost`, `jdel`) e promises assíncronas
- **Animações UX**: `fadeIn`, `skeleton` keyframes; modais com overlay clicável; botões com hover/active/states para loading/disabled

### Banco de dados (`app/database.py`)
| Tabela | Finalidade |
|-------|--------|
| `patients` | Perfis de usuário/clinica (nome, sexo, nascimento, peso, altura, etc.) |
| `food_catalog` | Edital de alimentos (estrutura nutricional normalizada para engine) |
| `bia_readings` | Medições antropométricas (peso, altura, %BF, etc.) para pacientes |
| `recipes` | Manuscritos de receitas personalizadas (ingredientes, instruções) |
| `diet_plans` | Histórico de planos alimentares gerados (macros e condição clínica) |
| `diet_items` | Itens detalhados de cada dia/meal para cada plano |
| `notifications` | fila de mensagens do sistema (lidas/não lidas) |

### Arquiteturas de componente UI
- **Sidebar global** com tema azul-escuro (`#1e293b`), hover destacado e modo escuro com alternância (`🌙`)
- **Toast system** – `toast()` suporta `success`, `error`, `warn`, `info` – com ícones e cores correspondentes
- **Modal / Confirm** – `showConfirm()` estático e estilizado com modos de perigo, botões personalizados
- **Cards de métricas** (Dashboard) – KPI baseados em contagem de DB (pacientes, com objetivo, etc.)
- **Grid de dieta** – layout de 7 colunas (dias + refeições) comSkeleton loader durante geração de plano
- **Página de pacient** integrada com 14 abas (Gerais, Dietas, BIA, Agenda, Notas clínicas, etc.)

## 🔑 MODULOS CRÍTICOS DE NEGÓCIO (arquivado em `app/`, principal)

| Módulo | Responsabilidade |
|--------|----------|
| `app/main.py` | Todos os endpoints REST – geração de dieta, BIA, receitas, agendamentos, exportações, etc. |
| `app.database.py` | CRUD, stored procedures, queries entre módulos (ex. cross‑references diet‑patient) |
| `app/utils/` (se presente) | Correções de erro, helpers para UI e chamadas de API |
| `nutrition_engine`, `meal_planner`, `bia_parser` | Lógica central de engine para cálculo de macros, geração de dieta, parsing de medidas corporais |
| `diet_presets` | Graficos predefinidos de presets de macros (personalizado, perda_gordo, hipertrofia)
| `pdf_export`, `pdf_sport_science` | Geração de PDFs (relatórios nutricionais, relatórios científicos esportivos) |

## 🔌 DEPENDÊNCIAS

```
fastapi, uvicorn (execução, endpoints)
python-multipart (UploadFile)
sqlalchemy Não utilizado (direto sqlite3)
Pillow (geração de PDF?)
Tesseract (OCR para BIA)
...
```

## 📋 ATALHOS DE CONJUTURA

- `hermes` – abre interface gráfica do Hermes Agent (recomenda-se para edição, testing)
- `node --check app/templates/index.html` – validation de sintaxe JS
- `pytest` – suite de testes (ativa no lado dev)
- `make` – (se presente) operações de compilação/

## 🧠 PERSISTENT AGENT MEMORIES (da Hermes)

*(Oculto – alimentado via `memory` tool durante execução)*  
Inclui vinculos sensíveis: credenciais por ambiente, rotas de usuário, identificadores de chave de API, padrões de sessão, etc.

## 🗂️ REFERÊNCIAS DE TEMPLATE / COMPONENTE

- Index.md de documentação – PATH para documentação de frontend e backend, integrada com comentários de análise de hermit

## 📜 FLUXOS DE NEGÓCIO DE ALTO NÍVEL

1. **Login** → token JWT → armazena em `localStorage.token`  
2. **Início** → verifica sessão ativa → renderiza dashboard com métricas  
3. **Paciente** → abre tela de detalhes → alterna entre abas → ações CRUD  
4. **BIA** → gera entrada de medição → salva → exibe gráfico e radar  
5. **Dieta** → seleciona preset / custom → gera plano automatizado → persiste como `diet_plans` + `diet_items`  
6. **Notificações** → push de lembretes e alertas do sistema  
7. **Exportação** → PDF/CSV e download de planilha  
8. **Configurações** → personalização da marca (nome, logotipo, tema) → refletido globalmente na UI  

## 📤 AUTO‑REPOSITORIO / CI SETUP

- **Git**: branch `main` com commit tags `v2.20.5`, `v2.20.6`, etc.
- **CI** (se configurado): executa `pytest`, aprova linting e CI checks antes do merge

## 📁 ESTRUTURA ATUAL DE ARQUIVOS (snapshot rápido)

```
NutriCoach/
├─ app.py, run_v2.py
├─ app/main.py, app/database.py, app/templates/index.html
├─ app/static/style.css, assets/
├─ BUG_REPORT_LATEST.md, MEMORY.md, USER.md
├─ release_validator.sh, RELEASE_CERTIFICATE.md
├─ requirements.txt, README.md, CHANGELOG.md
├─ .github/workflows/ (se presente)
└─ .hermes/  (estado do agente)
```

## 🔗 FLUXO DE AUTOMAÇÃO REPLICA

`Hermes` → (auto‑learning) → memória indexada → `Phase 2` (ux gap eradication) → `Phase 3` (sub‑agent testing) → `Phase 4` (auto‑fix) → `Phase 5` (validation & certification) → **Distribuição pronta**

---

## 🗓️ ÚLTIMA ATUALIZAÇÃO

- **Data**: 2026‑07‑29 (autônomo)
- **Versão**: v2.20.5 (main)
- **Status**: Implementação da fase <s>2</s: 4>‑<s>4</s: 1>? Em progresso – aguardando AWS e sub‑agentes.

## 📌 NOTAS DE SEGURANÇA E CONFORMIDADE

- O fluxo de autenticação usa JWT apenas localStorage (sem cookies)
- Front‑end só é servido via `http://127.0.0.1:8400` (CORS restrito)
- As mensagens de erro estão livres de XSS graças a `esc()`
- **auth.py** contém módulos de autenticação dedicados (???)

---

**Fin**  
Neste ponto, a memória do agente incorpora um mapeamento completo que funciona como um REPL do sistema para tarefas autônomas subsequentes.
