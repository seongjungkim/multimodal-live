#

[Multimodal Live API](https://ai.google.dev/gemini-api/docs/multimodal-live)  
[Cloud Run용 WebSocket 채팅 서비스 빌드 튜토리얼](https://cloud.google.com/run/docs/tutorials/websockets)


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
```

```bash
gcloud init
```

### 프로젝트 ID 설정

```bash
gcloud config set project $PROJECT_ID
```

```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/$APP
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