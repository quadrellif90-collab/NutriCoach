# -*- coding: utf-8 -*-
"""Entrypoint for uvicorn - ensures app.py exists for validation scripts."""
import sys
sys.path.insert(0, __file__)

from app import main

app = main.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8400, log_level="info")