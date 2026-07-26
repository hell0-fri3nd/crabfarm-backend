# CrabFarm Backend — Architecture

## Overview

CrabFarm Backend is a FastAPI-powered API server for managing crab farm operations. It provides RESTful endpoints for crab data management, real-time sensor monitoring via WebSockets, automated feeding scheduling, LSTM-based growth prediction, and an AI assistant for mud crab farming knowledge.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| Framework | FastAPI (ASGI) |
| Server | Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Database | MySQL 8.0 (via PyMySQL) |
| Migrations | Alembic |
| Auth | PyJWT (HTTP-only cookies) |
| Scheduler | APScheduler (async) |
| ML | PyTorch 2.10 (LSTM) |
| AI Assistant | LangChain + Groq (LLaMA 3.1) |
| Real-time | WebSockets |
| Containerization | Docker / Docker Compose |

---

## Folder Structure

```
crabfarm-backend/
│
├── App.py                          # Main entry point — FastAPI app with lifespan, CORS, router registration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Production Docker image
├── compose.yaml                    # Docker Compose (app + MySQL)
├── compose.debug.yaml              # Debug Compose (with debugpy)
├── .env                            # Environment variables (DB, JWT, ESP32, Groq, etc.)
├── alembic.ini                     # Alembic migration config
│
├── alembic/                        # Database migrations
│   ├── env.py                      #   Alembic environment setup
│   ├── script.py.mako              #   Migration template
│   └── versions/                   #   Versioned migration scripts
│       ├── fb3179d6205f_migration_table.py         # Initial schema
│       ├── 33e05a5b7d66_migration_seeder.py        # Seed data
│       ├── aefb5bbab48e_activity_logs_tables.py    # Activity logs
│       ├── 24e806715c23_your_new_tables.py         # (duplicate seeder)
│       └── c1c5697e9d49_sensor_logs.py             # Sensor logs
│
├── database/                       # Database connection
│   └── database.py                 #   Engine, SessionLocal, get_db()
│
├── models/                         # SQLAlchemy ORM models (7 tables)
│   ├── __init__.py                 #   Re-exports all models + Base
│   ├── users.py                    #   Users (id, name, email, password, pin, roles)
│   ├── crab.py                     #   Crab (id, name, group_by)
│   ├── crab_logs.py                #   Crab growth logs (type: prediction/actual, width, weight)
│   ├── sensor_logs.py              #   Water sensor logs (6 sensor types, status: NORMAL/WARNING/DANGER)
│   ├── activity_logs.py            #   User activity audit trail
│   ├── calibration_settings.py     #   Sensor calibration thresholds
│   └── scheduler_settings.py       #   Feeding/valve schedules (daily/weekly/monthly/custom)
│
├── routers/                        # API route handlers (7 REST + 1 WebSocket)
│   ├── __init__.py                 #   Re-exports all routers
│   ├── auth.py                     #   POST /login, /pin, /logout, GET /status
│   ├── crabs.py                    #   CRUD crabs + growth logs
│   ├── settings.py                 #   CRUD scheduler settings
│   ├── control.py                  #   ESP32 hardware control (start/stop/pause feeding, dispensers)
│   ├── prediction.py               #   ML growth prediction endpoints
│   ├── gateway.py                  #   API gateway proxy to Raspberry Pi
│   ├── activity_logs.py            #   Activity + sensor log retrieval
│   └── websockets.py               #   WebSocket endpoint for real-time sensor data
│
├── services/                       # Business logic layer
│   ├── __init__.py                 #   Re-exports all services
│   ├── jwt_manager.py              #   JWT token creation/validation + custom decorators
│   ├── esp32_config.py             #   HTTP client for ESP32 (feeder, dispenser, relay control)
│   ├── crab_prediction.py          #   LSTM neural network model (load/save, predict, train)
│   ├── scheduler_manager.py        #   APScheduler job manager (load, create, trigger)
│   ├── sensor_analyzer.py          #   Sensor trend analysis, anomaly detection, risk scoring
│   ├── web_sockets.py              #   WebSocket connection manager (connect, disconnect, broadcast)
│   ├── model/                      #   Saved ML model weights
│   │   └── crab_model.pt           #     Pre-trained PyTorch LSTM weights
│   ├── train/                      #   Training data
│   │   └── crab_logs Mar 23 - Mar 29 2026.csv
│   └── agents/                     #   AI Assistant (LangChain + Groq)
│       ├── __init__.py             #     AiAssistant class (intent classification + chat)
│       └── prompts/                #     LLM prompt templates
│           ├── intentions_prompt.py
│           ├── knowledge_prompt.py
│           └── sensor_analyze_prompt.py
│
└── (config) .env                   # All environment configuration
```

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI App (App.py)                      │
│         CORS · Lifespan · Router Registration               │
├─────────────────────────────────────────────────────────────┤
│                        Routers                              │
│    auth · crabs · settings · control · prediction           │
│    gateway · activity_logs · websockets                     │
├─────────────────────────────────────────────────────────────┤
│                        Services                             │
│  JWT · ESP32 · Prediction · Scheduler · SensorAnalyzer     │
│  WebSockets · AiAssistant                                   │
├─────────────────────────────────────────────────────────────┤
│                    Models + Database                         │
│  SQLAlchemy ORM · Alembic Migrations · MySQL                │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
[ESP32 Hardware] ──HTTP──▶ [Control Router] ──▶ [ESP32Config Service]
                              ▲
[ESP32 (feeder)] ◀──HTTP── (scheduled jobs) ◀── [SchedulerManager]

[Raspberry Pi] ──HTTP──▶ [Gateway Router] ──proxy──▶ [External Service]

[React Frontend] ──HTTP──▶ [FastAPI App] ──▶ [Router] ──▶ [Service] ──▶ [DB]
                  ◀──JSON──                     │              │
                                                ├──▶ [CrabPrediction]
                                                ├──▶ [JWTManager]
                                                ├──▶ [SensorAnalyzer]
                                                └──▶ [AiAssistant] ◀──┘

[Sensor Hardware] ──WS──▶ [WebSocket Router] ──broadcast──▶ [React Clients]
                                  │
                          [sensor_logs DB insert]
```

---

## API Endpoints

All REST routes are prefixed with `/api/v1/`. WebSocket at `/ws/v1/websockets`.

| Router | Prefix | Key Endpoints |
|--------|--------|--------------|
| Auth | `/api/v1/auth` | Login, Logout, PIN verification, Token status |
| Crabs | `/api/v1/crabs` | List crabs, By group, Insert log, View logs |
| Settings | `/api/v1/settings` | CRUD scheduler schedules |
| Control | `/api/v1/controls` | ESP32 status, Start/Stop/Pause feeding, Dispensers |
| Prediction | `/api/v1/predictions` | Get/predict growth for a crab (7-day forecast) |
| Gateway | `/api/v1/gateway` | Proxy to Raspberry Pi API |
| Logs | `/api/v1/logs` | Activity logs, Sensor logs |
| WebSocket | `/ws/v1/websockets` | Real-time sensor data |

---

## Database Schema (7 Tables)

| Table | Purpose |
|-------|---------|
| `users` | Authentication (name, email, password, pin, roles) |
| `crab` | Individual crab records (name, group) |
| `crab_logs` | Growth measurements (prediction or actual, width, weight) |
| `sensor_logs` | Water quality sensor readings (6 types, status) |
| `activity_logs` | User activity audit trail |
| `calibration_settings` | Sensor calibration thresholds |
| `scheduler_settings` | Feeding/valve automation schedules |

---

## Key Design Decisions

- **Authentication**: JWT stored in HTTP-only cookies with 15-min access tokens and refresh tokens (1-day or 30-day remember-me).
- **Scheduling**: APScheduler restores all enabled schedules from the database at startup.
- **ML Model**: PyTorch LSTM with 2-input → 16-hidden → 2-output architecture for width/weight prediction.
- **AI Assistant**: LangChain routes between sensor data analysis and crab farming Q&A via Groq's LLaMA 3.1.
- **Hardware Control**: Direct HTTP to ESP32 for feeder/dispenser/relay commands.
- **Real-time**: WebSocket server ingests sensor data and broadcasts to all connected clients.
