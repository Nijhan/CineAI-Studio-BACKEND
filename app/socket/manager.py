import asyncio
import json
import socketio
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.security import decode_token

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CLIENT_URL,
)


@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        return False
    try:
        user_id = decode_token(token)
        await sio.save_session(sid, {"user_id": user_id})
        await sio.enter_room(sid, f"user_{user_id}")
    except Exception:
        return False


@sio.event
async def disconnect(sid):
    pass


async def _redis_listener():
    """Subscribe to job_progress channel and forward to Socket.IO rooms."""
    r = aioredis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("job_progress")
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            job_id = data.get("job_id")
            # Broadcast to all connected clients — frontend filters by job_id
            await sio.emit("job_progress", data)


def start_listener():
    loop = asyncio.get_event_loop()
    loop.create_task(_redis_listener())
