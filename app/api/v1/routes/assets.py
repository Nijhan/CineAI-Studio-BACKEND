from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.asset import Asset
from app.models.project import Project
from app.schemas.schemas import AssetOut
from app.services.s3_service import generate_upload_key, create_presigned_upload, get_public_url, delete_object

router = APIRouter(prefix="/projects/{project_id}/assets", tags=["assets"])


class PresignRequest(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    duration_ms: int | None = None
    type: str  # video | audio | image


class ConfirmUploadRequest(BaseModel):
    s3_key: str
    filename: str
    type: str
    size_bytes: int
    duration_ms: int | None = None
    metadata: dict = {}


async def _get_project(project_id: str, user: User, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/presign")
async def presign_upload(
    project_id: str,
    body: PresignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project(project_id, user, db)
    key = generate_upload_key(str(user.id), body.filename)
    url = create_presigned_upload(key, body.content_type)
    return {"upload_url": url, "s3_key": key}


@router.post("", response_model=AssetOut, status_code=201)
async def confirm_upload(
    project_id: str,
    body: ConfirmUploadRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project(project_id, user, db)
    asset = Asset(
        project_id=project_id,
        user_id=user.id,
        type=body.type,
        filename=body.filename,
        s3_key=body.s3_key,
        url=get_public_url(body.s3_key),
        size_bytes=body.size_bytes,
        duration_ms=body.duration_ms,
        metadata=body.metadata,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("", response_model=list[AssetOut])
async def list_assets(project_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _get_project(project_id, user, db)
    result = await db.execute(select(Asset).where(Asset.project_id == project_id, Asset.user_id == user.id))
    return result.scalars().all()


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(project_id: str, asset_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    delete_object(asset.s3_key)
    await db.delete(asset)
    await db.commit()
