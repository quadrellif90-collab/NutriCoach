# -*- coding: utf-8 -*-
"""NutriCoach v2 (Dietowin-style) — avvio rapido."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from app.main import app

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("NUTRICOACH_PORT", "8400"))
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
