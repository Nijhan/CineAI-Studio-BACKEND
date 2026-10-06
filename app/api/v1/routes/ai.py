from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.asset import Asset
from app.models.job import Job
from app.models.caption import Caption
from app.schemas.schemas import AutoTrimRequest, VoiceEnhanceRequest, CaptionRequest, CopilotRequest, CopilotResponse, JobOut
from app.services import tasks
from app.services.copilot_service import copilot_chat

router = APIRouter(prefix="/ai", tags=["ai"])


async def _get_asset(asset_id, user: User, db: AsyncSession) -> Asset:
    result = await db.execute(select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


async def _create_job(db: AsyncSession, user: User, job_type: str, project_id=None, input_data: dict = {}) -> Job:
    job = Job(user_id=user.id, project_id=project_id, type=job_type, input=input_data)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/auto-trim", response_model=JobOut, status_code=202)
async def auto_trim(body: AutoTrimRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    asset = await _get_asset(body.asset_id, user, db)
    job = await _create_job(db, user, "auto_trim", asset.project_id, body.model_dump(mode="json"))
    tasks.auto_trim_task.delay(str(job.id), asset.url, body.silence_threshold_db, body.min_silence_ms)
    return job


@router.post("/voice-enhance", response_model=JobOut, status_code=202)
async def voice_enhance(body: VoiceEnhanceRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    asset = await _get_asset(body.asset_id, user, db)
    job = await _create_job(db, user, "voice_enhance", asset.project_id, body.model_dump(mode="json"))
    tasks.voice_enhance_task.delay(str(job.id), asset.url, body.noise_reduction, body.normalize)
    return job


@router.post("/captions", response_model=JobOut, status_code=202)
async def generate_captions(body: CaptionRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    asset = await _get_asset(body.asset_id, user, db)
    job = await _create_job(db, user, "generate_captions", asset.project_id, body.model_dump(mode="json"))
    tasks.generate_captions_task.delay(str(job.id), asset.url, body.language, body.preset)
    return job


@router.post("/copilot", response_model=CopilotResponse)
async def copilot(body: CopilotRequest, user: User = Depends(get_current_user)):
    result = await copilot_chat(body.message, body.history)
    return CopilotResponse(**result)


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == user.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
