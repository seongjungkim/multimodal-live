#

Cloud Run에서 WebSocket을 사용하여 서버를 만드는 방법은 일반적인 Python WebSocket 서버를 만드는 방법과 거의 동일하지만, 몇 가지 중요한 고려 사항이 있습니다. Cloud Run은 기본적으로 HTTP/1.1, HTTP/2, gRPC를 지원하며, WebSocket도 이러한 프로토콜 위에서 동작합니다.

스트리밍 오디오 및 동영상 형식에서 Multimodal Live API를 사용하는 방법의 예를 보려면 cookbooks 저장소에서 'Multimodal Live API - Quickstart' 파일을 실행하세요.

<strong>예제 블로그</strong>
- [[FastAPI/Python] 양방향 통신을 위한 웹소켓 in FastAPI](https://dev-in-seoul.tistory.com/45?utm_source=chatgpt.com)  

<strong>SDK / API</strong>
- [Multimodal Live API](https://ai.google.dev/gemini-api/docs/multimodal-live)  
- [Generative AI > Google Gen AI SDK](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)  
- [Google APIs Gen AI SDK](https://googleapis.github.io/python-genai/)  
- [Google Gen AI SDK for Python in Github](https://github.com/googleapis/python-genai)  
- [Cloud Run용 WebSocket 채팅 서비스 빌드 튜토리얼](https://cloud.google.com/run/docs/tutorials/websockets)  
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)  

<strong>소스 / YouTube</strong>
- [GitHub - Multimodal Live API - Quickstart (YouTube)](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py)  
- [Use Gemini 2.0 to Build a Realtime Chat App with Multimodal Live API (YouTube)](https://www.youtube.com/watch?v=y2ETLEZ-oi8)  
- [Backend - Realtime Gemini 2.0 Mobile App for Voice Chat with Camera and Images (Source)](https://github.com/yeyu2/Youtube_demos/tree/main/gemini20-android/Backend)  
- [Multimodal Live API demo: React.js console (YouTube)](https://www.youtube.com/watch?v=J_q7JY1XxFE)  
- [Multimodal Live API - Web console (Source)](https://github.com/google-gemini/multimodal-live-api-web-console)  
- [Multimodal Live API - Web console - GenExplainer (Source)](https://github.com/google-gemini/multimodal-live-api-web-console/tree/demos/genexplainer)  
- [Multimodal Live API - Web console - GenWeather (Source)](https://github.com/google-gemini/multimodal-live-api-web-console/tree/demos/genweather)  
- [Multimodal Live API - Web console - GenList (Source)](https://github.com/google-gemini/multimodal-live-api-web-console/tree/demos/genlist)  

[Source Repositories](https://source.developers.google.com/p/tpcg-datacollector/r/multimodal-live)


## Source Repositories

```bash
git remote add tpcg https://source.developers.google.com/p/tpcg-datacollector/r/multimodal-live)
```

```python
GEN_API_KEY = os.environ.get("GEN_API_KEY", "")
os.environ['GOOGLE_API_KEY'] = GEN_API_KEY
MODEL = "gemini-2.0-flash-exp"  # use your model ID

#instruction_text = "You are a helpful Korean assistant and answer in a friendly Korean."
instruction_text = "당신은 도움이 되는 한국인 조수이고 친절한 한국어로 대답해줍니다."
```

```python
google_search_tool = types.Tool(
    google_search = types.GoogleSearch()
)
```

## Build and Deploy to Cloud Run

```bash
# 프로젝트 ID 설정
PROJECT_ID=qnacom-service
REGION=asia-northeast3
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
APP=websocket-server
API_KEY=AIzaSyDrloo99pXlhA7iN1QDn_5Lw-E6bpys3vg
TAG=gcr.io/$PROJECT_ID/$APP
```

```bash
gcloud init
```

### 프로젝트 ID 설정

```bash
gcloud config set project $PROJECT_ID
```

```bash
gcloud builds submit --project=$PROJECT_ID --tag $TAG
```

### 타임아웃 설정 (최대 1시간, 필요에 따라 조정)
### 최대 인스턴스 수 (필요에 따라 조정)

```bash
gcloud run deploy $APP \
  --image gcr.io/$PROJECT_ID/$APP \
  --platform managed \
  --allow-unauthenticated \
  --region $REGION \
  --set-env-vars REDISHOST=$REDIS_HOST,REDISPORT=$REDIS_PORT,REDISPASSWORD=$REDIS_PASSWORD,GEN_API_KEY=$API_KEY \
  --timeout=3600 \
  --max-instances=10
```

## Run Multimodal Live Server on Compute Engine

```bash
python main_for_mobile.py
```

## Errors

```
https://websocket-server-923091573679.asia-northeast3.run.app/multimodal
INFO: ('169.254.169.126', 47906) - "WebSocket /multimodal" 403
INFO: connection rejected (403 Forbidden)
INFO: connection closed
```