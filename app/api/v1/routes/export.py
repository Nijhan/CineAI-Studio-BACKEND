from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.job import Job
from app.schemas.schemas import ExportRequest, JobOut
from app.services import tasks
from app.services.s3_service import create_presigned_download

router = APIRouter(prefix="/export", tags=["export"])


@router.post("", response_model=JobOut, status_code=202)
async def export_project(body: ExportRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Project).where(Project.id == body.project_id, Project.user_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    job = Job(user_id=user.id, project_id=body.project_id, type="export", input=body.model_dump(mode="json"))
    db.add(job)
    await db.commit()
    await db.refresh(job)

    tasks.export_project_task.delay(str(job.id), str(body.project_id), body.format, body.resolution, body.preset)
    return job


@router.get("/download/{job_id}")
async def get_download_url(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == user.id, Job.type == "export"))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    if job.status != "done":
        raise HTTPException(status_code=400, detail=f"Export not ready, status: {job.status}")

    export_key = job.output.get("export_key")
    if not export_key:
        raise HTTPException(status_code=500, detail="Export key missing")

    return {"download_url": create_presigned_download(export_key)}
