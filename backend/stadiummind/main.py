"""Entrypoint: ``python -m stadiummind.main`` or ``uvicorn`` target.

Usage
-----
    uvicorn stadiummind.main:app --reload

or run directly, which starts uvicorn programmatically:

    python -m stadiummind.main
"""

from __future__ import annotations

import logging

from stadiummind.api.app import create_app

logging.basicConfig(level=logging.INFO)

# Module-level ASGI app for uvicorn / gunicorn.
app = create_app()


def main() -> None:  # pragma: no cover - manual launch helper
    import uvicorn

    uvicorn.run("stadiummind.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":  # pragma: no cover
    main()
