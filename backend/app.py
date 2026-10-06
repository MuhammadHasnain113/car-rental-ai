import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.conversation_manager import manager
from backend.llm_service import stream_chat_completion

app = FastAPI(title="ApexDrive AI - Car Rental System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "default_session")
    session = manager.get_or_create_session(session_id)

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)

            if data.get("action") == "reset":
                manager.reset_session(session_id)
                await websocket.send_json({"type": "reset_ack"})
                continue

            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            # Handle turn-taking cleanly: check if previous turn is still generating
            if session.lock.locked():
                await websocket.send_json({
                    "type": "error", 
                    "message": "Assistant is still responding. Please wait for the current turn to finish."
                })
                continue

            async with session.lock:
                # Orchestrate structured prompt messages
                messages = manager.build_orchestrated_prompt(session_id, user_message)
                full_reply = []

                # Stream response
                async for token in stream_chat_completion(messages):
                    full_reply.append(token)
                    await websocket.send_json({"type": "token", "token": token})

                # End of turn
                await websocket.send_json({"type": "done"})
                
                # Commit turns to session history
                complete_text = "".join(full_reply)
                manager.record_turn(session_id, "user", user_message)
                manager.record_turn(session_id, "assistant", complete_text)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})