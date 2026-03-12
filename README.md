# F1 Racing Intelligence API

A data-driven REST API built with **FastAPI** and **PostgreSQL** for querying Formula 1 statistics, managing race predictions, and generating AI-powered race narratives. Includes an interactive frontend dashboard and an MCP server for AI client integration.

Built for COMP3011 Web Services and Web Data (University of Leeds, 2025/26).

**Live deployment:** https://api-production-61d4.up.railway.app/
**Live API docs:** https://api-production-61d4.up.railway.app/docs

---

## Quick Start — Docker (Recommended for Examiners)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running. Nothing else needed.

```bash
git clone https://github.com/KianThakrar/Web-Services-and-Web-Data.git
cd Web-Services-and-Web-Data
cp .env.example .env
docker-compose up --build
```

> `.env` provides the database password and JWT secret. The defaults in `.env.example` work out of the box — no editing required.

**What happens on first run:**
1. PostgreSQL starts inside Docker (no local database installation needed)
2. F1 data is loaded from the bundled CSV files — **this takes ~10 seconds**
3. The API and frontend start at **http://localhost:8000**

**Once running:**
- Interactive dashboard: **http://localhost:8000/**
- API documentation (Swagger): **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

> The AI race summary endpoint works without an `ANTHROPIC_API_KEY` — summaries use a deterministic fallback and are cached on first request.

**To stop:**
```bash
docker-compose down        # stop (data is preserved)
docker-compose down -v     # stop and wipe database (fresh start next run)
```

---

## Troubleshooting

**Port 8000 already in use**

Edit `docker-compose.yml`, change `"8000:8000"` to `"8001:8000"`, then visit `http://localhost:8001`.

**Seeding appears to hang**

The seed script loads from `data/csv/` (bundled in the repo). It should complete in under 15 seconds. You will see `✓ CSV seed complete.` followed by `Uvicorn running on http://0.0.0.0:8000`.

**"Connection refused" when visiting localhost:8000**

The API only starts after seeding completes. Keep watching the Docker logs.

**Starting completely fresh**

```bash
docker-compose down -v     # removes the database volume
docker-compose up --build  # rebuilds and reseeds from scratch
```

---

## Manual Setup (Local PostgreSQL)

### Prerequisites
- Python 3.12+
- PostgreSQL running locally

### Steps

```bash
git clone https://github.com/KianThakrar/Web-Services-and-Web-Data.git
cd Web-Services-and-Web-Data

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set DATABASE_URL to your local PostgreSQL instance

createdb f1_racing_db           # or create via pgAdmin / psql

alembic upgrade head

python -m scripts.seed          # loads from data/csv/ — completes in ~10s

uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/** for the dashboard.

---

## Running Tests

Tests use a file-backed SQLite database (`test.db`) that is recreated for each test
function — no PostgreSQL or Docker required.

```bash
source venv/bin/activate
DEBUG=false pytest tests/ -v
```

All 69 tests should pass. Tests are independent of Docker and PostgreSQL — they use an in-memory SQLite database.

---

## API Endpoints

### Utility
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Interactive frontend dashboard (SPA) |
| GET | `/api` | API info and links |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and receive JWT token |
| GET | `/api/v1/auth/me` | Get current user profile |
| POST | `/api/v1/auth/logout` | Revoke current token (blacklists JTI) |

### Drivers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/drivers` | List drivers (filter: `?nationality=British&name=hamilton`, paginate: `?limit=20&offset=0`) |
| GET | `/api/v1/drivers/{id}` | Get driver by ID |

### Constructors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/constructors` | List constructors (filter: `?nationality=German`, paginate: `?limit=50&offset=0`) |
| GET | `/api/v1/constructors/{id}` | Get constructor by ID |

### Races
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/races` | List races (filter: `?season=2024`, paginate: `?limit=50&offset=0`) |
| GET | `/api/v1/races/{id}` | Get race by ID |

### Predictions (Auth required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/predictions` | Create a prediction |
| GET | `/api/v1/predictions` | List your predictions |
| PUT | `/api/v1/predictions/{id}` | Update a prediction |
| DELETE | `/api/v1/predictions/{id}` | Delete a prediction |

### Favourites (Auth required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/favourites` | Add a driver to favourites |
| GET | `/api/v1/favourites` | List your favourites |
| DELETE | `/api/v1/favourites/{id}` | Remove a favourite |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/drivers/standings?season=2024` | Driver championship standings |
| GET | `/api/v1/analytics/constructors/standings?season=2024` | Constructor standings |
| GET | `/api/v1/analytics/drivers/nationalities` | Driver nationality breakdown |
| GET | `/api/v1/analytics/drivers/top-winners` | All-time top race winners |
| GET | `/api/v1/analytics/seasons/{season}/summary` | Season summary statistics |
| GET | `/api/v1/analytics/drivers/{id}/vs/{id2}?year_from=2010&year_to=2020` | Head-to-head comparison (optional year range) |
| GET | `/api/v1/analytics/drivers/{id}/circuits/{name}` | Driver circuit performance history |
| GET | `/api/v1/analytics/constructors/era-dominance` | Constructor dominance by decade |
| GET | `/api/v1/analytics/drivers/{id}/win-probability?circuit_name=Monza` | Win probability model (optional circuit) |
| GET | `/api/v1/analytics/races/{id}/win-probabilities` | Normalised win probabilities for all drivers in a race |

### Weather × Performance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/weather/circuits/{name}` | Circuit weather profile (avg temp, rain %, conditions history) |
| GET | `/api/v1/analytics/weather/drivers/{id}` | Driver wet vs dry performance (win rate, avg finish, points delta) |
| GET | `/api/v1/analytics/weather/races/{id}` | Race weather conditions + full results |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ai/races/{id}/summary` | AI-generated race narrative (cache-first) |

---

## HTTP Status Codes

The API uses semantically correct status codes throughout:

| Code | Meaning | When used |
|------|---------|-----------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation errors |
| 401 | Unauthorised | Missing or invalid JWT |
| 403 | Forbidden | Authenticated but not owner of resource |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Duplicate username, email, or favourite |
| 422 | Unprocessable | Pydantic schema validation failure |
| 429 | Too Many Requests | Rate limit exceeded on auth endpoints |
| 500 | Internal Server Error | Unhandled exceptions (global handler) |

---

## AI Integration

The `/api/v1/ai/races/{id}/summary` endpoint uses a **cache-first strategy**:

1. Checks `ai_summary_cache` table — returns instantly if found (`"cached": true`)
2. If `ANTHROPIC_API_KEY` is set — calls Claude Haiku for a live summary
3. If no API key — generates a deterministic fallback summary

This ensures **full reproducibility** for examiners cloning without an API key.

---

## Security

- JWT authentication with bcrypt password hashing
- JWT token revocation via JTI blacklist — logout invalidates the token immediately
- JWT key rotation support via `SECRET_KEY_PREVIOUS` for zero-downtime key changes
- Rate limiting on auth endpoints (10 req/min per IP)
- Security response headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
- Input validation: username 3–50 chars alphanumeric, password 8–72 chars
- Configurable CORS origins (no wildcard)
- Global exception handler prevents stack traces leaking to clients

---

## Frontend Dashboard

**Live:** https://api-production-61d4.up.railway.app/ — or locally at http://localhost:8000/

An interactive dashboard served directly by FastAPI (`frontend/index.html` + `frontend/styles.css`). No build step required — vanilla JS with Inter font, served as static files.

| Tab | What it shows |
|-----|--------------|
| **Win Probability** | Select a season + race → ranked table of all drivers with normalised win probabilities (logistic regression, sums to 100%) |
| **Standings** | Championship standings table for any season 2000–2025 |
| **Head-to-Head** | Two-driver career comparison with optional year-range filter |
| **Weather Impact** | Driver wet vs dry performance (win rate, podiums, DNFs) + race-level weather conditions viewer |
| **AI Summaries** | Claude Haiku–generated race narratives with Cached / Live AI badge |
| **Top Winners** | All-time race winners leaderboard (top 10/20/50) |

---

## Data

Race data covers **seasons 2000–2025** sourced from the [Jolpica F1 API](https://api.jolpi.ca/ergast/f1/) (Ergast-compatible). Weather data is sourced from the [Open-Meteo Archive API](https://open-meteo.com/) (free, no API key):

| Table | Rows | Source |
|-------|------|--------|
| Drivers | 874 | Jolpica F1 API |
| Constructors | 214 | Jolpica F1 API |
| Races | 503 | Jolpica F1 API |
| Race Results | 10,550 | Jolpica F1 API |
| Weather Cache | 500 | Open-Meteo Archive API |

All data is bundled as CSV files in `data/csv/` so the database can be seeded instantly without any external API access. To refresh or extend the data:

```bash
python -m scripts.seed --api          # re-fetch F1 data from Jolpica API
python -m scripts.export_csv          # export updated DB back to CSV
python -m scripts.fetch_weather       # re-fetch weather from Open-Meteo → data/csv/weather.csv
```

---

## MCP Server

The project includes an MCP (Model Context Protocol) server for integration with AI clients like Claude Desktop and Claude Code.

### Tools available (13 tools):
- `search_drivers` — search drivers by name or nationality
- `get_driver_details` — full driver profile
- `list_races` — races by season
- `get_race_results` — finishing order for a race
- `get_race_ai_summary` — AI narrative for a race
- `get_driver_standings` — season championship standings
- `get_constructor_standings_tool` — constructor standings
- `get_season_summary_tool` — season statistics
- `get_all_time_top_winners` — all-time win leaderboard
- `get_driver_win_probability` — win probability model (circuit + career + form + constructor)
- `get_circuit_weather` — historical weather profile for a circuit
- `get_driver_wet_vs_dry` — driver performance in wet vs dry conditions
- `get_race_weather` — weather conditions and results for a specific race

### Verify the MCP server:
```bash
python -m scripts.test_mcp           # lists all tools and tests DB connectivity
```

### Run the MCP server:

**stdio transport** (Claude Desktop / Claude Code):
```bash
python mcp_server.py
```

**SSE transport** (HTTP — for any MCP client):
```bash
python mcp_server.py --sse          # serves on http://localhost:3001/sse
```

### Add to Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "f1-racing": {
      "command": "python",
      "args": ["/path/to/Web-Services-and-Web-Data/mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/f1_racing_db"
      }
    }
  }
}
```

### Multi-Client MCP Demo

The same SSE MCP server works with multiple AI clients — no server changes required.
See [`examples/`](examples/) for ready-to-run demos:

| Client | File | SDK |
|--------|------|-----|
| Anthropic Claude | `examples/mcp_claude_demo.py` | `anthropic` + `mcp` |
| OpenAI Agents | `examples/mcp_openai_demo.py` | `openai-agents` |
| Google Gemini | `examples/mcp_gemini_demo.py` | `google-adk` |

```bash
# Start SSE server first
python mcp_server.py --sse

# Then run any demo
python examples/mcp_claude_demo.py
python examples/mcp_openai_demo.py
python examples/mcp_gemini_demo.py
```

---

## Documentation

- [API Documentation (PDF)](docs/api_documentation.pdf)

Full endpoint reference including parameters, request/response schemas, authentication, and error codes.

---

## Project Structure

```
.
├── app/
│   ├── auth/           # JWT utilities (JTI, key rotation, blacklist)
│   ├── models/         # SQLAlchemy ORM models
│   ├── routers/        # FastAPI route handlers
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic layer
│   ├── config.py       # Pydantic settings
│   ├── database.py     # SQLAlchemy engine and session
│   └── main.py         # FastAPI application entry point
├── data/
│   └── csv/            # Bundled CSV snapshots (874 drivers, 503 races, 10,550 results, 500 weather)
├── examples/           # Multi-client MCP demo scripts
│   ├── mcp_claude_demo.py
│   ├── mcp_openai_demo.py
│   └── mcp_gemini_demo.py
├── frontend/
│   ├── index.html      # Single-page dashboard (served at GET /)
│   └── styles.css      # External stylesheet (served at /static/styles.css)
├── scripts/            # Data seeding and utility scripts
│   ├── seed.py         # Master entry point (auto-detects CSV vs API)
│   ├── seed_from_csv.py# Fast CSV-based seed (no API calls)
│   ├── fetch_weather.py# Fetch weather from Open-Meteo → data/csv/weather.csv
│   ├── test_mcp.py     # MCP server verification script
│   ├── export_csv.py   # Export DB to CSV snapshots
│   ├── seed_drivers.py # Fetch drivers from Jolpica API
│   ├── seed_constructors.py
│   └── seed_races.py   # Fetch races 2000–2025 from Jolpica API
├── tests/              # Pytest test suite (69 tests)
├── alembic/            # Database migrations
├── docs/               # API documentation PDF
├── mcp_server.py       # MCP server (stdio + SSE transport)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
