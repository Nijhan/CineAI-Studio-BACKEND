from fastapi import APIRouter
from app.api.v1.routes import auth, projects, assets, ai, export

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(projects.router)
router.include_router(assets.router)
router.include_router(ai.router)
router.include_router(export.router)
