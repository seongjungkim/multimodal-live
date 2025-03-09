#

Cloud Run에서 WebSocket을 사용하여 서버를 만드는 방법은 일반적인 Python WebSocket 서버를 만드는 방법과 거의 동일하지만, 몇 가지 중요한 고려 사항이 있습니다. Cloud Run은 기본적으로 HTTP/1.1, HTTP/2, gRPC를 지원하며, WebSocket도 이러한 프로토콜 위에서 동작합니다.

스트리밍 오디오 및 동영상 형식에서 Multimodal Live API를 사용하는 방법의 예를 보려면 cookbooks 저장소에서 'Multimodal Live API - Quickstart' 파일을 실행하세요.

[Multimodal Live API](https://ai.google.dev/gemini-api/docs/multimodal-live)  
[Cloud Run용 WebSocket 채팅 서비스 빌드 튜토리얼](https://cloud.google.com/run/docs/tutorials/websockets)  
[FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)  
[[FastAPI/Python] 양방향 통신을 위한 웹소켓 in FastAPI](https://dev-in-seoul.tistory.com/45?utm_source=chatgpt.com)  
[GitHub - Multimodal Live API - Quickstart](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py)  

[Source Repositories](https://source.developers.google.com/p/tpcg-datacollector/r/multimodal-live)


```bash
git remote add tpcg https://source.developers.google.com/p/tpcg-datacollector/r/multimodal-live)
```

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

# 타임아웃 설정 (최대 1시간, 필요에 따라 조정)
# 최대 인스턴스 수 (필요에 따라 조정)

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

##

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