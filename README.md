# F1 Racing Intelligence API

A data-driven REST API built with **FastAPI** and **PostgreSQL** for querying Formula 1 statistics, managing race predictions, and generating AI-powered race narratives.

Built for COMP3011 Web Services and Web Data (University of Leeds, 2025/26).

---

## Quick Start — Docker (Recommended for Examiners)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running. Nothing else needed.

```bash
git clone https://github.com/KianThakrar/Web-Services-and-Web-Data.git
cd Web-Services-and-Web-Data
docker-compose up --build
```

**What happens on first run:**
1. PostgreSQL starts inside Docker (no local database installation needed)
2. F1 data is automatically fetched from the Jolpica API and seeded — **this takes ~60 seconds, please wait**
3. The API starts at **http://localhost:8000**

**Once running:**
- Interactive API docs: **http://localhost:8000/docs**
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

The seed script fetches ~100 races across 5 seasons from an external API and prints progress as it goes. Wait up to 90 seconds. You will see `✓ Seed complete.` when it finishes, followed by `Uvicorn running on http://0.0.0.0:8000`.

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

python -m scripts.seed          # ~60 seconds

uvicorn app.main:app --reload
```

---

## Running Tests

Tests use SQLite in-memory — no PostgreSQL or Docker required.

```bash
source venv/bin/activate
pytest tests/ -v
```

All 55 tests should pass.

---

## API Endpoints

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
| GET | `/api/v1/drivers` | List all drivers (filter: `?nationality=British`) |
| GET | `/api/v1/drivers/{id}` | Get driver by ID |

### Constructors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/constructors` | List all constructors (filter: `?nationality=German`) |
| GET | `/api/v1/constructors/{id}` | Get constructor by ID |

### Races
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/races` | List all races (filter: `?season=2024`) |
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
| GET | `/api/v1/analytics/drivers/{id}/vs/{id2}` | Head-to-head career comparison |
| GET | `/api/v1/analytics/drivers/{id}/circuits/{name}` | Driver circuit performance history |
| GET | `/api/v1/analytics/constructors/era-dominance` | Constructor dominance by decade |
| GET | `/api/v1/analytics/drivers/{id}/win-probability` | Win probability model (weighted) |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ai/races/{id}/summary` | AI-generated race narrative (cache-first) |

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

---

## MCP Server

The project includes an MCP (Model Context Protocol) server for integration with AI clients like Claude Desktop and Claude Code.

### Tools available (10 tools):
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
├── examples/           # Multi-client MCP demo scripts
│   ├── mcp_claude_demo.py
│   ├── mcp_openai_demo.py
│   └── mcp_gemini_demo.py
├── scripts/            # Data seeding and utility scripts
├── tests/              # Pytest test suite (55 tests)
├── alembic/            # Database migrations
├── docs/               # API documentation PDF
├── mcp_server.py       # MCP server (stdio + SSE transport)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Data Source

Race data is sourced from the [Jolpica F1 API](https://api.jolpi.ca/ergast/f1/) (Ergast-compatible), a free and publicly available Formula 1 dataset covering all seasons from 1950 to present. Seasons 2020–2024 are seeded (~100 races, ~2000 results).
