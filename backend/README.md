# StadiumMind AI — Backend

FastAPI service + OOP multi-agent AI orchestrator. Runs fully offline with
zero configuration; every external integration is optional.

## Run

```bash
pip install -r requirements.txt
python -m pytest -q                        # 68 tests
uvicorn stadiummind.main:app --reload      # http://localhost:8000/docs
```

## Package map

| Module                    | Responsibility                                             |
|---------------------------|------------------------------------------------------------|
| `core/`                   | `Settings`, domain models, `Venue` graph, exceptions       |
| `infra/`                  | `MessageBus`, `KeyValueStore`, `Repository` (+ fallbacks)  |
| `simulation/`             | `StadiumSimulator` — deterministic crowd feed              |
| `ml/`                     | `CrowdPredictor` — XGBoost/LightGBM + linear fallback      |
| `optimization/`           | queueing (Erlang-C), routing (Dijkstra), LP allocation     |
| `llm/`                    | `LLMAdapter` — `GeminiLLM` / `MockLLM`                     |
| `integrations/`           | `MatchProvider` (football-data.org), `DirectionsProvider` (Google Maps) + fallbacks |
| `agents/`                 | `Agent` base + 6 agents + `AIOrchestrator`                 |
| `api/`                    | FastAPI app, schemas, auth, WebSocket, `StadiumService`    |

## HTTP API

| Method & path                                   | Purpose                                    | Auth        |
|-------------------------------------------------|--------------------------------------------|-------------|
| `GET  /api/health`                              | status, match minute, active LLM/ML backend| none        |
| `POST /api/auth/login`                          | issue a role token                         | none        |
| `GET  /api/venue`                               | venue graph + geo anchor + zone lat/lng    | none        |
| `GET  /api/match`                               | current match (football-data.org / mock)   | none        |
| `GET  /api/directions?origin=&destination=`     | walking route between zones (Google/haversine)| none     |
| `GET  /api/crowd/heatmap`                       | per-zone occupancy + level + lat/lng       | none        |
| `POST /api/crowd/tick`                          | advance the simulation one minute          | none        |
| `POST /api/crowd/surge?zone_id=&people=`        | inject a crowd surge (demo)                | none        |
| `GET  /api/alerts`                              | congestion alerts                          | none        |
| `GET  /api/ai/recommendations`                  | proactive ranked recommendations           | none        |
| `GET  /api/ai/intents`                          | supported reactive intents                 | none        |
| `POST /api/ai/query`                            | reactive query (navigate, best_exit, …)    | none        |
| `POST /api/ai/recommendations/{id}/decision`    | approve/reject a recommendation            | ops/security|
| `POST /api/incidents`                           | report an incident                         | ops/sec/med |
| `GET  /api/incidents`                           | list incidents                             | none        |
| `POST /api/incidents/{id}/resolve`              | resolve an incident                        | ops/sec/med |
| `WS   /ws/live`                                 | live heatmap + recommendation stream       | none        |

## Enabling real services

Set `GEMINI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, or
`KAFKA_BOOTSTRAP_SERVERS` and install the matching optional dependency from
`requirements.txt`. See the root README for the full table.

## Testing

```bash
python -m pytest -q            # all
python -m pytest tests/unit    # unit only
python -m pytest tests/system  # API + end-to-end demo story
```
