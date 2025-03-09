from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

from apis import audio_loop

router = APIRouter()

@router.websocket("/multimodal")
#async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
async def gemini_session_handler(websocket: WebSocket):
    """Handles the interaction with Gemini API within a websocket session."""

    await websocket.accept()

    audio = audio_loop.AudioLoop()
    await audio.run(websocket=websocket)
