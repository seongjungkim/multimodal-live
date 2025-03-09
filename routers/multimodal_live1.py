from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

import asyncio
import os
import websockets

from google import genai
from google.genai import types

# Load API key from environment
GEN_API_KEY = os.environ.get("GEN_API_KEY", "")
os.environ['GOOGLE_API_KEY'] = GEN_API_KEY
MODEL = "gemini-2.0-flash-exp"  # use your model ID

CONFIG = {
    "system_instruction": types.Content(
        parts=[
            types.Part(
                text="You are a helpful Korean assistant and answer in a friendly Korean."
                #text="당신은 도움이 되는 한국인 조수이고 친절한 한국어로 대답해줍니다."
            )
        ]
    ),
    "response_modalities": ["AUDIO"]
}

genai_client = genai.Client(
  http_options={
    'api_version': 'v1alpha',
  }
)

@app.websocket("/multimodal2")
#async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
async def gemini_session_handler2(websocket: WebSocket):
    """Handles the interaction with Gemini API within a websocket session."""

    await websocket.accept()

    while True:
        json_data = await websocket.receive_json()
        print("json_data", json_data, flush=True)
        config_message = json_data.get("setup", {})
        print("config_message", config_message, flush=True)

        config = {"response_modalities": ["AUDIO"]}

        async with genai_client.aio.live.connect(model=MODEL, config=config) as session:
            #await send_to_gemini(websocket, session)
            #await receive_from_gemini(websocket, session)
            # Start send loop
            send_task = asyncio.create_task(send_to_gemini(websocket, session))
            # Launch receive loop as a background task
            receive_task = asyncio.create_task(receive_from_gemini(websocket, session))
            await asyncio.gather(send_task, receive_task)
