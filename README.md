# CineAI Studio — Backend

FastAPI + PostgreSQL + Redis + Celery + AWS S3 + OpenAI

## Stack
| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy (async) + Alembic |
| Cache / Queue | Redis + Celery |
| Storage | AWS S3 (presigned uploads) |
| AI | OpenAI GPT-4o (copilot) + Whisper (captions) |
| Real-time | Socket.IO (job progress) |

## Project Structure
```
app/
├── api/v1/routes/   # auth, projects, assets, ai, export
├── core/            # config, security, deps
├── db/              # session, base
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic schemas
├── services/        # S3, Celery tasks, AI copilot
└── socket/          # Socket.IO real-time manager
alembic/             # DB migrations
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in all values in .env

# 3. Run DB migrations
alembic upgrade head

# 4. Start API server
python main.py

# 5. Start Celery worker (separate terminal)
celery -A app.services.celery_app worker --loglevel=info
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Current user |
| PATCH | `/api/v1/auth/me` | Update profile |
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/:id` | Get project |
| PATCH | `/api/v1/projects/:id` | Update project |
| DELETE | `/api/v1/projects/:id` | Delete project |
| POST | `/api/v1/projects/:id/assets/presign` | Get S3 upload URL |
| POST | `/api/v1/projects/:id/assets` | Confirm upload |
| GET | `/api/v1/projects/:id/assets` | List assets |
| DELETE | `/api/v1/projects/:id/assets/:id` | Delete asset |
| POST | `/api/v1/ai/auto-trim` | Smart auto-trim job |
| POST | `/api/v1/ai/voice-enhance` | Voice enhancement job |
| POST | `/api/v1/ai/captions` | Generate captions (Whisper) |
| POST | `/api/v1/ai/copilot` | AI director chat |
| GET | `/api/v1/ai/jobs/:id` | Poll job status |
| POST | `/api/v1/export` | Export project |
| GET | `/api/v1/export/download/:job_id` | Get download URL |
| GET | `/health` | Health check |

## Real-time (Socket.IO)
Connect with JWT auth token. Listen for `job_progress` events:
```json
{ "job_id": "...", "progress": 75, "status": "processing" }
```

## Interactive Docs
`http://localhost:5000/docs`
