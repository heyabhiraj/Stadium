# StadiumMind AI — Low-Fidelity Wireframes

Box wireframes for every screen with annotations. Notation: `[ ]` control/tile,
`( )` action button, `====` divider, `▓` map/heat area, `»` navigation.

---

## FAN APP

### F1 · Language Select (Welcome shell)
```
+--------------------------------+
|            StadiumMind         |   Logo (SVG), centered
|         Choose your language   |
|                                |
|  [ English ]   [ Español ]     |   6 tiles, 2 cols
|  [ Français ]  [ Português ]   |
|  [ العربية ]   [ Deutsch ]     |   Arabic tile flips layout to RTL
|                                |
|         ( Continue » )         |
+--------------------------------+
```
Notes: large tap targets; selected tile highlighted; remembers choice.

### F2 · Experience Launcher
```
+--------------------------------+
|  StadiumMind AI                |
|  Choose an experience          |
|  +--------+ +--------+          |
|  |  FAN   | |  OPS   |          |   3–4 cards; icon + title + 1-line desc
|  +--------+ +--------+          |
|  +--------+ +--------+          |
|  |  MAP   | | AI CHAT|          |
|  +--------+ +--------+          |
+--------------------------------+
```

### F3 · Home
```
+--------------------------------+
| ☼ Good evening, welcome        |   greeting (SVG sun icon)
| Brazil vs Spain                |   match card (real data)
| FIFA WC 2026 · MetLife · 7:30  |
| =============================  |
| [Navigate][ Food ][Transport]  |   6 action tiles (SVG icons)
| [Washroom][ A11y ][Emergency]  |
| =============================  |
| Live alerts                    |
|  • Gate 3 busy                 |
|  • Food Court A crowded        |
+--------------------------------+
| Home  Map  AI  Alerts  Profile |   bottom nav (5)
+--------------------------------+
```

### F4 · Map
```
+--------------------------------+
| [search............] [filter]  |
|                                |
|     ▓▓▓  Stadium + heat  ▓▓▓    |   Google satellite / SVG fallback
|     ▓ green/amber/red pins ▓    |   pins colored by congestion
|                                |
+--------------------------------+
| Food Court A                   |   bottom sheet on tap
| Queue 6 min · 120 m · ★4.8     |
| ( Navigate )                   |
+--------------------------------+
```

### F5 · Route view
```
+--------------------------------+
| Walking · 2 min      ( x )     |
|                                |
|     ▓ route polyline ▓         |
|     ● you → ● destination      |
|                                |
| Crowd density: ▁▂▅▂▁           |
| [ Avoid crowd  ● ON ]          |
| ( Start )   ( Alt route )      |
+--------------------------------+
```

### F6 · AI assistant
```
+--------------------------------+
| How can I help?                |
| ( 🎤 Voice )  ( ⌨ Type )       |
| ------------------------------ |
| Suggestions:                   |
|  [Where is my seat?]           |
|  [Least crowded gate]          |
|  [Food near me]                |
|  [Wheelchair route]            |
| ------------------------------ |
| » answer card (title + why +   |
|   Navigate action)             |
+--------------------------------+
```

### F7 · Alerts
```
+--------------------------------+
| Alerts                         |
| ● red   Gate 3 congested       |
| ● amber Food Court A busy       |
| ● info  Metro minor delay      |
|   ( Navigate to safe zone )     |
+--------------------------------+
```

### F8 · Profile
```
+--------------------------------+
| Alex Fan                       |
| Seat: North Stand N12 · Row 8  |
| Language: [English ▾]          |
| Accessibility mode [ ○ off ]   |
| Notifications [ ● on ]         |
+--------------------------------+
```

### F9 · Emergency sheet
```
+--------------------------------+
| Emergency                      |
| ( Call venue safety )          |
| ( Report incident )            |
| ( Nearest safe exit » )        |
+--------------------------------+
```

---

## OPERATIONS DASHBOARD

### O1 · Cockpit
```
+-------------------------------------------------------------+
| 42'  | Attendance 68,240 | Congested 2 | Open incidents 1   |  KPI strip
+---------------------------+---------------------------------+
|                           |  AI RECOMMENDATIONS             |
|     ▓ STADIUM HEATMAP ▓    |  [crowd · HIGH · 92%]           |
|     ▓ zones colored   ▓    |  Redirect Gate 3 → Gate 5       |
|     ▓ pulsing red hot ▓    |  "Two buses arrived; G5 is 30%" |
|                           |  ( Approve ) ( Reject )         |
|                           |  [emergency · CRIT · 90%] ...   |
+---------------------------+---------------------------------+
| Incidents | Volunteers | Transport            (tabs)        |
| 19:12 CRIT medical @ Medical 1 — 3 volunteers dispatched    |
+-------------------------------------------------------------+
```
Annotations: no side menu; approve/reject is the primary loop; recommendations
ranked by severity × confidence; clicking a zone filters the right rail.

### O2 · Analytics / after-action
```
+-------------------------------------------------------------+
| Match summary  · queue time ↓ · incidents · decisions log   |
| ▓ charts: attendance curve, congestion timeline ▓           |
| Recommendations: 24 issued · 18 approved · 6 rejected       |
+-------------------------------------------------------------+
```

---

## SECURITY CONSOLE

### S1 · Security cockpit
```
+-------------------------------------------------------------+
| ▓ map + risk flags ▓        | INTAKE                        |
|                             | Type [▾] Severity [▾] Zone[▾] |
|                             | ( Create incident )           |
|                             | TRIAGE / DISPATCH             |
|                             |  Fastest route ✓  Corridor ✓  |
| AUDIT LOG (timestamped)                                      |
+-------------------------------------------------------------+
```

---

## MEDICAL VIEW

### M1 · Medical
```
+-------------------------------------------------------------+
| Standby staging: West Concourse (suggested)                 |
| ALERT: CRIT medical @ Medical 1                             |
| ( Accept )  » fastest step-free route  ▓ map ▓              |
| On-scene ( ✓ )   Handoff ( ✓ )                              |
+-------------------------------------------------------------+
```

---

## VOLUNTEER APP

### V1 · Assignment
```
+--------------------------------+
| Your assignment                |
| Assist medical corridor        |
| » Medical 1 · 120 m · 2 min    |
| ( Accept )                     |
| Status: ○en-route ○on-scene    |
|         ○resolved              |
| ------------------------------ |
| Messages from Ops              |
+--------------------------------+
```

---

## ADMIN

### A1 · Admin
```
+-------------------------------------------------------------+
| Venue config | Zones & geo | Users & roles | Feeds | Flags  |
| ▓ editable venue graph, anchor lat/lng, feed status ▓       |
+-------------------------------------------------------------+
```

---

## Wireframe → hi-fi mapping
Each low-fi screen maps to a hi-fi component set defined in
`04_DESIGN_SYSTEM.md` (Card, ActionTile, BottomSheet, RecommendationCard,
Heatmap, KPIStat, TabBar, AlertRow). The standalone HTML shell and the Next.js
app implement F1–F9 and O1 directly.
