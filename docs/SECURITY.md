# StadiumMind AI — Security Review

Scope: backend gateway (FastAPI), AI layer, integrations, and the Next.js
frontend. This document records the threat model, the controls in place, and
the open findings with remediation status.

## 1. Assets & trust boundaries
- **Assets:** operator decisions & audit trail, incident data, live crowd
  state, API keys (Gemini, football-data, Google Maps server key), user roles.
- **Trust boundaries:** browser ↔ gateway (untrusted client), gateway ↔
  external APIs (egress), gateway ↔ datastores, LLM prompt (untrusted text can
  reach it via incident descriptions).

## 2. Controls implemented

| Threat (STRIDE) | Control | Where |
|---|---|---|
| Spoofing | Bearer-token auth, signed (HMAC) tokens, expiry, role check | `api/security.py`, `require_role` |
| Tampering | HMAC signature verification; input validation | `api/security.py`, `api/schemas.py` |
| Repudiation | Operator decisions persisted with decided_by/at (schema) | `05_SYSTEM_DESIGN` schema |
| Information disclosure | Strict CORS allow-list, `Cache-Control: no-store`, no PII in analytics | `api/app.py`, `api/middleware.py` |
| DoS | Per-IP rate limiting (429 + Retry-After); surge upper bound | `api/middleware.py`, `api/service.py` |
| Elevation of privilege | RBAC per route; production config guard | `api/app.py`, `core/config.py` |
| Prompt injection | Untrusted text sanitised + system instruction marks context as data | `llm/adapter.py` |
| Injection (SQL) | Parameterised ORM (SQLAlchemy); no string-built SQL | `infra/sql_repository.py` |
| SSRF | External calls only to fixed, code-defined hosts (not user URLs) | `integrations/*` |
| XSS/CSRF (web) | CSP + `X-Frame-Options` + no cookie auth (bearer only) | `next.config.mjs` |

### Detail
- **CORS:** origins come from `CORS_ALLOWED_ORIGINS` (default `localhost:3000`);
  wildcard is rejected in production. `allow_credentials=False` because auth is
  a bearer header, not a cookie — which also means classic CSRF does not apply.
- **Security headers (API):** `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Content-Security-Policy: default-src 'none'`, `Permissions-Policy`, and HSTS
  in production. (`SecurityHeadersMiddleware`.)
- **Security headers (web):** CSP allowing self + Google Maps, `X-Frame-Options`,
  `nosniff`, HSTS, `poweredByHeader:false`. (`next.config.mjs headers()`.)
- **Rate limiting:** fixed-window per client IP, health-check exempt, 429 with
  `Retry-After`. Single-instance in-process; back with Redis for multi-instance.
- **Input validation:** bounded/pattern-checked username, intent slug, incident
  description length (≤ 500), surge bounds. Unknown zones → 404, not 500.
- **Prompt-injection:** `sanitize_for_prompt()` strips control chars, collapses
  whitespace, truncates, and defuses known injection phrases; the system prompt
  instructs the model to treat all context/questions as untrusted data.
- **Production guard:** `Settings.assert_production_safe()` refuses to start with
  the default JWT secret, wildcard CORS, or disabled rate limiting.
- **Secret management:** no secrets in source code (verified). `NEXT_PUBLIC_*`
  values are, by design, public in the browser bundle.

## 3. Findings

| # | Severity | Finding | Status |
|---|---|---|---|
| S-1 | **High** | A real Google Maps browser key was committed in `frontend/app-nextjs/.env.production`. | **Mitigated + action required.** `.env*` is now gitignored; `.env.production.example` added. **You must rotate the key and restrict it** (HTTP-referrer allow-list + Maps JS/Directions API restriction) in Google Cloud, because it is already exposed in history. |
| S-2 | Medium | Default JWT secret usable in non-prod. | **Fixed.** Production guard blocks start-up with the default secret. |
| S-3 | Medium | No rate limiting / security headers on the gateway. | **Fixed.** Middleware added + tested. |
| S-4 | Low | Incident free-text reaches the LLM. | **Fixed.** Length-bounded + sanitised. |
| S-5 | Info | `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is public by design. | Accepted; must be referrer-restricted (see S-1). |

## 4. Dependency & supply chain
- Python deps are pinned with lower bounds in `requirements.txt`; run
  `pip-audit` in CI to catch CVEs. Node deps via `package-lock.json`; run
  `npm audit --production` in CI.
- Recommended CI gates: `pip-audit`, `npm audit`, secret-scanning (e.g.
  gitleaks), and SAST (e.g. bandit/semgrep).

## 5. Test evidence
Security controls are covered by automated tests:
`tests/system/test_gateway_security.py` (headers, CORS, rate limit, validation,
unsafe-prod refusal), `tests/unit/test_config_security.py` (production guard),
and `tests/unit/test_llm.py` (prompt sanitisation). All pass in the full suite.

## 6. Residual risk & next steps
1. **Rotate & restrict the exposed Maps key (S-1) — do this first.**
2. Move rate-limit state to Redis for multi-instance correctness.
3. Add CI security gates (pip-audit, npm audit, gitleaks, bandit/semgrep).
4. Add OIDC/SSO for staff and short-lived refresh tokens (currently signed
   bearer tokens; adequate for the demo, upgrade for production).
5. Per-host-country DPIA before processing any real crowd data.
