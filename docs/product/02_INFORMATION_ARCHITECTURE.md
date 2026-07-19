# StadiumMind AI — Information Architecture (IA)

Defines every screen, how screens connect, entry points, deep links and URL
maps across all five surfaces: **Fan app, Operations, Security, Medical,
Volunteer**, plus the shared **Welcome/Language** shell and **Admin**.

---

## 1. Product surfaces & top-level map

```
StadiumMind AI
│
├── Welcome shell (shared entry)
│     ├── Language select
│     └── Role / experience launcher  (Fan · Ops · Map · AI Chat)
│
├── Fan app (mobile)              [role: fan]
├── Operations dashboard (web)    [role: operations]
├── Security console (web)        [role: security]
├── Medical view (web/tablet)     [role: medical]
├── Volunteer app (mobile)        [role: volunteer]
└── Admin (web)                   [role: admin]
```

---

## 2. Navigation model

- **Fan app:** 5-tab bottom navigation, max **2 taps** to any feature, bottom
  sheets instead of modals, a floating voice button on every screen.
- **Ops/Security/Medical:** single-screen "cockpit" (no deep menu trees) —
  map + recommendations + timeline visible together; panels, not page hops.
- **Volunteer:** task-centric single stack (current assignment → detail → status).

### Fan bottom navigation (only 5)
```
Home | Map | AI | Alerts | Profile
```

---

## 3. Screen inventory & navigation graph

### 3.1 Welcome shell (shared)
```
[Splash] → [Language Select] → [Experience Launcher]
                                     ├── Fan app
                                     ├── Ops dashboard
                                     ├── Map explorer
                                     └── AI chat
```
| Screen | Purpose | Reaches |
|---|---|---|
| Splash | Brand + load | Language Select |
| Language Select | Choose 1 of 6 languages (RTL aware) | Experience Launcher |
| Experience Launcher | 4 cards to enter a surface | Fan / Ops / Map / AI |

### 3.2 Fan app
```
Home ──┬── Navigate → Route view → Arrived
       ├── Food → Venue map (food filter) → Bottom sheet → Route view
       ├── Transport → Transport view → Route view
       ├── Washroom → Map (WC filter) → Bottom sheet → Route
       ├── Accessibility → A11y route view
       └── Emergency → Emergency sheet (call / report / safe exit)

Map ──── Zone tap → Bottom sheet (queue, distance, rating, Navigate)
AI ───── Suggestions / Voice / Type → Answer card → (Navigate | More)
Alerts ─ Alert list → Alert detail → (Navigate to safe zone)
Profile ─ Seat info · Language · Accessibility mode · Notifications
```
| Screen | Key elements | Deep link |
|---|---|---|
| Home | Match card, 6 action tiles, live alerts | `/fan` |
| Map | Google/SVG map, heat overlay, search, bottom sheet | `/fan/map` |
| Route view | Path, ETA, crowd density, "Avoid crowd" toggle | `/fan/route?to=` |
| AI | Suggestions, voice, chat, action cards | `/fan/ai` |
| Alerts | Location-scoped alerts | `/fan/alerts` |
| Profile | Seat, language, a11y, notifications | `/fan/profile` |
| Emergency | Call, report incident, nearest safe exit | `/fan/emergency` |

### 3.3 Operations dashboard (single cockpit)
```
[Top KPI strip] attendance · congested zones · open incidents · match clock
[Left/Main] Stadium heatmap (zone select → detail)
[Right] AI recommendations (ranked) → Approve / Reject
[Bottom] Incident timeline  |  Volunteers  |  Transport metering (tabs)
```
| Panel | Purpose | Route |
|---|---|---|
| Heatmap | Live congestion by zone | `/ops` |
| Recommendations | Ranked, explained, approve/reject | `/ops` (right rail) |
| Incident timeline | Chronological incidents & status | `/ops#incidents` |
| Volunteers | Allocation & dispatch | `/ops#volunteers` |
| Transport | Egress metering vs transit load | `/ops#transport` |
| Analytics | Post-match after-action report | `/ops/analytics` |

### 3.4 Security console
```
[Map w/ risk flags] → [Incident intake] → [Triage] → [Dispatch + corridor protect] → [Audit log]
```
Routes: `/security`, `/security/incident/:id`.

### 3.5 Medical view
```
[Standby staging] → [Incident alert] → [Fastest step-free route] → [On-scene] → [Handoff/log]
```
Route: `/medical`, `/medical/incident/:id`.

### 3.6 Volunteer app
```
[My assignment] → [Route] → [Status: accept/en-route/on-scene/resolved] → [Messages]
```
Routes: `/volunteer`, `/volunteer/task/:id`.

### 3.7 Admin
```
[Venue config] · [Zones & geo] · [Users & roles] · [Feeds/integrations] · [Feature flags] · [Audit]
```
Route: `/admin/*`.

---

## 4. URL / route map (canonical)

| Surface | Route | Notes |
|---|---|---|
| Welcome | `/` | Language select |
| Launcher | `/launch` | 4 experience cards |
| Fan | `/fan`, `/fan/map`, `/fan/ai`, `/fan/alerts`, `/fan/profile` | Mobile-first |
| Ops | `/ops`, `/ops/analytics` | Cockpit |
| Security | `/security`, `/security/incident/:id` | RBAC |
| Medical | `/medical`, `/medical/incident/:id` | RBAC |
| Volunteer | `/volunteer`, `/volunteer/task/:id` | Mobile |
| Admin | `/admin/*` | RBAC (admin) |
| API | `/api/*` | Proxied to gateway |

---

## 5. Entry points & deep links
- **QR on ticket** → `/fan?seat=N12-R8` (pre-selects seat context).
- **Push notification** → `/fan/alerts` or `/fan/route?to=<safe_zone>`.
- **Staff SSO** → role-appropriate cockpit (`/ops`, `/security`, `/medical`, `/volunteer`).
- **NFC/beacon at gate** (future) → `/fan/map?near=<zone>`.

---

## 6. State & context that persists across screens
- Selected **language** (and text direction) — global.
- **Seat / ticket context** for the fan — global within Fan app.
- **Accessibility mode** — global; alters routing and layout everywhere.
- **Auth role** — determines available surfaces and API scopes.
- **Live crowd snapshot** — shared read-model powering map, alerts and AI.

---

## 7. IA principles applied
- **Shallow, not deep:** operators never navigate more than one level from the cockpit.
- **One truth, many views:** the same crowd/incident model renders per role.
- **Progressive disclosure:** bottom sheets reveal detail on demand, not upfront.
- **Consistent placement:** primary action always bottom-right / bottom-sheet CTA.
