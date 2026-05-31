# Analysing Allan

An AI-powered Garmin activity analysis platform. Sync workouts from Garmin Connect, analyse heart rate profiles with Claude, and explore your training data through an MCP tool server.

![Architecture](docs/architecture.png)

## Architecture

```
┌──────────────────────────────────────────────────┐
│                   Frontend                       │
│          Vite + React + Tailwind                 │
│              http://localhost:5173                │
└──────────────────────┬───────────────────────────┘
                       │ HTTP
┌──────────────────────▼───────────────────────────┐
│              Backend (FastAPI + FastMCP)          │
│              http://localhost:8000                │
│                                                   │
│  ┌─────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Garmin Tools │  │ HR Analysis│  │ DB Access │  │
│  └─────────────┘  └────────────┘  └───────────┘  │
└─────────┬───────────────────────────┬─────────────┘
          │                           │
┌─────────▼─────────┐     ┌──────────▼──────────┐
│   Garmin Connect   │     │  PostgreSQL (Neon)   │
│   (garminconnect)  │     │  Serverless DB       │
└───────────────────┘     └─────────────────────┘

┌──────────────────────────────────────────────────┐
│              ZeroClaw AI Agent                   │
│              http://localhost:8080                │
│         (Discord / CLI chat interface)           │
└──────────────────────────────────────────────────┘
```

## Components

### Backend (`backend/`)

FastAPI server with an MCP (Model Context Protocol) interface exposing Garmin analysis tools:

| Tool                                                   | Description                                                                            |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| `sync_garmin_activities(limit)`                        | Fetches latest activities, metrics, and splits from Garmin Connect                     |
| `update_workout_metadata(id, is_intervals, structure)` | Classifies workout structure (intervals, etc.)                                         |
| `analyze_hr_profile(id)`                               | Generates HR plot → sends to Anthropic Claude for visual analysis → saves HR profile   |
| `get_activity_summary(id?, limit, type, hr_buckets)`   | Lists recent activities or returns full condensed view with stats, splits, and HR data |

**Stack:** Python, FastAPI, FastMCP, SQLAlchemy, PostgreSQL (Neon), Garmin Connect API, Anthropic Claude, Matplotlib

### Frontend (`frontend/`)

React + Vite dashboard for exploring the platform's capabilities.

**Stack:** React 19, Vite 8, Tailwind CSS 4, Recharts, TanStack React Query, Lucide icons

### ZeroClaw (`zeroclaw/`)

AI agent runtime that connects to the backend's MCP interface, providing a Discord and CLI chat interface for interacting with the system.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (optional, for running the full stack)
- A [Neon](https://neon.tech) PostgreSQL database
- A [Garmin Connect](https://connect.garmin.com) account
- An [Anthropic](https://anthropic.com) API key

### Setup

1. **Clone and configure**

```bash
git clone <repo-url>
cd garmin-analysis
cp .env.example .env
```

2. **Set environment variables** in `.env`:

```ini
DATABASE_URL=postgresql://...
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_garmin_password
ANTHROPIC_API_KEY=sk-ant-...
```

3. **Run with Docker Compose** (starts backend + ZeroClaw):

```bash
docker compose up -d --build
```

4. **Run frontend separately**:

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Running Backend Directly (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.app:app --reload --port 8000
```

### Running Batch Analysis

```bash
cd backend
python scripts/batch_analyze_hr.py [limit=10]
```

Finds recent activities without an HR profile, generates plots, sends them to Claude, and saves analysis to the database.

## Database

The `activities` table stores:

- Core stats (HR, power, cadence, training effect, elevation)
- Raw Garmin API responses, 1-second metrics, and lap splits
- User-classified metadata (interval flags, workout structure)
- Anthropic-generated HR profile summaries

Migrations managed via Alembic (`backend/alembic/`).

## Project Structure

```
garmin-analysis/
├── backend/
│   ├── app/
│   │   ├── app.py              # FastAPI server entrypoint
│   │   ├── mcp/                # MCP tool server (FastMCP)
│   │   ├── models/             # SQLAlchemy models
│   │   ├── clients/            # External API clients (Garmin)
│   │   ├── services/           # Business logic (HR visual analysis)
│   │   ├── core/               # Config, database setup
│   │   └── tools/              # MCP tool implementations
│   ├── scripts/                # Batch processing scripts
│   └── alembic/                # DB migrations
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   └── data/               # Mock data
│   └── ...
├── zeroclaw/                   # AI agent runtime
├── docker-compose.yml          # Backend + ZeroClaw orchestration
└── .env                        # Environment variables
```
