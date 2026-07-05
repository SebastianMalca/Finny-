# api/index.py
# Vercel Serverless Function entry point for the FINNY Flask backend.
# Vercel detecta automáticamente este archivo como la función serverless.

import sys
import os

# Agregar el root del proyecto al path para que las importaciones funcionen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app  # noqa: F401 — Vercel espera que 'app' esté en el módulo
