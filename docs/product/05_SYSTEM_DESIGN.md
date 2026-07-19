# StadiumMind AI — System Design Document

Covers the target production architecture: microservices, event-driven data
platform, AI agent architecture, database schema, API contracts, frontend
architecture, security, observability and scaling. The current repository
implements a coherent MVP of this design (FastAPI modular monolith with the same
service boundaries and graceful fallbacks); this document is the north star it
grows into.

---

## 1. Architecture overview

```
                         ┌──────────────────────────────────────────┐
   Fans (mobile)  ─────► │              API Gateway / BFF            │
   Ops/Sec/Med (web) ──► │  (auth, rate-limit, routing, WebSocket)   │
   Volunteers (mobile)─► └───────────────┬──────────────────────────┘
                                         │  REST + WS
        ┌────────────────────────────────┼─────────────────────────────┐
        ▼                ▼                ▼               ▼              ▼
   Identity Svc    Venue/Maps Svc    Crowd Svc      AI Orchestrator   Notification Svc
        │                │                │               │              │
        └───────── Event Bus (Kafka) ─────────────────────┴──────────────┘
                          │  topics: crowd.readings, ops.incidents, ai.recommendations, ...
        ┌─────────────────┼───────────────────────────────────────────────┐
        ▼                 ▼                 ▼                ▼               ▼
  Ingestion Svc     Prediction Svc     Optimization Svc   LLM Gateway   Analytics Svc
  (sensors, transit, weather)          (ML: XGBoost)      (Gemini)      (warehouse)

   Stores:  PostgreSQL (system of record) · Redis (hot state) · Object store (assets/reports)
```

Two planes:
- **Real-time plane** (event bus + Redis + WebSocket) for live crowd, incidents, recommendations.
- **System-of-record plane** (PostgreSQL) for durable entities (incidents, recommendations, users, audit).

---

## 2. Microservices

| Service | Responsibility | Sync API | Consumes (topics) | Produces (topics) | Store |
|---|---|---|---|---|---|
| **API Gateway / BFF** | AuthN/Z, routing, rate-limit, WebSocket fan-out | all `/api/*`, `/ws/*` | ai.recommendations, crowd.readings | — | — |
| **Identity** | Users, roles, tokens (OIDC) | `/auth/*` | — | user.events | Postgres |
| **Venue/Maps** | Venue graph, geo projection, directions proxy | `/venue`, `/directions` | — | — | Postgres |
| **Ingestion** | Normalise sensor/transit/weather feeds | webhooks | — | crowd.readings, transit.updates, weather.updates | — |
| **Crowd** | Maintain live density read-model, alerts | `/crowd/*` | crowd.readings | crowd.alerts | Redis |
| **Prediction** | Short-horizon crowd forecasting (ML) | `/predict` | crowd.readings | crowd.forecasts | model store |
| **Optimization** | Queueing, routing, allocation (OR) | `/optimize/*` | — | — | — |
| **AI Orchestrator** | Multi-agent proactive/reactive reasoning | `/ai/*` | crowd.*, ops.incidents, transit.* | ai.recommendations | Postgres (recs) |
| **LLM Gateway** | Gemini access, prompt mgmt, caching, fallback | internal | — | — | cache |
| **Incident** | Incident lifecycle & dispatch | `/incidents/*` | — | ops.incidents, dispatch.commands | Postgres |
| **Notification** | Push/SMS/in-app fan & staff messaging | `/notify/*` | crowd.alerts, ai.recommendations | notify.sent | — |
| **Analytics** | After-action, KPIs, warehouse ETL | `/analytics/*` | all | — | Warehouse |

**Boundaries** follow the current code packages (`core`, `infra`, `simulation`,
`ml`, `optimization`, `llm`, `agents`, `api`) — each maps to one or more
services when extracted from the MVP monolith. Deployment model: **one logical
tenant per venue**, config-driven by the venue model.

---

## 3. Event-driven architecture

### 3.1 Topics (Kafka)
| Topic | Key | Payload | Producers → Consumers |
|---|---|---|---|
| `crowd.readings` | zone_id | occupancy, capacity, arrival_rate, ts | Ingestion → Crowd, Prediction, AI |
| `crowd.forecasts` | zone_id | predicted ratio, minutes_to_congestion | Prediction → AI, Ops |
| `crowd.alerts` | zone_id | level, message | Crowd → Notification, Fan/Ops |
| `transit.updates` | station | mode, load, delay | Ingestion → AI (Transport agent) |
| `weather.updates` | venue | temp, precip, wind | Ingestion → AI (Sustainability/Emergency) |
| `ops.incidents` | incident_id | type, severity, zone, status | Incident → AI, Security, Medical |
| `ai.recommendations` | rec_id | agent, title, explanation, confidence, severity | AI → Ops, Notification |
| `dispatch.commands` | volunteer_id | task, route, zone | Incident/AI → Volunteer |
| `notify.sent` | user/zone | channel, message | Notification → Analytics |

### 3.2 Patterns
- **Event carried state transfer** for crowd readings (each event self-describes a zone).
- **CQRS**: Crowd service builds a Redis **read-model** (latest snapshot) from the stream;
  writes (incidents, recommendations, decisions) go to Postgres.
- **Idempotency**: recommendations use **deterministic ids** (`hash(agent|title|zone)`) so
  re-analysis upserts rather than duplicates and operator decisions persist.
- **Outbox pattern** for reliable publish from services that also write Postgres.
- **Backpressure**: consumers are horizontally scaled by partition (partition key = zone/venue).

### 3.3 Delivery semantics
At-least-once on the bus; consumers are idempotent. The WebSocket fan-out is
best-effort with a periodic full-snapshot to self-heal missed deltas.

---

## 4. AI agent architecture

```
                         AI Orchestrator
                               │  builds one shared AgentContext per cycle
        ┌───────┬───────┬──────┴────┬───────────┬─────────────┐
     Crowd   Navigation Emergency  Accessibility Transport  Sustainability
        │        │         │            │            │            │
        └────────┴─────────┴─── uses ───┴────────────┴────────────┘
             Prediction (ML) · Optimization (OR) · LLM Gateway (Gemini)
```

- **Contract:** every agent is an `Agent` subclass implementing
  `analyze(context)` (proactive) and optionally `handle_query(context)` (reactive),
  declaring the `intents` it can answer. New capability = new subclass + register
  (Open/Closed principle).
- **Proactive cycle:** orchestrator builds an `AgentContext` (venue + live crowd +
  match minute + incidents + tools), fans it to every agent, then **de-duplicates
  and ranks** recommendations by `severity × confidence`. A failing agent is
  isolated and logged — it can't break the cycle.
- **Reactive routing:** an intent (e.g. `navigate`, `best_exit`, `wheelchair_route`)
  is routed to the first capable agent.
- **Explain-before-recommend:** each agent turns its computed situation into prose
  via the **LLM Gateway** (`explain()`), with a deterministic fallback so an LLM
  outage never blocks a recommendation.
- **Human-in-the-loop:** every recommendation starts `approved = null`; operator
  Approve/Reject is persisted and preserved across cycles.

### 4.1 Agent responsibilities
| Agent | Signals used | Output |
|---|---|---|
| Crowd | occupancy, arrival rate, forecast, queueing wait | redirect fans between gates |
| Navigation | venue graph, live congestion | congestion-aware / step-free routes |
| Emergency | active incidents, LP allocation | volunteer dispatch + fan reroute |
| Accessibility | lift/ramp status, a11y graph | step-free routing, a11y risk flags |
| Transport | transit load, match clock | best egress option, metering |
| Sustainability | occupancy | energy-saving hints for idle zones |

### 4.2 Models & optimisation
- **Forecasting:** gradient-boosted regression (XGBoost/LightGBM) on
  `[current_ratio, arrival_rate, match_minute, trend]`; linear fallback.
- **Queueing:** Erlang-C (M/M/c) wait-time estimates for service points.
- **Routing:** Dijkstra with congestion-weighted edges (+ accessibility filter).
- **Allocation:** integer LP (PuLP) for volunteer assignment; greedy fallback.

---

## 5. Database schema (PostgreSQL, system of record)

```sql
-- Users & auth ---------------------------------------------------------
CREATE TABLE users (
  id            UUID PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  role          TEXT NOT NULL CHECK (role IN
                 ('fan','volunteer','operations','security','medical','admin')),
  locale        TEXT NOT NULL DEFAULT 'en',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Venue model ----------------------------------------------------------
CREATE TABLE venues (
  id            UUID PRIMARY KEY,
  name          TEXT NOT NULL,
  anchor_lat    DOUBLE PRECISION NOT NULL,
  anchor_lng    DOUBLE PRECISION NOT NULL,
  footprint_m   DOUBLE PRECISION NOT NULL DEFAULT 320
);
CREATE TABLE zones (
  id            TEXT PRIMARY KEY,
  venue_id      UUID REFERENCES venues(id),
  name          TEXT NOT NULL,
  type          TEXT NOT NULL,              -- gate|seating|food|washroom|...
  x             REAL NOT NULL, y REAL NOT NULL,
  lat           DOUBLE PRECISION, lng DOUBLE PRECISION,
  capacity      INTEGER NOT NULL,
  service_points INTEGER NOT NULL DEFAULT 0,
  accessible    BOOLEAN NOT NULL DEFAULT true
);
CREATE TABLE zone_edges (              -- undirected graph (store both directions)
  venue_id UUID, a TEXT, b TEXT, PRIMARY KEY (venue_id, a, b)
);

-- Operations -----------------------------------------------------------
CREATE TABLE incidents (
  id          TEXT PRIMARY KEY,
  venue_id    UUID REFERENCES venues(id),
  type        TEXT NOT NULL,          -- medical|security|crowd_crush|fire|lost_person
  severity    TEXT NOT NULL,          -- low|medium|high|critical
  zone_id     TEXT REFERENCES zones(id),
  description TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'open',   -- open|dispatched|resolved
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);
CREATE TABLE recommendations (
  id          TEXT PRIMARY KEY,       -- deterministic: hash(agent|title|zone)
  venue_id    UUID,
  agent       TEXT NOT NULL,
  title       TEXT NOT NULL,
  explanation TEXT NOT NULL,
  confidence  REAL NOT NULL,
  zone_id     TEXT,
  severity    TEXT NOT NULL,
  actions     JSONB NOT NULL DEFAULT '[]',
  metadata    JSONB NOT NULL DEFAULT '{}',
  approved    BOOLEAN,                -- null=pending
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_by  UUID REFERENCES users(id),
  decided_at  TIMESTAMPTZ
);
CREATE TABLE volunteer_tasks (
  id          UUID PRIMARY KEY,
  volunteer_id UUID REFERENCES users(id),
  incident_id TEXT REFERENCES incidents(id),
  zone_id     TEXT REFERENCES zones(id),
  status      TEXT NOT NULL DEFAULT 'assigned',   -- assigned|accepted|enroute|onscene|resolved
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  actor UUID, action TEXT, entity TEXT, entity_id TEXT,
  detail JSONB, at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Time-series crowd (partitioned by day; or a TSDB) --------------------
CREATE TABLE crowd_readings (
  venue_id UUID, zone_id TEXT, occupancy INT, capacity INT,
  arrival_rate REAL, ts TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (ts);
```
Hot state (latest snapshot, per-zone) lives in **Redis** (`crowd:{venue}:latest`)
for sub-second reads; `crowd_readings` is the durable history for analytics.

---

## 6. API contracts (selected)

Base: `/api`. Auth: `Authorization: Bearer <token>`; RBAC per route. Errors use
`{ "detail": "..." }` with standard HTTP codes.

### 6.1 Auth
```
POST /api/auth/login
  req  { "username": "op", "role": "operations" }
  res  { "access_token": "...", "token_type": "bearer", "role": "operations" }
```

### 6.2 Venue & crowd
```
GET  /api/venue           → { anchor:{name,lat,lng,footprint_m}, zones:[{id,name,type,x,y,lat,lng,capacity,neighbours,accessible}] }
GET  /api/crowd/heatmap   → [ { id,name,type,x,y,lat,lng,occupancy,capacity,ratio,level,accessible } ]
POST /api/crowd/tick      → heatmap[]           (advance simulation one minute)
POST /api/crowd/surge?zone_id=&people=  → { status, zone_id, people }   (400 if people<=0)
GET  /api/alerts          → [ { id,message,zone_id,level } ]
```

### 6.3 AI
```
GET  /api/ai/recommendations   → [ { id,agent,title,explanation,confidence,zone_id,severity,actions[],metadata,approved } ]
GET  /api/ai/intents           → { intents: ["navigate","best_exit","wheelchair_route", ...] }
POST /api/ai/query             req { intent, params:{origin,destination,...} } → RecommendationOut
POST /api/ai/recommendations/{id}/decision   [ops|security]  req { approved:bool } → RecommendationOut
```

### 6.4 Incidents
```
POST /api/incidents            [ops|security|medical]  req { type,severity,zone_id,description } → IncidentOut
GET  /api/incidents?include_resolved=  → IncidentOut[]
POST /api/incidents/{id}/resolve   [ops|security|medical] → IncidentOut
```

### 6.5 Match & directions (external-backed)
```
GET  /api/match       → { id,home_team,away_team,competition,venue,kickoff_utc,status,home_score,away_score,minute,source }
GET  /api/directions?origin=<zone>&destination=<zone>
      → { origin,destination,distance_m,duration_min,provider,polyline:[[lat,lng]],steps[] }
```

### 6.6 Realtime
```
WS   /ws/live   → server pushes { match_minute, heatmap[], recommendations[] } per tick
```

Full request/response models are the pydantic schemas in
`backend/stadiummind/api/schemas.py`; the OpenAPI spec is served at `/docs`.

---

## 7. Frontend architecture (Next.js + Tailwind)

- **Framework:** Next.js (App Router) + TypeScript + Tailwind; `output: standalone`.
- **Rendering:** mostly client components for live data; server components for static shell.
- **State/data:** typed API client (`lib/api.ts`) + polling / WebSocket; no global store needed for MVP (local component state + context for locale/auth).
- **i18n:** locale context + string catalog (`lib/i18n.ts`), `dir` toggled for RTL (Arabic).
- **Design tokens → Tailwind:** `tailwind.config.ts` derives colors/radius/fonts from the design-system tokens (§11 of Design System) so brand is centralised.
- **Maps:** `GoogleStadiumMap` loads Maps JS with `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`, renders congestion markers + Directions polylines; falls back to SVG `StadiumMap`.
- **Routing (see IA §4):** `/` (language) → `/launch` (cards) → `/fan`, `/ops`, `/fan/map`, `/fan/ai`.
- **Component library** mirrors the design system: `Card`, `ActionTile`,
  `RecommendationCard`, `BottomSheet`, `StadiumMap`, `GoogleStadiumMap`, `KPIStat`, `TabBar`.
- **Delivery:** Dockerized standalone server; static assets via CDN; edge caching for the shell.

---

## 8. Security & privacy
- **AuthN:** OIDC/OAuth2 (staff SSO); signed bearer tokens; short TTL + refresh.
- **AuthZ:** RBAC per route (fan/volunteer/operations/security/medical/admin).
- **Transport:** TLS 1.3 everywhere; HSTS; secrets in a vault (never in code).
- **Data:** at-rest encryption; **aggregate-only** crowd analytics (no PII, no face ID);
  DPIA per host country; audit log of every operator decision.
- **Abuse/limits:** gateway rate-limiting; per-role quotas; WAF on public edges.

---

## 9. Observability & operations
- **Metrics** (Prometheus): API latency/error rate, bus lag, recommendation
  cycle time, LLM latency/cost, WebSocket connections.
- **Tracing** (OpenTelemetry): request → agent → tool spans.
- **Logging:** structured JSON; **per-agent decision log** for audit/debug.
- **Dashboards/alerts** (Grafana): match-day SLOs; on-call rota + runbooks.
- **Health:** `/api/health` reports LLM backend, predictor backend, match/maps
  providers and venue — for quick match-day readiness checks.

---

## 10. Scaling & resilience
- **Horizontal scale** by venue and by Kafka partition (key = zone/venue).
- **Redis** for sub-second live reads; **Postgres** read replicas for consoles.
- **Stateless services** behind the gateway; autoscale on CPU + bus lag.
- **Graceful degradation** (implemented today): Gemini→mock, Kafka→in-memory,
  Redis→in-memory, SQL→in-memory, Google→SVG/haversine, football-data→fixture.
  A venue never goes dark because one dependency fails.
- **DR:** multi-AZ; nightly Postgres backups; infra as code for one-command venue bring-up.

---

## 11. Mapping to the current repository (MVP → target)
| Target service | Today (in repo) |
|---|---|
| AI Orchestrator + agents | `stadiummind/agents/*` |
| Prediction | `stadiummind/ml/crowd_predictor.py` |
| Optimization | `stadiummind/optimization/*` |
| Crowd/read-model + bus + cache | `stadiummind/infra/*`, `simulation/*` |
| LLM Gateway | `stadiummind/llm/adapter.py` |
| Venue/Maps + Match | `stadiummind/core/venue.py`, `integrations/*` |
| Gateway/BFF | `stadiummind/api/app.py` + `service.py` |
The MVP is a modular monolith with these seams already drawn, so extraction to
independent services is mechanical rather than a rewrite.
