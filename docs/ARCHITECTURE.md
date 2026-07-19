# StadiumMind AI — Architecture

This document explains **how** the system is built and **why** it is built that
way, with an emphasis on object-oriented design and software-engineering
discipline.

## 1. Layered architecture

The backend is split into layers that depend only on the layers below them.
Each layer is independently testable.

```
 api/          FastAPI gateway, schemas, auth, WebSocket   (delivery)
   │
 agents/       OOP multi-agent orchestrator                (application / AI)
   │
 simulation/ · ml/ · optimization/ · llm/                  (domain services)
   │
 core/         config, domain models, venue graph          (domain)
   │
 infra/        message bus, cache, repository               (infrastructure)
```

Dependencies point **inward**: `agents` and `simulation` depend on `core`,
never the reverse. The web framework lives only in `api/`, so the entire
"brain" of the product can be exercised with plain Python objects in a test.

## 2. Key OOP design decisions

### Strategy pattern — pluggable implementations behind interfaces
Three infrastructure concerns and the LLM are all abstract interfaces with
interchangeable concrete strategies:

| Interface        | Production strategy | Fallback strategy      |
|------------------|---------------------|------------------------|
| `LLMAdapter`        | `GeminiLLM`              | `MockLLM`              |
| `MatchProvider`     | `FootballDataProvider`   | `MockMatchProvider`    |
| `DirectionsProvider`| `GoogleDirectionsProvider`| `HaversineDirections` |
| `MessageBus`        | `KafkaBus`               | `InMemoryBus`          |
| `KeyValueStore`     | `RedisStore`             | `InMemoryStore`        |
| `Repository`        | `SqlRepository`          | `InMemoryRepository`   |

A `build_*` factory reads `Settings` and returns the right strategy. Callers
depend only on the interface — this is the Dependency Inversion Principle, and
it is what lets the whole system run and test offline.

### Template Method + Strategy — the agent hierarchy
`Agent` is an abstract base class that defines the contract
(`analyze`, `can_handle`, `handle_query`) and provides the shared
`explain()` helper (LLM-backed, with graceful fallback). Six concrete agents —
`CrowdAgent`, `NavigationAgent`, `EmergencyAgent`, `AccessibilityAgent`,
`TransportAgent`, `SustainabilityAgent` — each own a single domain. Adding a
new capability means writing one subclass and registering it: the
**Open/Closed Principle** in practice.

### Composition root — one place that wires everything
`StadiumService` composes the simulator, orchestrator, repository, cache and
bus, and exposes coarse use-cases. The FastAPI routes are thin adapters over
it, and a test spins up the whole system in a single line.

### Immutable configuration
`Settings` is a frozen dataclass built once from the environment and cached.
Tests construct their own `Settings` to override any value — no global mutation,
no hidden `os.getenv` calls scattered through the code.

## 3. The AI orchestration flow

**Proactive** (`AIOrchestrator.analyze`): build one shared `AgentContext` from
the current crowd snapshot, fan it out to every agent, collect recommendations,
de-duplicate and rank them by `severity × confidence`. A failing agent is
isolated so it can never break the cycle.

**Reactive** (`AIOrchestrator.handle_query`): route an intent (e.g. `navigate`,
`best_exit`) to the first agent that declares it can handle it.

Every `Recommendation` carries an `explanation` and a `confidence`, and starts
life `approved = None` — embodying *explain before recommending* and
*human approval for operational actions*.

## 4. Data & intelligence layers

- **Simulation** (`StadiumSimulator`) — a deterministic, seeded, discrete-time
  crowd model that is the live data source for the demo. Occupancy relaxes
  toward type-specific targets, so baseline crowds are believable and injected
  surges produce clear hotspots.
- **ML forecasting** (`CrowdPredictor`) — gradient-boosted regression
  (XGBoost/LightGBM) trained on synthetic-but-physical data, with a closed-form
  linear fallback. Identical public API regardless of backend.
- **Operations research** — Erlang-C queueing for wait-time estimates,
  Dijkstra-based congestion-aware routing, and integer-LP volunteer allocation
  (with a provably-equivalent greedy fallback for this problem shape).
- **LLM** — Gemini for natural-language explanations, mocked deterministically
  in tests.
- **External data** (`integrations/`) — `MatchProvider` pulls the live fixture
  from **football-data.org** (`X-Auth-Token`); `DirectionsProvider` gets
  walking routes from the **Google Maps Directions API**. Both are HTTP-mocked
  in tests and degrade to deterministic offline fallbacks if a key or the
  network is missing.

## 4.1 Real-world geolocation

The `Venue` is anchored to a real location (default **MetLife Stadium**, the
FIFA World Cup 2026 final venue). An equirectangular projection maps each
normalised zone coordinate to real `lat/lng`, and landmarks such as the
Meadowlands Rail Station are pinned to their true coordinates. The frontend
`GoogleStadiumMap` renders these on a satellite Google Map with congestion-
coloured markers and Directions-API walking routes to gates/exits/transit;
it falls back to the SVG `StadiumMap` when no browser key is set.

## 5. SDLC & quality practices

- **Testing** — 68 tests split into `tests/unit` (pure logic: models, venue,
  queueing, allocation, routing, predictor, simulation, LLM, auth, infra,
  agents) and `tests/system` (FastAPI `TestClient` API tests plus a single
  end-to-end test that walks the full 7-step demo story). Run with `pytest`.
- **Determinism** — seeded RNG and a forced `MockLLM` in tests make every run
  reproducible; there are no network calls in the test suite.
- **Error handling** — a small domain exception hierarchy
  (`StadiumMindError` → `ConfigurationError`, `AgentError`, `LLMError`,
  `OptimizationError`, `RepositoryError`) maps cleanly onto HTTP statuses.
- **Documentation** — every module has a module docstring explaining its role;
  public classes and non-trivial functions are documented.
- **Resilience** — optional dependencies and services degrade gracefully; one
  bad subscriber, agent, or LLM call cannot crash the pipeline.
- **Separation of concerns** — wire schemas (`api/schemas.py`) are distinct
  from domain models (`core/models.py`) so transport and domain evolve
  independently.

## 6. Extending the system

| To add…                    | Do this                                                        |
|----------------------------|----------------------------------------------------------------|
| A new AI capability        | Subclass `Agent`, implement `analyze`/`handle_query`, register in `AIOrchestrator`. |
| A new persistence backend  | Implement `Repository`, add a branch in `build_repository`.    |
| A new zone/venue           | Extend `build_default_venue()` or construct a `Venue`.         |
| A different LLM vendor      | Implement `LLMAdapter`, select it in `build_llm`.              |

## 7. Roadmap (post-MVP)

Digital twin & IoT sensor ingestion · drone/robotics integration · real indoor
positioning (BLE/UWB) · multilingual voice assistant · reinforcement-learning
crowd control · full observability (Grafana/Prometheus dashboards).
