import asyncio
import sys
import uuid

#import aioredis  # asyncio와 함께 사용
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from routers import multimodal_live, text_live

templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.include_router(multimodal_live.router)
app.include_router(text_live.router)

@app.get("/")
async def get(request: Request):
    template_data = {
        "request": request,
        "locale": "ko_KR",
        "uuid": uuid.uuid4()
    }

    response = templates.TemplateResponse("main.html", template_data)
    return response
