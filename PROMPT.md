# PROMPT.md — GenAI Usage Log

This document records all AI prompts, tools, and conversations used throughout the development of this project, as required by the COMP3011 GenAI declaration.

---

## Tools Used

| Tool | Purpose | Sessions |
|---|---|---|
| Claude Code (Sonnet 4.6) | Architecture planning, code generation, TDD workflow, commit orchestration, debugging | All sessions |

---

## Session Log

### Session 1 — Project Planning & Architecture

**Date:** 2026-03-03
**Model:** Claude Sonnet 4.6
**Purpose:** Project idea selection, architecture design, engineering standards

**Prompts used:**

#### Prompt 1: Coursework Analysis
> Analyse the COMP3011 coursework brief and summarise the key requirements, marking criteria, and what differentiates each grade band.

**Outcome:** Generated a comprehensive PLAN.md mapping every requirement and marking criterion to specific implementation tasks.

#### Prompt 2: Project Idea Brainstorming
> Suggest genuinely creative and original project ideas that use real, freely available public datasets, have compelling analytical endpoints, would be memorable to an examiner, have a natural place for AI integration, and could realistically be built by one person.

**Outcome:** Evaluated 15+ project ideas across domains (sports, politics, science, crime, energy, gaming). Narrowed to shortlist based on data availability, analytical depth, and originality.

#### Prompt 3: Engineering Standards Design
> Create a master orchestrator prompt for this project that enforces TDD, conventional commits, clean layered architecture, and industry-standard git workflow with feature branches and granular commits.

**Outcome:** Created CLAUDE.md with full engineering ruleset including:
- TDD Red-Green-Refactor cycle
- Conventional commit message format
- Git Flow Lite branching strategy with 10 feature branches
- 60+ planned granular commits mirroring professional workflow
- Clean layered architecture (routers → services → models)
- Pre-flight checklist for every commit

#### Prompt 4: AI Endpoint Reproducibility
> The examiner needs to clone and run this without any API keys. How do I make the AI endpoint reproducible?

**Outcome:** Designed cache-first strategy — AI summaries are pre-generated and stored in the database during development. The endpoint serves cached responses by default and only calls the Claude API when a key is configured and no cache exists.

---

### Session 2 — Full API Implementation

**Date:** 2026-03-04
**Model:** Claude Sonnet 4.6
**Purpose:** Build all 11 implementation phases from scaffold to documentation

**Prompts used:**

#### Prompt 5: Project Scaffold
> Create the project scaffold: requirements.txt, Pydantic settings, SQLAlchemy database setup, FastAPI app with CORS, and health check endpoints.

**Outcome:** Phase 1 complete — requirements, config, database, main.py, health router, pushed to `feature/project-setup`.

#### Prompt 6: SQLAlchemy Data Models
> Create all data models: User, Driver, Constructor, Race, RaceResult, Prediction, Favourite. Then initialise Alembic for migrations.

**Outcome:** Phase 2 complete — 7 models with proper foreign keys and relationships, Alembic configured for autogenerate.

#### Prompt 7: JWT Authentication (TDD)
> Write failing TDD tests for registration, login, and JWT-protected routes. Then implement JWT utilities, user schemas, user service, and auth router to make them pass.

**Outcome:** Phase 3 complete — 8 tests all passing. Discovered and fixed bcrypt 5.x compatibility issue with passlib.

#### Prompt 8: Data Seeding
> Build seeding scripts to fetch drivers, constructors, and races from the Jolpica F1 API. Include a master seed.py entry point.

**Outcome:** Phase 4 complete — Scripts fetch and upsert all F1 data for seasons 2020–2024.

#### Prompt 9: Core Read Endpoints (TDD)
> Write failing tests then implement read endpoints for drivers, constructors, and races with nationality/season filtering.

**Outcome:** Phase 5 complete — 12 tests passing. Full list + detail endpoints for 3 resources.

#### Prompt 10: CRUD Endpoints (TDD)
> Write failing tests then implement full CRUD for Predictions and Favourites, both auth-protected with ownership enforcement.

**Outcome:** Phase 6 complete — 10 tests passing. 30/30 total tests.

#### Prompt 11: Analytics Endpoints (TDD)
> Write failing tests then implement analytics: constructor standings, driver standings, nationality breakdown, top winners, season summary.

**Outcome:** Phase 7 complete — 5 tests passing. 35/35 total tests.

#### Prompt 12: AI Integration (TDD)
> Write failing tests then implement cache-first AI service using Claude Haiku with deterministic fallback and AISummaryCache model.

**Outcome:** Phase 8 complete — 3 tests passing. 38/38 total tests.

#### Prompt 13: MCP Server
> Build a FastMCP server that exposes F1 data, analytics, and AI summaries as tools for Claude Desktop/Claude Code integration.

**Outcome:** Phase 9 complete — 9 tools registered and verified.

#### Prompt 14: Docker Deployment
> Create Dockerfile and docker-compose.yml so the examiner can run `docker-compose up --build` and have a fully working API.

**Outcome:** Phase 10 complete — docker-compose auto-seeds on first start.

#### Prompt 15: Documentation
> Write a comprehensive README with quick-start (Docker), manual setup, endpoint reference table, MCP configuration, and testing instructions.

**Outcome:** Phase 11 complete — README covers all usage scenarios.

---

### Session 3 — Security, Error Handling & Advanced Features

**Date:** 2026-03-05
**Model:** Claude Sonnet 4.6
**Purpose:** JWT security hardening, win probability endpoint, multi-client MCP, HTTP correctness audit

**Prompts used:**

#### Prompt 16: JWT Security Hardening
> Add JWT logout with token blacklisting, JTI claims, and key rotation support.

**Outcome:** Token blacklist table added, JTI embedded in all tokens, `SECRET_KEY_PREVIOUS` for zero-downtime key rotation. 55 tests passing.

#### Prompt 17: Win Probability Endpoint
> Add a win probability endpoint using a weighted multi-factor model: circuit win rate (40%), overall career rate (30%), recent form (20%), constructor strength (10%).

**Outcome:** `GET /api/v1/analytics/drivers/{id}/win-probability?circuit_name=...` implemented with all four factors and circuit-specific historical analysis.

#### Prompt 18: Multi-Client MCP Examples
> Create demo scripts showing the MCP SSE server used with Claude, OpenAI Agents SDK, and Google Gemini ADK.

**Outcome:** Three demo scripts in `examples/` confirming the MCP server is client-agnostic.

#### Prompt 19: HTTP Error Code Audit
> Audit all HTTP error codes — are 400/404/403 being used correctly everywhere?

**Outcome:** 8 issues found and fixed:
- Duplicate username/email: 400 → 409 Conflict
- Ownership violations: 404 → 403 Forbidden (with correct 404 for not found)
- Missing FK validation on predictions and favourites (race_id, driver_id)
- Global exception handler added to prevent stack trace leakage
- Claude API call wrapped in try/except with graceful fallback

---

### Session 4 — Frontend Dashboard & Data Pipeline

**Date:** 2026-03-06
**Model:** Claude Sonnet 4.6
**Purpose:** Build interactive frontend, extend dataset to 2000–2025, create CSV seed pipeline

**Prompts used:**

#### Prompt 20: Frontend Dashboard
> Implement a frontend to show off the API. Dark F1 theme, interactive tabs, no build step.

**Outcome:** `frontend/index.html` — single-page dashboard with 5 tabs (Win Probability, Standings, Head-to-Head, AI Summaries, Top Winners). Served at `GET /` via FastAPI `FileResponse`. Driver autocomplete on all search inputs.

#### Prompt 21: Extend Data to 2000–2025
> Update the seed script to fetch all F1 seasons from 2000 to 2025.

**Outcome:** `SEASONS_TO_SEED = list(range(2000, 2026))` with retry/backoff on 429 rate limiting. 503 races and 10,550 results across 26 seasons now in the database.

#### Prompt 22: CSV Seed Pipeline
> Create CSV files of all seeded data so the assessor can populate the database without needing the external API.

**Outcome:**
- `data/csv/` — four CSV files bundled in the repo (drivers, constructors, races, race_results)
- `scripts/export_csv.py` — dumps current DB to CSV snapshots
- `scripts/seed_from_csv.py` — fast bulk load from CSVs, no API calls
- `scripts/seed.py` updated — auto-detects CSVs and prefers them; falls back to API if missing

#### Prompt 23: Frontend Filters
> Add season/race dropdown to Win Probability (replacing free-text circuit input) and year-range filter to Head-to-Head.

**Outcome:**
- Win Probability: season select → race select (populates circuit_name automatically)
- Head-to-Head: "From year" / "To year" selects passing `?year_from=&year_to=` query params
- H2H API endpoint updated to accept and apply `year_from`/`year_to` parameters
- `GET /api/v1/drivers?name=...` partial name filter added for autocomplete

---

## AI Integration in the API

The project includes an AI-powered endpoint (`/ai/...`) that uses the Anthropic Claude API (Haiku model) to generate contextual summaries from structured database records. This represents creative application of GenAI as a first-class API feature, not merely a development aid.

### How it works:
1. Client requests a summary for a specific resource
2. API fetches structured data from the SQL database
3. Data is formatted into a contextual prompt
4. Prompt is sent to Claude Haiku via the Anthropic SDK
5. Generated narrative is returned as JSON (and cached for future requests)

### Reproducibility:
- Pre-cached summaries are seeded into the database
- No API key required to demonstrate the feature
- Fresh generation available when `ANTHROPIC_API_KEY` is configured

---

## Reflections on AI Usage

### What worked well
- Using Claude Code as a pair programmer for TDD — the red-green-refactor cycle was significantly faster with AI generating both tests and implementation
- AI was effective at auditing code for correctness issues (HTTP status codes, security gaps) that are easy to miss manually
- Architecture planning sessions produced clear, structured plans that were followed closely throughout development
- CSV pipeline suggestion was practically useful — avoids API rate limiting and makes the project self-contained for assessors

### What didn't work
- Initial data seeding hit Jolpica rate limits (429 errors) which required adding retry/backoff logic — the AI's first implementation assumed no rate limiting
- The AI initially underestimated deployment complexity, suggesting it was optional until the rubric was checked

### How AI changed my approach
- Enforced a more disciplined commit structure (conventional commits, feature branches) than I would have used alone
- Encouraged TDD — writing tests first made the implementation more reliable
- Surfaced security considerations (JWT hardening, error code correctness, CORS) that I may not have prioritised otherwise

### What I would do differently
- Start with the CSV seed pipeline earlier rather than relying on live API fetching throughout development
- Set up deployment (Railway/Heroku) earlier in the project to avoid last-minute surprises
