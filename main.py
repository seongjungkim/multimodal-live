import asyncio
import base64
import json
import logging
import os
import uuid

from google import genai

#import aioredis  # asyncio와 함께 사용
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI()

"""
# Redis 연결 설정 (Cloud Memorystore 사용 시)
REDIS_HOST = os.environ.get("REDISHOST", "localhost") # Cloud Run에서 환경 변수로 설정.
REDIS_PORT = int(os.environ.get("REDISPORT", 6379))
REDIS_PASSWORD = os.environ.get("REDISPASSWORD", "")  # 필요하면 설정
"""
# Load API key from environment
GEN_API_KEY = os.environ.get("GEN_API_KEY", "")
os.environ['GOOGLE_API_KEY'] = GEN_API_KEY
#os.environ['GOOGLE_API_KEY'] = 'AIzaSyDrloo99pXlhA7iN1QDn_5Lw-E6bpys3vg'
MODEL = "gemini-2.0-flash-exp"  # use your model ID

genai_client = genai.Client(
  http_options={
    'api_version': 'v1alpha',
  }
)

@app.get("/")
async def get(request: Request):
    template_data = {
        "request": request,
        "locale": "ko_KR",
        "uuid": uuid.uuid4()
    }

    response = templates.TemplateResponse("main.html", template_data)
    return response

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    redis = None  # redis 연결 객체의 scope를 try 블럭 안으로.
    try:

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

@app.websocket("/multimdal")
#async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
async def gemini_session_handler(websocket_client: WebSocket):
    """Handles the interaction with Gemini API within a websocket session."""

    await websocket_client.accept()

    try:
        config_message = await websocket_client.recv()
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})
        
        config["system_instruction"] = "You are a daily life assistant."
        

        async with genai_client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")

            async def send_to_gemini():
                """Sends messages from the client websocket to the Gemini API."""
                try:
                  async for message in websocket_client:
                      try:
                          data = json.loads(message)
                          if "realtime_input" in data:
                              for chunk in data["realtime_input"]["media_chunks"]:
                                  if chunk["mime_type"] == "audio/pcm":
                                      #print(f"Chunk data size: {len(chunk['data'])}")
                                      #print(f"Sending audio chunk: {chunk['data'][:5]}")
                                      await session.send(input={"mime_type": "audio/pcm", "data": chunk["data"]})
                                      
                                  elif chunk["mime_type"] == "image/jpeg":
                                      print(f"Sending image chunk: {chunk['data'][:50]}")
                                      await session.send(input={"mime_type": "image/jpeg", "data": chunk["data"]})
                                      
                      except Exception as e:
                          print(f"Error sending to Gemini: {e}")
                  print("Client connection closed (send)")
                except Exception as e:
                     print(f"Error sending to Gemini: {e}")
                finally:
                   print("send_to_gemini closed")


            async def receive_from_gemini():
                """Receives responses from the Gemini API and forwards them to the client, looping until turn is complete."""
                try:
                    while True:
                        try:
                            print("receiving from gemini")
                            async for response in session.receive():
                                if response.server_content is None:
                                    print(f'Unhandled server message! - {response}')
                                    continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        if hasattr(part, 'text') and part.text is not None:
                                            #await client_websocket.send(json.dumps({"text": part.text}))
                                            await websocket_client.send(json.dumps({"text": part.text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            print("audio mime_type:", part.inline_data.mime_type)
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            
                                            #await client_websocket.send(json.dumps({"audio": base64_audio}))
                                            await websocket_client.send(json.dumps({"audio": base64_audio}))
                                            
                                            print("audio received")

                                if response.server_content.turn_complete:
                                    print('\n<Turn complete>')
                                    
                        #except websockets.exceptions.ConnectionClosedOK:
                        except WebSocketDisconnect:
                            print("Client connection closed normally (receive)")
                            break  # Exit the loop if the connection is closed
                        except Exception as e:
                            print(f"Error receiving from Gemini: {e}")
                            break 

                except Exception as e:
                      print(f"Error receiving from Gemini: {e}")
                finally:
                      print("Gemini connection closed (receive)")


            # Start send loop
            send_task = asyncio.create_task(send_to_gemini())
            # Launch receive loop as a background task
            receive_task = asyncio.create_task(receive_from_gemini())
            await asyncio.gather(send_task, receive_task)


    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")


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
