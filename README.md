# Playto Payout Engine

A production-grade MVP of a high-integrity financial payout engine.
Designed using a ledger-first architecture with strict concurrency control.

## Features
- Immutable Double-Entry Ledger System
- Pessimistic Row-level Locking for strict Concurrency (`SELECT ... FOR UPDATE`)
- Background Celery workers with simulated network behavior and explicit retry mechanics
- Explicit State Machines
- End-to-end testing with pytest proving race conditions are handled safely
- Beautiful Glassmorphism React Dashboard

## Prerequisites
- Docker & Docker Compose (Make sure Docker Desktop is running!)
- Python 3.10+
- Node.js 20+

## Setup Instructions

### 1. Start Services
```bash
docker compose up -d
```
*This starts PostgreSQL on port 5432 and Redis on port 6379.*

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv: .\venv\Scripts\Activate.ps1 OR source venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations payouts
python manage.py migrate

# Seed dummy data (if you want to test right away, or run tests)
# Run tests
pytest
```

### 3. Run Servers
**Backend:**
```bash
cd backend
python manage.py runserver
```

**Celery Workers (in a new terminal):**
```bash
cd backend
# Activate venv
celery -A config worker -P solo -l INFO
```
*(Note: `-P solo` is often required for Celery workers to run correctly on Windows).*

**Celery Beat (in a separate new terminal):**
*Required to run the automated sweeper task that checks for stuck payouts every 15 seconds.*
```bash
cd backend
# Activate venv
celery -A config beat -l INFO
```

**Frontend (in a new terminal):**
```bash
cd frontend
npm install
npm run dev
```

## Running the Reconciliation Check
In the backend folder, run:
```bash
python ../reconcile.py
```
This script will cross-check the immutable ledger credits/debits against the snapshot projection.
# payout-engine
