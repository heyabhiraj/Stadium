# StadiumMind AI

A GenAI-powered operating system for **FIFA World Cup 2026** stadiums. It helps
fans, operators, volunteers, security and medical teams make better real-time
decisions across navigation, crowd management, accessibility, transport,
sustainability and emergency response.

> **Challenge brief.** Build a GenAI-enabled solution that enhances stadium
> operations and the overall tournament experience for fans, organizers,
> volunteers, or venue staff. The solution must leverage Generative AI to
> improve navigation, crowd management, accessibility, transportation,
> sustainability, multilingual assistance, operational intelligence, or
> real-time decision support during the FIFA World Cup 2026.

---

## What's in the box

```
Stadium/
├── backend/            FastAPI + OOP multi-agent orchestrator (Python)
│   ├── stadiummind/    the application package (layered - see ARCHITECTURE)
│   └── tests/          68 unit + system tests (pytest)
├── frontend/
│   ├── demo/index.html standalone, no-build interactive demo (open in a browser)
│   └── app-nextjs/      production Next.js + TypeScript + Tailwind app
└── docs/ARCHITECTURE.md design, layers, patterns and the SDLC story
```

## The product in one picture

```
              Fan Mobile App     Operations Center     Security / Medical
                      \                |                  /
                       \               |                 /
                         ====== FastAPI Gateway =========
                                       |
                              AI Orchestrator (OOP)
        Crowd · Navigation · Emergency · Accessibility · Transport · Sustainability
                                       |
        Simulation feed · ML forecasting · OR optimisation · Gemini LLM
                                       |
                 Streaming (Kafka) · Cache (Redis) · DB (SQL)
```

## Quick start (2 minutes, no keys, no services)

### 1. Try the demo instantly
Open `frontend/demo/index.html` in any browser and click **Play full demo**.
It runs the entire 7-step story offline (no backend required).

### 2. Run the backend + tests
```bash
cd backend
pip install -r requirements.txt        # core deps only; integrations optional
python -m pytest -q                    # -> 68 passed
uvicorn stadiummind.main:app --reload  # API on http://localhost:8000
```
Open http://localhost:8000/docs for the interactive OpenAPI explorer.

### 3. Run the Next.js frontend (optional)
```bash
cd frontend/app-nextjs
npm install
npm run dev                            # http://localhost:3000 (proxies /api -> :8000)
```

## Turning on the real integrations

Everything degrades gracefully to in-process implementations, so it runs with
zero configuration. Set environment variables to switch on the real thing:

| Capability        | Variable(s)                                   | Fallback when unset       |
|-------------------|-----------------------------------------------|---------------------------|
| Gemini LLM        | `GEMINI_API_KEY`, `GEMINI_MODEL`              | deterministic MockLLM     |
| Match data        | `FOOTBALL_DATA_API_KEY` (football-data.org)   | deterministic mock fixture|
| Google Maps + Directions | `GOOGLE_MAPS_API_KEY` (server), `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` (browser) | SVG map + haversine estimate |
| PostgreSQL        | `DATABASE_URL`                                | in-memory repository      |
| Redis cache       | `REDIS_URL`                                   | in-memory store           |
| Kafka streaming   | `KAFKA_BOOTSTRAP_SERVERS`                     | in-process message bus    |
| ML forecasting    | install `xgboost` / `lightgbm`                | NumPy linear fallback     |
| LP allocation     | install `pulp`                                | greedy allocator          |

The venue is geo-anchored to **MetLife Stadium** (WC 2026 final venue): every
zone, gate and exit has real lat/lng. The Google map shows the real ground with
congestion overlays and draws walking routes to exits/transit via the Directions
API; without a key it falls back to the built-in SVG map. Match data comes from
**football-data.org**; without a key a deterministic Brazil-vs-Spain fixture is
used so the UI always renders.

```bash
export GEMINI_API_KEY="your-key-here"
uvicorn stadiummind.main:app
# GET /api/health now reports  "llm": "gemini"
```

## The 7-step demo story

1. A fan opens the app and is guided to the least-crowded entrance.
2. The AI assistant recommends the quietest gate.
3. Congestion builds at Gate 3 (two buses arrive → crowd surge).
4. The operations dashboard receives an **explained** redirect recommendation and approves it.
5. A medical incident occurs; the emergency agent dispatches volunteers.
6. Nearby fans are rerouted to keep the response corridor clear.
7. After full time, the AI recommends the best exit/transport option.

This exact narrative is covered end-to-end by
`backend/tests/system/test_demo_story.py`.

## Product principles

Minimal UI · AI assists, never overwhelms · **explain before recommending** ·
mobile-first · accessibility-first · **human approval for operational actions**.

## Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - layers, OOP design, patterns, SDLC & testing.
- **[backend/README.md](backend/README.md)** - backend module map and API reference.

## License

Prototype for the FIFA World Cup 2026 GenAI challenge.
