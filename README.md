# F1 Racing Intelligence API

A data-driven REST API built with **FastAPI** and **PostgreSQL** for querying Formula 1 statistics, managing race predictions, and generating AI-powered race narratives.

Built for COMP3011 Web Services and Web Data (University of Leeds, 2025/26).

---

## Quick Start (Docker — Recommended)

```bash
git clone https://github.com/KianThakrar/Web-Services-and-Web-Data.git
cd Web-Services-and-Web-Data
cp .env.example .env
docker-compose up --build
```

The API will be available at **http://localhost:8000**
Interactive docs at **http://localhost:8000/docs**

> On first start, the container automatically seeds all F1 data from the Jolpica API (drivers, constructors, races 2020–2024). This takes ~30 seconds.

---

## Manual Setup (Local PostgreSQL)

### Prerequisites
- Python 3.12+
- PostgreSQL running locally

### Steps

```bash
# 1. Clone and enter the repo
git clone https://github.com/KianThakrar/Web-Services-and-Web-Data.git
cd Web-Services-and-Web-Data

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your PostgreSQL instance

# 5. Create the database
createdb f1_racing_db            # or use pgAdmin / psql

# 6. Run migrations
alembic upgrade head

# 7. Seed data
python -m scripts.seed

# 8. Start the API
uvicorn app.main:app --reload
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and receive JWT token |
| GET | `/api/v1/auth/me` | Get current user profile |

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

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ai/races/{id}/summary` | AI-generated race narrative (cache-first) |

---

## MCP Server

The project includes an MCP (Model Context Protocol) server for integration with AI clients like Claude Desktop and Claude Code.

### Tools available:
- `search_drivers` — search drivers by name or nationality
- `get_driver_details` — full driver profile
- `list_races` — races by season
- `get_race_results` — finishing order for a race
- `get_race_ai_summary` — AI narrative for a race
- `get_driver_standings` — season championship standings
- `get_constructor_standings_tool` — constructor standings
- `get_season_summary_tool` — season statistics
- `get_all_time_top_winners` — all-time win leaderboard

### Run the MCP server:
```bash
python mcp_server.py
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

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_auth.py -v
```

All tests use SQLite in-memory — no PostgreSQL required for testing.

---

## Project Structure

```
.
├── app/
│   ├── auth/           # JWT utilities
│   ├── models/         # SQLAlchemy ORM models
│   ├── routers/        # FastAPI route handlers
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic layer
│   ├── config.py       # Pydantic settings
│   ├── database.py     # SQLAlchemy engine and session
│   └── main.py         # FastAPI application entry point
├── scripts/            # Data seeding scripts
├── tests/              # Pytest test suite
├── alembic/            # Database migrations
├── mcp_server.py       # MCP server
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## AI Integration

The `/api/v1/ai/races/{id}/summary` endpoint uses a **cache-first strategy**:

1. Checks `ai_summary_cache` table — returns instantly if found
2. If `ANTHROPIC_API_KEY` is set — calls Claude Haiku for a live summary
3. If no API key — generates a deterministic fallback summary

This ensures **full reproducibility** for examiners cloning without an API key.

---

## Data Source

Race data is sourced from the [Jolpica F1 API](https://api.jolpi.ca/ergast/f1/) (Ergast-compatible), a free and publicly available Formula 1 dataset covering all seasons from 1950 to present.
