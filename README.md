# Lego Inventory Service (modular scaffold)

Minimal, modular FastAPI service to manage LEGO sets and part inventory.
Designed for Raspberry Pi 5. SQLite backend. Clean architecture.

Run:
1. Create and activate venv:
   python3 -m venv venv
   source venv/bin/activate
2. Install:
   pip install -r requirements.txt
3. Initialize DB (first run will auto-create sqlite file).
4. Start:
   uvicorn app.main:app --host 0.0.0.0 --port 8081

Files:
- app/main.py         : app factory and startup events
- app/api/*           : FastAPI routers
- app/core/*          : domain models and services
- app/infrastructure/*: DB and external API adapters
- requirements.txt
