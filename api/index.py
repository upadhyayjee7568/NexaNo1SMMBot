"""Vercel serverless entry point.

Vercel's @vercel/python runtime detects the ASGI ``app`` object exported here and
serves the entire FastAPI application (web panels + API + Telegram webhook).
"""

import os
import sys

# Ensure the project root is importable when running inside the Vercel function.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

# Vercel looks for a module-level `app` (ASGI) or `handler`.
handler = app
