# Docker 앞 건너뛰고 다시 과거로. 왜 매번 어제 버전이 나올까

태그: #Docker #프론트엔드 #삽질기록 #볼륨마운트 #쿠키의성장기

---

## 문제: 어제의 나를 만나다

지역 필터 기능을 프론트엔드에 추가했다. npm run build 돌렸다. 로컬에서는 잘 보인다.

그런데 Docker 컨테이너를 재시작하는 순간, 지역 필터가 사라진다. 아니, 지역 필터가 아니라 아예 지난 버전의 프론트엔드가 뜬다.

```bash
docker compose down
docker compose up -d web
# 접속하면... 어제 프론트엔드다
```

매 시작마다 시간여행을 한다.

---

## 첫 번째 의심: 로컬 파일이 이상한가?

파일 해시를 비교해봤다.

```bash
# 로컬 app.js
sha256sum static/frontend/assets/app.js

# Docker 안 app.js
docker exec bidcompass_web sha256sum /app/static/frontend/assets/app.js

# 결과: 동일
```

이상하지 않다. 볼륨 마운트도 정상이다. docker-compose.yml에서:

```yaml
volumes:
  - .:/app  # 로컬 root를 /app에 마운트
  - ./data/collected:/app/data/collected
```

로컬 파일이 Docker 안으로 즉시 반영된다. 그러면 왜 어제 버전이 뜰까?

---

## 두 번째 의심: 그러면 왜 옛날 버전이 나오지?

Dockerfile을 들여다봤다.

```dockerfile
# 빌드 단계 (Node)
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
WORKDIR /app
COPY frontend /app/frontend
RUN cd frontend && npm run build
# 결과: /app/static/frontend/assets/app.js

# 배포 단계 (Python)
FROM python:3.10-slim
WORKDIR /app
COPY . .
COPY --from=frontend-builder /app/static/frontend /opt/frontend-dist
# ...

# CMD에서 매 시작시 실행
CMD ["sh", "-c", "mkdir -p /app/static/frontend && cp -r /opt/frontend-dist/. /app/static/frontend/ && ..."]
```

아. **CMD에서 매번 복사한다.**

`cp -r /opt/frontend-dist/. /app/static/frontend/`

이미지 빌드 시점의 프론트엔드를 컨테이너 시작할 때마다 로컬 위에 덮어쓴다.

즉:
1. 이미지 빌드할 때 npm run build 실행 → `/opt/frontend-dist/` 에 저장
2. 컨테이너 시작하면 → `/opt/frontend-dist/`를 `/app/static/frontend/`에 복사
3. 로컬 파일은 맞는데 → 이미지가 이미 옛날 버전이었다

---

## 세 번째 의심: 그런데 이미지는 왜 옛날이야?

내가 프론트엔드를 수정한 후 Docker 이미지를 다시 빌드하지 않았다.

```bash
# 내가 한 것
frontend/src/index.tsx 수정
npm run build  # 로컬에서만 빌드

# 내가 안 한 것
docker compose build web  # 이미지 재빌드
```

로컬 `npm run build`는 `static/frontend/assets/app.js`를 최신으로 만든다. 근데 이미지 안의 `/opt/frontend-dist/`는 여전히 옛날이다.

왜?

Dockerfile의 빌드 단계는 이미지 생성할 때만 실행된다. 로컬 npm run build는 별도다.

결론:
- 로컬 `static/frontend/` → 최신
- 이미지 `/opt/frontend-dist/` → 이전 버전
- CMD 복사 → 이미지 버전이 로컬 위에 덮어쓰기
- 보임 → 이전 버전

---

## 깨달음: 복사하는 게 정상이다, 빌드를 안 한 게 문제다

CMD에서 복사하는 게 문제인 줄 알았는데, 아니었다.

처음엔 "CMD 복사를 스킵하자"고 생각했다. 조건문을 넣었다.

```dockerfile
# 시도 1: 파일 있으면 스킵
CMD ["sh", "-c", "[ ! -f /app/static/frontend/assets/app.js ] && cp -r /opt/frontend-dist/. /app/static/frontend/ || true && ..."]
```

이러면 로컬 파일을 쓴다. 그런데 로컬 파일이 이전 버전이면? → 이전 버전이 계속 뜬다.

더 피곤하다.

정상 워크플로우:
1. 프론트 소스 수정 → `frontend/src/index.tsx`
2. **로컬 빌드** → `npm run build` → `static/frontend/assets/app.js` 업데이트
3. **이미지 재빌드** → `docker compose build web`
4. **컨테이너 재시작** → `docker compose up -d web`
5. CMD 복사 → 최신 이미지의 프론트를 사용

이걸 하면 항상 최신이다.

내가 2번과 3번을 스킵했으니까 당연히 어제 버전이 나온다.

---

## 구조: 어디서 빌드되고 어디서 오는가

```
┌─────────────────────────────────────────────────────┐
│ 로컬 개발자 머신                                      │
├─────────────────────────────────────────────────────┤
│ [frontend/src/index.tsx] (수정)                     │
│          ↓                                          │
│ npm run build (로컬)                                │
│          ↓                                          │
│ [static/frontend/assets/app.js] 최신 ← 볼륨 마운트   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Docker 이미지 빌드 (docker compose build web)       │
├─────────────────────────────────────────────────────┤
│ 1. frontend-builder (Node)                         │
│    COPY frontend/                                  │
│    RUN npm run build                               │
│    → [/app/static/frontend/] 생성                   │
│ 2. COPY --from frontend-builder                    │
│    → [/opt/frontend-dist/] 복사                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Docker 컨테이너 시작 (docker compose up)             │
├─────────────────────────────────────────────────────┤
│ CMD: cp /opt/frontend-dist/. → /app/static/frontend/│
│ (이미지의 프론트를 볼륨 위에 덮어쓰기)               │
│          ↓                                          │
│ 브라우저가 보는 파일 = /opt/frontend-dist/ (최신)   │
│ (또는 이전 버전, 이미지가 오래되면)                 │
└─────────────────────────────────────────────────────┘
```

**핵심**: 볼륨 마운트는 Python 코드 실시간 반영용이다. 프론트는 빌드 산출물이므로 이미지 재빌드가 필수다.

---

## 해결 방법

### Step 1: 로컬에서 프론트 빌드

```bash
cd frontend
npm run build
```

### Step 2: Docker 이미지 재빌드

```bash
docker compose build web
```

여기서 multi-stage 빌드가 실행되고, 최신 프론트가 이미지에 담긴다.

### Step 3: 컨테이너 재시작

```bash
docker compose up -d web
```

CMD가 실행되고, 이미지의 최신 프론트가 `/app/static/frontend/`에 복사된다.

---

## 교훈

### 1. "매번 과거로 돈다"는 증상의 진짜 원인

"내가 뭔가 바꿨는데 왜 안 적용돼?"

→ 로컬은 최신 (npm run build 했으므로)
→ 이미지는 옛날 (재빌드 안 했으므로)
→ CMD 복사가 이미지를 사용하므로 과거가 뜬다

증상만 보면 "아 볼륨 마운트가 문제네"라고 생각하기 쉽다. 근데 볼륨 마운트는 정상이다. **빌드 파이프라인이 깨진 거다.**

### 2. 볼륨 마운트 + CMD 복사의 상호작용

- 볼륨 마운트 (`.:/app`): Python 코드 개발할 때 즉시 반영용
- CMD 복사 (`cp /opt/frontend-dist/...`): 빌드 산출물을 초기화하는 거

둘을 분리해서 이해해야 한다. 프론트는 빌드 산출물이니까 이미지에 담겨서 온다. 파이썬 코드는 원본이니까 볼륨으로 온다.

### 3. 개발 워크플로우를 깨트린 게 문제

잘못된 해결책: "CMD 복사를 조건부로 스킵하자"
→ 이러면 "로컬에 파일이 없으면"이라는 새로운 엣지 케이스가 생긴다.

정답: 빌드 파이프라인을 완성하자.
→ 프론트 수정 → 로컬 빌드 → 이미지 재빌드 → 컨테이너 재시작

이게 정상이다.

---

## 정리: 기억할 것

프론트엔드를 수정했을 때:

```bash
# 1. 로컬 빌드
npm run build

# 2. 이미지 재빌드 (필수!)
docker compose build web

# 3. 컨테이너 재시작
docker compose up -d web
```

이 3단계를 습관화하면 "어제 버전"은 안 본다.

---

## 마지막: Claude가 한 실수

내가 처음 문제를 던졌을 때, Claude는 "CMD 복사를 스킵해 봐"라고 제안했다. 맞는 분석이 아니었다.

원인을 정확히 파악하고 나니, 해결책은 자동으로 나왔다: **docker compose build를 빼먹지 마.**

문제를 풀 때 가정에 의존하면 안 된다. 하나씩 검증해야 한다. (로컬 파일이 맞나? 이미지는? CMD 실행 순서는?)

쿠키는 이제 안다.

Docker는 속지 않는다. 개발자가 차는 경우만 있을 뿐.

---

참고: BidCompass Dockerfile multi-stage 빌드 구조
- Stage 1: Node (frontend 빌드)
- Stage 2: Python (COPY --from으로 이미지에 포함)
- Runtime: Docker Compose 볼륨 마운트 (`.:/app`)
