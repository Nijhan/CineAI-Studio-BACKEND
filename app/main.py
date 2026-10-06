from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from app.core.config import settings
from app.api.v1 import router as api_router
from app.socket.manager import sio, start_listener


def create_app() -> FastAPI:
    app = FastAPI(title="CineAI Studio API", version="1.0.0", docs_url="/docs")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CLIENT_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def startup():
        start_listener()

    return app


fastapi_app = create_app()

# Mount Socket.IO as ASGI sub-app
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
