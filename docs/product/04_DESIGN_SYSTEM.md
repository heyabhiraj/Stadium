# StadiumMind AI — High-Fidelity Design System

A FIFA-quality, accessible, multilingual design system. All values are provided
as **design tokens** so they map 1:1 to Tailwind config and CSS variables.

---

## 1. Brand & tone
Confident, calm, trustworthy. The UI should feel like a **premium control
surface** — spacious, high-contrast, motion used sparingly to draw the eye to
what changed. Never flashy during an incident.

---

## 2. Color

### 2.1 Core palette (tokens)
| Token | Hex | Use |
|---|---|---|
| `--navy` | `#0B1F3A` | Primary brand, headers, dark surfaces |
| `--navy-2` | `#12294C` | Gradient partner |
| `--brand` (blue) | `#2563EB` | Primary actions, links, accents |
| `--brand-soft` | `#DBEAFE` | Selected/ghost backgrounds |
| `--surface` | `#FFFFFF` | Cards |
| `--canvas` | `#F4F6FB` | App background |
| `--text` | `#0F172A` | Primary text |
| `--muted` | `#64748B` | Secondary text |
| `--line` | `#E2E8F0` | Borders/dividers |

### 2.2 Status / congestion scale (semantic)
| Token | Hex | Meaning |
|---|---|---|
| `--success` (green) | `#16A34A` | Normal / go / approved |
| `--warning` (amber) | `#F59E0B` | Moderate |
| `--busy` (orange) | `#EA580C` | Busy |
| `--danger` (red) | `#DC2626` | Congested / critical / reject |

Congestion heat = green → amber → orange → red (occupancy 0→100%). These four
are the *only* colors used for the heatmap so the mapping is unambiguous.

### 2.3 Contrast rules
All text ≥ 4.5:1 on its background (WCAG AA). Status colors are paired with an
icon or label — never color alone — for color-blind accessibility.

---

## 3. Typography
- **Family:** Inter (fallback: system-ui). Numerals use tabular figures for KPIs.
- **Scale (px / line-height):**

| Token | Size/LH | Weight | Use |
|---|---|---|---|
| `display` | 32 / 38 | 800 | Match title, big KPI |
| `h1` | 24 / 30 | 700 | Screen title |
| `h2` | 20 / 26 | 700 | Section |
| `h3` | 16 / 22 | 600 | Card title |
| `body` | 15 / 22 | 400 | Paragraph |
| `label` | 13 / 18 | 600 | Tiles, chips |
| `caption` | 11 / 14 | 600 uppercase | Eyebrow/agent tag |

RTL: same scale; text-align flips; the layout mirrors (see §9).

---

## 4. Spacing, grid & radius
- **8px base grid.** Spacing tokens: 4, 8, 12, 16, 24, 32, 48.
- **Radius:** `--radius: 12px` (cards, tiles, buttons); pills use 999px.
- **Container:** max-width 1180px (web); fan app frame 380–420px.
- **Layout:** Ops cockpit is a `380px | 1fr` split with a KPI strip on top.

---

## 5. Elevation & surfaces
| Level | Shadow | Use |
|---|---|---|
| 0 | none, 1px `--line` border | Cards (default, flat + border) |
| 1 | `0 1px 2px rgba(15,23,42,.06)` | Hover |
| 2 | `0 8px 24px rgba(15,23,42,.12)` | Bottom sheets, popovers |
Surfaces prefer **borders over heavy shadows** for a crisp, data-dense feel.

---

## 6. Iconography
- **Library:** Lucide (consistent 2px stroke). **All icons are SVG — never emoji.**
- Sizes: 16 (inline), 22 (tiles/nav), 28 (feature).
- Domain glyphs: navigate, utensils, train, accessibility, alert-triangle,
  map-pin, radio, heart-pulse, leaf (sustainability).

---

## 7. Components (library)

| Component | Anatomy | States |
|---|---|---|
| **Button** | label (+icon); filled / secondary / danger / ghost | default, hover, active, disabled, loading |
| **ActionTile** | icon + label; 1/3 width | default, hover, pressed, focus |
| **Card** | title (caption) + content; 1px border, 12px radius | — |
| **RecommendationCard** | agent tag + severity badge + title + explanation + confidence bar + Approve/Reject | pending, approved, rejected |
| **BottomSheet** | handle + title + meta + primary CTA | peek, expanded |
| **Heatmap** | SVG/Google map, zone markers colored by level, pulse on congested | live |
| **KPIStat** | big number + label on navy tile | — |
| **TabBar** | 5 items, icon + label, active = brand | active/inactive |
| **AlertRow** | level dot + message + optional CTA | info/moderate/busy/congested |
| **Chip / Suggestion** | ghost pill, tappable | default, selected |
| **LanguageTile** | flag glyph + language name | default, selected (brand border) |
| **Badge (severity)** | low/medium/high/critical color-coded | — |

### 7.1 Confidence bar
A 6px track (`--line`) filled `--brand` to `confidence%`. Always paired with a
numeric "Confidence NN%" label.

### 7.2 Severity badge tokens
`low` = green-tint, `medium` = amber-tint, `high` = orange-tint,
`critical` = red-tint. Text uses the darker shade of the same hue.

---

## 8. Motion
- **Durations:** 120ms (micro), 200ms (standard), 320ms (sheet).
- **Easing:** `cubic-bezier(0.2, 0, 0, 1)` (decelerate).
- **Purposeful only:** congested zones pulse (1.4s loop) to draw attention;
  recommendation cards fade+rise on entry. No decorative animation during
  incidents (reduced-motion respected via `prefers-reduced-motion`).

---

## 9. Internationalization & RTL
- 6 launch languages: English, Español, Français, Português, العربية (RTL), Deutsch.
- All copy externalised to a string catalog keyed by locale.
- **RTL (Arabic):** set `dir="rtl"`; layout mirrors (nav, tiles, sheet CTAs,
  progress fills); icons that imply direction (arrows) are flipped; numerals per
  locale. Line-length and truncation tested for German (long compounds).

---

## 10. Accessibility
- WCAG 2.1 AA. Contrast ≥ 4.5:1; status never color-only.
- Targets ≥ 44×44px; focus rings visible (2px brand outline).
- Full keyboard nav on web consoles; ARIA roles on interactive SVG map markers.
- Screen-reader labels on every icon-only control; live regions announce new alerts.
- **Accessibility mode** increases target size, enables step-free routing and
  higher-contrast surfaces globally.

---

## 11. Design tokens (machine-readable)
```json
{
  "color": {
    "navy": "#0B1F3A", "brand": "#2563EB", "brandSoft": "#DBEAFE",
    "success": "#16A34A", "warning": "#F59E0B", "busy": "#EA580C", "danger": "#DC2626",
    "surface": "#FFFFFF", "canvas": "#F4F6FB", "text": "#0F172A",
    "muted": "#64748B", "line": "#E2E8F0"
  },
  "radius": { "md": 12, "pill": 999 },
  "space": [4, 8, 12, 16, 24, 32, 48],
  "font": { "family": "Inter", "scale": {
    "display": 32, "h1": 24, "h2": 20, "h3": 16, "body": 15, "label": 13, "caption": 11 } },
  "motion": { "micro": 120, "standard": 200, "sheet": 320,
    "easing": "cubic-bezier(0.2,0,0,1)" }
}
```
These tokens are the single source of truth. `tailwind.config.ts` and the
standalone HTML shell both derive their theme from them, guaranteeing the fan
app, ops dashboard and demo look identical.

---

## 12. Do / Don't
- **Do** lead with the recommended action and its reason.
- **Do** keep one primary CTA per surface.
- **Don't** use more than the four congestion colors on the map.
- **Don't** animate during an active incident beyond the single attention pulse.
- **Don't** use emoji or icon fonts — SVG only.
