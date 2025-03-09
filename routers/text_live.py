from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

import os

from google import genai
from google.genai import types

router = APIRouter()

# Load API key from environment
GEN_API_KEY = os.environ.get("GEN_API_KEY", "")
os.environ['GOOGLE_API_KEY'] = GEN_API_KEY
MODEL = "gemini-2.0-flash-exp"  # use your model ID

genai_client = genai.Client(
  http_options={
    'api_version': 'v1alpha',
  }
)

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

"""
# Redis 연결 설정 (Cloud Memorystore 사용 시)
REDIS_HOST = os.environ.get("REDISHOST", "localhost") # Cloud Run에서 환경 변수로 설정.
REDIS_PORT = int(os.environ.get("REDISPORT", 6379))
REDIS_PASSWORD = os.environ.get("REDISPASSWORD", "")  # 필요하면 설정
"""

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    https://ai.google.dev/gemini-api/docs/multimodal-live?hl=ko#send-receive-text
    """
    await websocket.accept()

    try:

        while True:
            #data = await websocket.receive_text()
            data = await websocket.receive_json()
            print("data", data, flush=True)
            message = data.get("message", "")

            if not message:
                continue

            config = {"response_modalities": ["TEXT"]}

            async with genai_client.aio.live.connect(model=MODEL, config=config) as session:
                #message = data #input("User> " )
                await session.send(input=message, end_of_turn=True)

                await websocket.send_text("##BEGIN##")
                async for response in session.receive():
                    if response.text is not None:
                        await websocket.send_text(response.text)
                        print(response.text, end="", flush=True)
                await websocket.send_text("##END##")

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
        #pass

"""
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    redis = None  # redis 연결 객체의 scope를 try 블럭 안으로.
    try:
        # Redis 연결 (비동기)
        redis = await aioredis.from_url(
            f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}" if REDIS_PASSWORD
            else f"redis://{REDIS_HOST}:{REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
        )

        # 연결 ID를 키로 사용하여 클라이언트 정보 저장 (예시)
        await redis.set(f"client:{client_id}", f"Connected at {asyncio.get_event_loop().time()}")

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")

            # Redis에서 메시지 가져오기 (예시)
            messages = await redis.lrange(f"chat:{client_id}", 0, -1)  # 모든 메시지 가져오기
            print(f"Messages from Redis: {messages}")


            # broadcast 기능 구현 (예시). 모든 클라이언트에게 메시지 전송
            all_clients = await redis.keys("client:*") # 모든 클라이언트 키
            for client_key in all_clients:
                c_id = client_key.split(":")[-1]
                if c_id != client_id: # 자기 자신에게는 보내지 않음.
                    try:
                        # 이부분은, websocket 연결이 끊어지면, send가 실패하게 됨.
                        # 각 클라이언트에 대한 websocket 객체를 얻을 방법 필요. -> 이 예제에서는 구현 안됨.
                        # await get_websocket_by_client_id(c_id).send_text(f"Broadcast from {client_id}: {data}")
                        pass
                    except Exception as e:
                        print(f"Error broadcasting to {c_id}: {e}")
                        # 연결이 끊긴 클라이언트는 삭제
                        await redis.delete(client_key)


            # Redis에 메시지 저장 (예시)
            await redis.rpush(f"chat:{client_id}", data)  # 리스트의 오른쪽에 추가
            await redis.ltrim(f"chat:{client_id}", 0, 99)  # 최대 100개 메시지만 유지 (예시)

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if redis:
             # 연결 종료 시 Redis에서 클라이언트 정보 삭제
            await redis.delete(f"client:{client_id}")
            await redis.close() #연결 종료
        await websocket.close()
"""
