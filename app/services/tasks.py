import uuid
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from app.services.celery_app import celery_app
from app.core.config import settings
from app.models.job import Job

engine = create_engine(settings.SYNC_DATABASE_URL)


def _update_job(job_id: str, **kwargs):
    with Session(engine) as db:
        db.execute(update(Job).where(Job.id == uuid.UUID(job_id)).values(**kwargs))
        db.commit()


def _emit_progress(job_id: str, progress: int, status: str = "processing"):
    """Push progress via Redis pub/sub — Socket.IO server subscribes."""
    import redis as redis_lib, json
    r = redis_lib.from_url(settings.REDIS_URL)
    r.publish("job_progress", json.dumps({"job_id": job_id, "progress": progress, "status": status}))


# ── Auto Trim ─────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="auto_trim")
def auto_trim_task(self, job_id: str, asset_url: str, silence_threshold_db: float, min_silence_ms: int):
    try:
        _update_job(job_id, status="processing", progress=10)
        _emit_progress(job_id, 10)

        # TODO: integrate ffmpeg silence detection + trim
        # Placeholder: returns mock trim points
        trim_points = [{"start_ms": 0, "end_ms": 5000}, {"start_ms": 6000, "end_ms": 12000}]

        _update_job(job_id, status="done", progress=100, output={"trim_points": trim_points})
        _emit_progress(job_id, 100, "done")
        return {"trim_points": trim_points}
    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc))
        _emit_progress(job_id, 0, "failed")
        raise


# ── Voice Enhance ─────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="voice_enhance")
def voice_enhance_task(self, job_id: str, asset_url: str, noise_reduction: bool, normalize: bool):
    try:
        _update_job(job_id, status="processing", progress=10)
        _emit_progress(job_id, 10)

        # TODO: integrate noisereduce / ffmpeg loudnorm filter
        # Placeholder: returns enhanced asset key
        enhanced_key = f"processed/{uuid.uuid4()}_enhanced.mp3"

        _update_job(job_id, status="done", progress=100, output={"enhanced_key": enhanced_key})
        _emit_progress(job_id, 100, "done")
        return {"enhanced_key": enhanced_key}
    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc))
        _emit_progress(job_id, 0, "failed")
        raise


# ── Captions ──────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="generate_captions")
def generate_captions_task(self, job_id: str, asset_url: str, language: str, preset: str):
    try:
        _update_job(job_id, status="processing", progress=10)
        _emit_progress(job_id, 10)

        from openai import OpenAI
        import httpx, tempfile, os

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Download asset to temp file for Whisper
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(httpx.get(asset_url).content)
            tmp_path = tmp.name

        _emit_progress(job_id, 40)

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        os.unlink(tmp_path)

        segments = [
            {"start_ms": int(s.start * 1000), "end_ms": int(s.end * 1000), "text": s.text}
            for s in transcript.segments
        ]

        _update_job(job_id, status="done", progress=100, output={"segments": segments, "preset": preset})
        _emit_progress(job_id, 100, "done")
        return {"segments": segments}
    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc))
        _emit_progress(job_id, 0, "failed")
        raise


# ── Export ────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="export_project")
def export_project_task(self, job_id: str, project_id: str, format: str, resolution: str, preset: str):
    try:
        _update_job(job_id, status="processing", progress=5)
        _emit_progress(job_id, 5)

        # TODO: integrate ffmpeg render pipeline
        # Placeholder: returns mock export URL
        export_key = f"exports/{project_id}/{uuid.uuid4()}.{format}"

        _update_job(job_id, status="done", progress=100, output={"export_key": export_key})
        _emit_progress(job_id, 100, "done")
        return {"export_key": export_key}
    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc))
        _emit_progress(job_id, 0, "failed")
        raise
