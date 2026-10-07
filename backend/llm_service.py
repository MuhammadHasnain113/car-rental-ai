import json
import httpx
from typing import AsyncGenerator, List

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"  # 1.5B fits the 0.5B-4B requirement and runs fast on CPU

async def stream_chat_completion(messages: List[dict]) -> AsyncGenerator[str, None]:
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.0,
            "top_p": 0.1,
            "top_k": 20
        }
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream("POST", OLLAMA_CHAT_URL, json=payload) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                body = json.loads(line)
                token = body.get("message", {}).get("content", "")
                if token:
                    yield token