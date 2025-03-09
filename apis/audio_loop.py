import asyncio
import base64
import io
import json
import os
import sys
import traceback
import tracemalloc

#import cv2
#import PIL.Image
#import mss

from google import genai
from google.genai import types

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

"""
https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

시스템 안내 (System Instructions):
https://ai.google.dev/gemini-api/docs/multimodal-live?hl=ko#system-instructions

함수 호출 사용 (Function Calling):
https://ai.google.dev/gemini-api/docs/multimodal-live?hl=ko#function-calling
https://github.com/yeyu2/Youtube_demos/blob/main/gemini20-realtime-function/main.py
"""

GEN_API_KEY = os.environ.get("GEN_API_KEY", "")
os.environ['GOOGLE_API_KEY'] = GEN_API_KEY
MODEL = "gemini-2.0-flash-exp"  # use your model ID

DEFAULT_MODE = "camera"

google_search_tool = types.Tool(
    google_search = types.GoogleSearch()
)

search_books = {
    "function_declarations": [
        {
            "name": "search_books",
            "description": "Retrieve books from the Google Books API.",
            "parameters": {
                "type": "OBJECT",
                "properties": {

                },
                "required": [],
            }
        }
    ]
}

CONFIG = {
    "system_instruction": types.Content(
        parts=[
            types.Part(
                #text="You are a helpful Korean assistant and answer in a friendly Korean."
                text="당신은 도움이 되는 한국인 조수이고 친절한 한국어로 대답해줍니다."
            )
        ]
    ),
    "tools": [google_search_tool],
    "response_modalities": ["AUDIO"]
}

tracemalloc.start()  # tracemalloc 시작

genai_client = genai.Client(
  http_options={
    'api_version': 'v1alpha',
  }
)


if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup

    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup


#
def search_books():
    return {}

class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode

        self.audio_in_queue = None
        self.out_queue = None

        self.session = None

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None

    async def send_text(self):
        print('send_text', flush=True)
        
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            await self.session.send(input=text or ".", end_of_turn=True)

    async def send_realtime(self):
        print('send_realtime', flush=True)
        
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        print('listen_audio', flush=True)

        try:
            while True:
                json_data = await self.websocket.receive_json()
                print("data", json_data, flush=True)

                if "realtime_input" in json_data:
                    for chunk in json_data["realtime_input"]["media_chunks"]:
                        #print("chunk", chunk, flush=True)
                        mime_type = chunk.get("mime_type", "")
                        #print("mime_type", mime_type, flush=True)

                        if mime_type == "audio/pcm":
                            # 오디오 청크 전송 (디버깅용 로그 - 실제 사용 시에는 제거)
                            #print(f"Chunk data size: {len(chunk['data'])}", flush=True)
                            #print(f"Sending audio chunk: {chunk['data'][:5]}")
                            await self.out_queue.put({"mime_type": mime_type, "data": chunk["data"]})

                        elif mime_type == "image/jpeg":
                            # 이미지 청크 전송 (디버깅용 로그 - 실제 사용 시에는 제거)
                            # print(f"이미지 청크 전송: {chunk['data'][:50]}")
                            await self.session.send(input={"mime_type": mime_type, "data": chunk["data"]})

                        elif mime_type == "plain/text":
                            # 텍스트 청크 전송 (디버깅용 로그 - 실제 사용 시에는 제거)
                            # print(f"텍스트 청크 전송: {chunk['data'][:50]}")
                            await self.session.send(input=chunk["data"] or ".", end_of_turn=True)

        except WebSocketDisconnect:
            print("Client connection closed normally (receive)")
        except Exception as e:
            print(f"Error receiving from client: {e}")

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        print('receive_audio', flush=True)
        
        while True:
            if not self.session:
                continue

            print('Receiving audio', flush=True)
            turn = self.session.receive()
            async for response in turn:
                #print('response', response, flush=True)
                print('response.data', response.data, flush=True)
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                    continue

                if text := response.text:
                    print(text, end="")
        
            # If you interrupt the model, it sends a turn_complete.
            # For interruptions to work, we need to stop playback.
            # So empty out the audio queue because it may have loaded
            # much more audio than has played yet.
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def send_audio(self):
        print('send_audio', flush=True)
        
        try:
            while True:
                bytestream = await self.audio_in_queue.get()
                #print('bytestream', bytestream, flush=True)
                #print("audio mime_type:", part.inline_data.mime_type)
                base64_audio = base64.b64encode(bytestream).decode('utf-8')
                                            
                sent_data = {"audio": base64_audio}
                #print('Sending audio', sent_data, flush=True)
                await self.websocket.send_json(sent_data)
                print('Sent audio', flush=True)
                #self.audio_in_queue.task_done()

        except WebSocketDisconnect:
            print("Client connection closed normally (send)")
        except Exception as e:
            print(f"Error sending to client: {e}")

    async def run(self, websocket):
        self.websocket = websocket

        try:
            async with (
                genai_client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                # Start send loop
                #send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.send_audio())

                #await send_text_task
                #raise asyncio.CancelledError("User requested exit")
        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            self.audio_stream.close()
            traceback.print_exception(EG)

    """
    def _get_frame(self, cap):
        # Read the frameq
        ret, frame = cap.read()
        # Check if the frame was read successfully
        if not ret:
            return None
        # Fix: Convert BGR to RGB color space
        # OpenCV captures in BGR but PIL expects RGB format
        # This prevents the blue tint in the video feed
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)  # Now using RGB frame
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}
    
    async def get_frames(self):
        # This takes about a second, and will block the whole program
        # causing the audio pipeline to overflow if you don't to_thread it.
        cap = await asyncio.to_thread(
            cv2.VideoCapture, 0
        )  # 0 represents the default camera

        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)

        # Release the VideoCapture object
        cap.release()

    def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):

        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)"
    """
