# StadiumMind AI — Implementation Roadmap

Phased delivery across **Frontend, Backend, AI and DevOps**. Each phase ends in
a demoable increment and an explicit exit gate. Durations are indicative
(2-week sprints).

---

## Phase 0 — Foundations (done in this repo)
**Goal:** working, tested MVP monolith with the target seams drawn.

| Track | Delivered |
|---|---|
| Backend | OOP agent orchestrator, simulation, ML, OR, FastAPI + WebSocket, graceful fallbacks |
| AI | 6 agents, explain-before-recommend, human-in-the-loop, idempotent recs |
| Frontend | SVG stadium map, Fan app + Ops dashboard, standalone demo |
| Integrations | football-data.org match data, Google Maps + Directions, MetLife geo |
| Quality | 97 unit + system tests green; SQL/optional paths verified |

**Exit gate:** end-to-end demo story passes; docs (this package) approved. ✅

---

## Phase 1 — Product shell & design system (Sprints 1–2)
**Goal:** FIFA-quality UX foundation.

- **Frontend:** language select (6 langs, RTL) → experience launcher; tokenised
  Tailwind theme from the design system; component library (Card, ActionTile,
  RecommendationCard, BottomSheet, KPIStat, TabBar, Heatmap); i18n catalog.
- **Backend:** locale-aware responses; `/venue/geo` hardening.
- **AI:** explanation prompt templates per locale.
- **DevOps:** Dockerfile (standalone Next.js) + Compose (api, web, postgres, redis).

**Exit gate:** all wireframe screens implemented in hi-fi; a11y audit AA on core flows.

---

## Phase 2 — Real-time platform (Sprints 3–4)
**Goal:** move from simulation to a real event-driven pipeline.

- **Backend:** extract Crowd, Ingestion, Notification services; Kafka topics;
  Redis read-model (CQRS); outbox pattern; Postgres schema + migrations.
- **AI:** subscribe to `crowd.readings`/`forecasts`; publish `ai.recommendations`.
- **Frontend:** WebSocket live feed for Ops heatmap + recommendations.
- **DevOps:** Kafka + schema registry; per-partition autoscaling; load test 90k concurrent.

**Exit gate:** sustained 500 msg/s/venue at p95 < 300 ms; recommendation cycle ≤ 3 s.

---

## Phase 3 — Incident & dispatch (Sprints 5–6)
**Goal:** full security/medical/volunteer loop.

- **Backend:** Incident service, dispatch commands, audit log, RBAC hardening.
- **AI:** Emergency agent → LP dispatch + corridor protection at scale.
- **Frontend:** Security console, Medical view, Volunteer app (status flow).
- **DevOps:** audit retention, SIEM export, DR runbook.

**Exit gate:** detection→on-scene ≤ 4 min in tabletop drill; full audit trail.

---

## Phase 4 — Fan scale & offline (Sprints 7–8)
**Goal:** 90k fans per venue, resilient on congested networks.

- **Frontend:** offline-first caching, push notifications, SMS fallback for critical alerts.
- **Backend:** edge/CDN for shell; BFF caching; rate limits.
- **AI:** async LLM explanations + caching to control latency/cost.
- **DevOps:** multi-AZ, CDN, chaos testing of every fallback path.

**Exit gate:** app interactive < 2.5 s on 4G at peak; all fallbacks chaos-tested.

---

## Phase 5 — Multi-venue & analytics (Sprints 9–10)
**Goal:** operate multiple host venues; prove ROI.

- **Backend:** config-driven venue onboarding; per-tenant isolation; Analytics service + warehouse ETL.
- **AI:** guidance-accuracy tracking; per-venue model tuning.
- **Frontend:** after-action report, KPI dashboards, admin console.
- **DevOps:** one-command venue bring-up (IaC); cost dashboards.

**Exit gate:** 2+ venues live from one control plane; KPI targets met in pilot.

---

## Phase 6 — Advanced (post-tournament backlog)
Digital twin & IoT sensor fusion · BLE/UWB indoor positioning · drone/robotics
dispatch · RL crowd control · predictive maintenance · retail personalization ·
cross-venue "tournament control tower".

---

## Cross-cutting workstreams

| Workstream | Ongoing responsibilities |
|---|---|
| **Security & privacy** | DPIA per country, pen-tests each phase, secret rotation |
| **Accessibility** | WCAG AA gate on every UI PR; assistive-tech testing each phase |
| **Localization** | Continuous string QA for 6 languages incl. RTL |
| **Reliability** | SLOs, error budgets, match-day on-call, game-day readiness reviews |
| **Data governance** | Aggregate-only analytics, retention policy, access reviews |

---

## Indicative team (per phase)
- 2–3 Frontend, 3–4 Backend, 1–2 ML/AI, 1–2 DevOps/SRE, 1 Design, 1 PM, 0.5 Security.

## Top delivery risks (see PRD §10 for full register)
1. Network saturation at peak → offline-first + CDN + SMS (Phase 4 priority).
2. Data-feed reliability → fallbacks already built; add feed SLAs (Phase 2).
3. Multi-venue complexity → config-driven tenancy + IaC (Phase 5).
4. AI trust/safety → human approval + audit are non-negotiable throughout.

---

## Definition of "match-ready" (v1 launch)
All Phase 1–4 exit gates met + PRD §11 release criteria satisfied: load,
security/DPIA, accessibility, runbooks, and 6-language content QA signed off.
