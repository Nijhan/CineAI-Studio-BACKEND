from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are CineAI Director, an expert AI video editing copilot.
You help users edit videos through natural language commands.
When a user gives an editing instruction, respond with:
1. A friendly confirmation of what you'll do.
2. A JSON "actions" array describing the editing operations.

Available actions: auto_trim, voice_enhance, add_captions, add_broll, cut_clip,
add_transition, adjust_color, add_music, export.

Always respond in JSON: {"reply": "...", "actions": [...]}"""


async def copilot_chat(message: str, history: list[dict]) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-10:])  # keep last 10 turns for context
    messages.append({"role": "user", "content": message})

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    import json
    return json.loads(response.choices[0].message.content)
