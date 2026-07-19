"""StadiumMind AI backend package.

A GenAI-powered operating system for FIFA World Cup 2026 stadiums. The package
is organised into clean, independently testable layers:

    core          - configuration, domain models, shared exceptions
    infra         - streaming (Kafka), cache (Redis), persistence (SQL)
    simulation    - discrete-time stadium crowd simulator (the live data feed)
    ml            - crowd prediction models (XGBoost / LightGBM + fallback)
    optimization  - queueing theory, LP volunteer allocation, route search
    llm           - pluggable Large-Language-Model adapters (Gemini + mock)
    agents        - the OOP multi-agent orchestrator (the "AI brain")
    api           - FastAPI gateway + WebSocket live feed

Every optional third-party integration degrades gracefully to an in-process
implementation, so the whole system runs and its test-suite passes with no
external services configured.
"""

__version__ = "0.1.0"
