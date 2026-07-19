# StadiumMind AI — User Journey Maps

Every persona is mapped across stages, with actions, emotional state, pain
points and the **AI touchpoint** that StadiumMind introduces at each step.
Legend for AI touchpoints: 🟢 proactive (AI acts first) · 🔵 reactive (AI answers) ·
🟠 human-approved action.

---

## Persona 1 — Fan (Alex)

**Profile.** 28, travelled from São Paulo, first time at the venue, speaks
Portuguese, has a general-admission ticket and a phone on roaming data.

**Goal.** Get in, find the seat, enjoy the match, avoid queues, get home.

| Stage | Action | Emotion | Pain (today) | StadiumMind AI touchpoint |
|---|---|---|---|---|
| Leave home/hotel | Checks kickoff, plans transport | Excited | Unclear best route/time | 🔵 App shows kickoff + recommended departure & transit |
| Approach venue | Arrives by metro | Anxious | Which gate? | 🟢 App routes to least-crowded gate for the seat |
| Security/entry | Queues at turnstile | Impatient | Long unclear queues | 🟢 Live gate wait times; redirect suggestion if congested |
| Concourse | Finds the seat | Lost | Poor signage | 🔵 Turn-by-turn indoor wayfinding, congestion-aware |
| In-seat | Wants food/washroom | Comfortable | Long queues, misses play | 🔵 "Least-crowded washroom / shortest food queue near me" |
| Incident nearby | Sees crowding | Concerned | No guidance | 🟢 Push alert + safe detour |
| Full time | Wants to leave | Tired | Egress crush, transport chaos | 🟢 Best exit + live transport recommendation |
| Journey home | Boards transit | Relieved | Overcrowded platforms | 🟠 Ops meters egress; app staggers guidance |

**Moments that matter:** first gate choice, the "where's my seat" moment, and
post-match egress. These are where StadiumMind must feel magical.

---

## Persona 2 — Volunteer (Maria)

**Profile.** 45, local, multilingual, assigned to the west concourse, carries a
phone with the volunteer app.

**Goal.** Help visitors and respond where she's needed, without guessing.

| Stage | Action | Emotion | Pain (today) | AI touchpoint |
|---|---|---|---|---|
| Shift start | Checks in | Ready | Unclear priorities | 🔵 App shows zone status + likely hotspots |
| Idle | Waits for radio calls | Uncertain | Reactive, radio noise | 🟢 AI suggests proactive positioning near predicted congestion |
| Dispatch | Receives assignment | Focused | Verbal, error-prone | 🟠 Ops-approved dispatch with turn-by-turn route |
| On scene | Assists / directs | Purposeful | No situational context | 🔵 Context card: what's happening, what to do |
| Resolve | Marks complete | Satisfied | Manual logging | 🔵 One-tap status; auto-logged with timestamp |

---

## Persona 3 — Operations Manager (Diego)

**Profile.** 52, runs the operations centre, 20 years of experience, responsible
for the whole venue's flow and safety.

**Goal.** Keep the venue running smoothly without being buried in data.

| Stage | Action | Emotion | Pain (today) | AI touchpoint |
|---|---|---|---|---|
| Pre-match | Reviews readiness | Calm | Manual checks | 🔵 Readiness snapshot; predicted arrival curve |
| Doors open | Monitors gates | Alert | CCTV wall overload | 🟢 Heatmap + ranked recommendations, not raw alarms |
| Build-up | Congestion forms at a gate | Stressed | Notices late | 🟢 Prediction: "Gate 3 congested in ~6 min" |
| Decision | Chooses response | Pressured | No decision support | 🟠 "Redirect to Gate 5 (saves 12 min), 92% conf" → Approve |
| Incident | Coordinates response | High-stress | Fragmented comms | 🟠 One-tap dispatch + fan reroute; single timeline |
| Full time | Manages egress | Focused | Transport mismatch | 🟠 Egress metering aligned to live transit capacity |
| Post-match | Debrief | Reflective | No structured record | 🔵 Auto after-action report from the decision log |

**Design implication:** Diego must feel he has a *copilot*, not another
dashboard. Confidence + explanation + one-tap approve is the core loop.

---

## Persona 4 — Security Officer (Sam)

**Goal.** Detect incidents fast and coordinate a safe, quick response.

| Stage | Action | Emotion | Pain (today) | AI touchpoint |
|---|---|---|---|---|
| Patrol | Monitors zones | Vigilant | Blind spots | 🟢 Anomaly/crowd-crush risk flag with location |
| Detect | Confirms incident | Urgent | Slow triage | 🔵 Guided triage: type, severity, zone |
| Coordinate | Directs responders | Tense | Radio-only | 🟠 Fastest clear route; auto fan reroute to protect corridor |
| Contain | Manages scene | Focused | No live picture | 🔵 Live density around scene; escalation suggestions |
| Close | Stands down | Relieved | Manual report | 🔵 Timestamped audit trail auto-generated |

---

## Persona 5 — Medical Team (Dr. Okafor)

**Goal.** Reach the patient by the fastest clear route and hand off cleanly.

| Stage | Action | Emotion | Pain | AI touchpoint |
|---|---|---|---|---|
| Standby | Awaits calls | Ready | Static positioning | 🔵 Suggested staging near predicted demand |
| Alert | Receives medical incident | Focused | Location ambiguity | 🟠 Exact zone + fastest step-free route |
| En route | Moves through crowd | Rushed | Crowds block path | 🟢 Corridor protection: fans rerouted ahead |
| Treat | Stabilises patient | Intense | No context | 🔵 Nearest medical point / evac route |
| Handoff | Transfers care | Careful | Manual logging | 🔵 Auto-logged incident record |

---

## Persona 6 — Accessibility user (Priya, wheelchair user)

**Goal.** A dignified, fully step-free experience equal to everyone else's.

| Stage | Action | Emotion | Pain (today) | AI touchpoint |
|---|---|---|---|---|
| Arrival | Finds accessible entry | Hopeful | Unclear a11y routes | 🔵 Accessible gate + step-free route pre-selected |
| Navigate | Uses lifts/ramps | Cautious | Lifts crowded/broken | 🟢 Live lift status; reroute if a lift is down/busy |
| Amenities | Reaches accessible WC/food | Independent | Poor info | 🔵 Nearest accessible amenity with live status |
| Emergency | Needs safe evac | Fearful | Generic evac ignores a11y | 🟠 Dedicated step-free evacuation route + volunteer dispatch |
| Egress | Leaves safely | Confident | Crowded step-free exits | 🟢 Accessible egress timed to avoid crush |

**Non-negotiable:** accessibility is a *mode across every flow*, not a separate
lesser app.

---

## Persona 7 — Transport authority (Metro control)

**Goal.** Match egress flow to transport capacity to avoid platform crush.

| Stage | Action | Emotion | Pain | AI touchpoint |
|---|---|---|---|---|
| Pre-egress | Forecasts demand | Planning | Guesswork | 🔵 Predicted egress curve by exit/mode |
| Full time | Sees surge | Reactive | Platform overcrowding | 🟢 Recommended metering: hold/release by gate |
| Coordinate | Aligns with Ops | Collaborative | Siloed comms | 🟠 Shared plan; Ops approves staggered release |

---

## Cross-persona "golden thread" (the demo narrative)

1. Fan is routed to the least-crowded gate (🟢).
2. Crowd agent predicts Gate 3 congestion; Ops gets an explained redirect (🟠).
3. Volunteers repositioned proactively (🟢).
4. Medical incident → responder dispatched, corridor protected, fans rerouted (🟠).
5. Post-match: best exit + transport recommended; egress metered with transit (🟠).

Every persona experiences the *same event* from their own role — one shared
truth, many tailored views.
