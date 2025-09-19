Placement Prep AI - Backend
===========================

FastAPI backend for code execution, submissions tracking, questions, study plans, and memory.

Quickstart
----------

1) Clone and enter backend folder:

```bash
cd backend
```

2) Create and activate venv (optional if already present):

```bash
python3 -m venv venv
source venv/bin/activate
```

3) Install dependencies:

```bash
pip install -r requirements.txt
```

4) Set environment variables (copy and edit as needed):

```bash
export DATABASE_URL="sqlite:///./app/data/app.db"
# Optional: to enable online study plan generation via OpenRouter
export OPENROUTER_API_KEY="your_key_here"
export OR_MODEL="openrouter/auto"  # optional
```

5) Run the server:

```bash
uvicorn app.main:app --reload
```

API at http://127.0.0.1:8000

Data & Database
---------------
- SQLite file at `app/data/app.db` (created automatically).
- SQLAlchemy models in `app/db/models.py`.
- Tables are created at startup via FastAPI lifespan.

Routers & Endpoints
-------------------

Users (`/users`)
----------------
- GET `/users/` — list users
- POST `/users/` — create user (JSON: `{email, name}`)
- GET `/users/{user_id}` — get single user
- GET `/users/{user_id}/submissions/` — list a user’s submissions
- GET `/users/{user_id}/weak-topics` — computed weak topics (from analytics service)

Submissions (`/submissions`)
----------------------------
- POST `/submissions/submit` — run code against testcases and persist results
  - JSON: `{user_id?, question, source_code, language_id, run_hidden?}`
- POST `/submissions/` — simple submission record without running tests
  - JSON: `{user_id?, question_id?, topic?, score, passed, total}`
- GET `/submissions/user/{user_id}` — list submissions by user

Questions (`/questions`)
------------------------
- Provided in `app/routers/questions.py` (inspect for available endpoints)

Executor (`/executor`)
----------------------
- Provided in `app/routers/executor.py` (inspect for available endpoints)

Study Plans (`/plans` and alias `/study-plans`)
----------------------------------------------
- POST `/plans/generate` — generate and save plan
- GET `/plans/user/{user_id}` — list user plans
- PUT `/plans/{plan_id}` — update plan title/raw JSON
- Alias routes under `/study-plans`:
  - POST `/study-plans/` — same as `/plans/generate`
  - PUT `/study-plans/{plan_id}` — update plan
  - GET `/study-plans/{plan_id}` — get plan by id

Notes:
- If `OPENROUTER_API_KEY` is missing or rate-limited, plan generation falls back to a local simple plan and returns `{ "fallback": true }`.

Memory (`/memory`)
------------------
- POST `/memory/short` — append short memory
- GET `/memory/short/{user_id}` — get short memory
- POST `/memory/long` — set long memory item
- GET `/memory/long/{user_id}/{key}` — get long memory
- GET `/memory/long/list/{user_id}` — list long memory items

Development Notes
-----------------
- Startup/shutdown use FastAPI lifespan (no deprecated on_event).
- Database sessions via `app/db/db.py` (`get_db`, `SessionLocal`).
- JSONL audit logs for submissions at `app/data/submissions.jsonl`.

Running Examples
----------------

Create a user:
```bash
curl -s -X POST http://127.0.0.1:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@example.com","name":"Student One"}' | jq
```

List users:
```bash
curl -s http://127.0.0.1:8000/users/ | jq
```

Generate a study plan (fallback if OpenRouter unavailable):
```bash
curl -s -X POST http://127.0.0.1:8000/plans/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"hours_per_week":10,"target_date":"2025-12-31","preferred_days":["Mon","Wed"],"goal":"Placement in 3 months"}' | jq
```

Create a simple submission:
```bash
curl -s -X POST http://127.0.0.1:8000/submissions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"question_id":"Q123","topic":"arrays","score":60,"passed":3,"total":5}' | jq
```

List submissions by user:
```bash
curl -s http://127.0.0.1:8000/submissions/user/1 | jq
```

