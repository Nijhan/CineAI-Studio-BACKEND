import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Any


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str = "Untitled Project"
    description: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    settings: dict | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    thumbnail_url: str | None
    duration_ms: int
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Assets ────────────────────────────────────────────────────────────────────

class AssetOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    filename: str
    url: str
    size_bytes: int | None
    duration_ms: int | None
    metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Jobs ──────────────────────────────────────────────────────────────────────

class JobOut(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    progress: int
    output: dict
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── AI ────────────────────────────────────────────────────────────────────────

class AutoTrimRequest(BaseModel):
    asset_id: uuid.UUID
    silence_threshold_db: float = -40.0
    min_silence_ms: int = 500


class VoiceEnhanceRequest(BaseModel):
    asset_id: uuid.UUID
    noise_reduction: bool = True
    normalize: bool = True


class CaptionRequest(BaseModel):
    asset_id: uuid.UUID
    preset: str = "default"
    language: str = "en"


class CopilotRequest(BaseModel):
    project_id: uuid.UUID
    message: str = Field(max_length=2000)
    history: list[dict[str, Any]] = []


class CopilotResponse(BaseModel):
    reply: str
    actions: list[dict[str, Any]] = []


# ── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    project_id: uuid.UUID
    format: str = "mp4"          # mp4 | webm | mov
    resolution: str = "1080p"    # 720p | 1080p | 4k
    preset: str = "youtube"      # youtube | tiktok | reels | instagram
