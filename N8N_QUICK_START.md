# n8n으로 미디어 모니터 자동화하기 🚀

**예상 소요 시간**: 15분  
**비용**: 완전 무료 ✅

---

## 🎯 n8n이란?

- 오픈소스 워크플로우 자동화 도구
- 시각적 편집기로 쉽게 자동화 구성
- **완전 무료** (self-hosted)
- 정확한 스케줄링 (크론 표현식 지원)

---

## 📋 사전 준비사항

### 필수:
1. ✅ Docker Desktop 설치 (Windows/Mac/Linux)
2. ✅ MS Teams Webhook URL
3. ✅ Gemini API Key

### Docker 설치 확인:
```bash
docker --version
docker-compose --version
```

Docker가 없으면: https://www.docker.com/products/docker-desktop

---

## 🚀 방법 1: Docker Compose로 빠른 시작 (추천)

### 1단계: 환경변수 파일 생성

`.env` 파일 생성 (`.env.example` 참고):

```bash
# .env 파일 내용
TEAMS_WEBHOOK_URL=https://your-teams-webhook-url
GEMINI_API_KEY=your-gemini-api-key
N8N_BASIC_AUTH_PASSWORD=your-secure-password
```

**중요**: 반드시 본인의 값으로 변경하세요!

### 2단계: Docker Compose 실행

프로젝트 폴더에서 실행:

```bash
# n8n 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f n8n
```

### 3단계: n8n 웹 인터페이스 접속

브라우저에서 접속:
```
http://localhost:5678
```

**로그인 정보**:
- Username: `admin`
- Password: `.env`에 설정한 비밀번호

---

## ⚙️ 워크플로우 설정

### 방법 A: JSON 파일 임포트 (가장 쉬움)

1. n8n 웹 인터페이스 접속 (http://localhost:5678)
2. 좌측 메뉴에서 **"Workflows"** 클릭
3. 우측 상단 **"Add workflow"** → **"Import from File"** 클릭
4. `n8n-workflow.json` 파일 선택
5. **"Save"** 클릭
6. 우측 상단 **"Active"** 토글 켜기 ✅

**완료!** 이제 자동으로 스케줄에 따라 실행됩니다.

---

### 방법 B: 수동으로 워크플로우 생성

#### 1️⃣ 새 워크플로우 만들기
- 좌측 메뉴 **"Workflows"** → **"Add workflow"**
- 이름: `언론계 인사/부고 모니터링`

#### 2️⃣ Schedule Trigger 노드 추가
- 왼쪽 **"+"** 버튼 → **"Schedule Trigger"** 검색
- 설정:
  - **Mode**: `Custom`
  - **Cron Expression**: `0 1,3,5,7,9 * * *`
  - **Timezone**: `Asia/Seoul`

#### 3️⃣ Execute Command 노드 추가
- Schedule Trigger 오른쪽 **"+"** 버튼
- **"Execute Command"** 검색 후 선택
- 설정:
  - **Command**: `cd /workspace && python scraper.py`
  - **Environment Variables** (Add Field 클릭):
    ```
    GEMINI_API_KEY={{ $env.GEMINI_API_KEY }}
    TEAMS_WEBHOOK_URL={{ $env.TEAMS_WEBHOOK_URL }}
    ```

#### 4️⃣ 워크플로우 저장 및 활성화
- 우측 상단 **"Save"** 클릭
- **"Active"** 토글 켜기 ✅

---

## 🧪 테스트 실행

### 수동으로 즉시 실행하기:

1. 워크플로우 편집 화면에서
2. 좌측 **Schedule Trigger 노드** 클릭
3. 우측 상단 **"Test workflow"** 버튼 클릭
4. 실행 결과 확인

### 성공 확인:
- ✅ Execute Command 노드가 녹색으로 표시됨
- ✅ Output에서 성공 로그 확인
- ✅ MS Teams에 알림 도착

---

## 📊 실행 스케줄

설정된 크론 스케줄 (한국시간):
```
0 1,3,5,7,9 * * *
```

실행 시간:
- 🕙 오전 10시 (UTC 01:00)
- 🕛 낮 12시 (UTC 03:00)
- 🕑 오후 2시 (UTC 05:00)
- 🕓 오후 4시 (UTC 07:00)
- 🕕 오후 6시 (UTC 09:00)

---

## 📈 모니터링

### 실행 기록 확인:
1. 좌측 메뉴 **"Executions"** 클릭
2. 각 실행 클릭하여 상세 로그 확인

### 실행 통계:
- ✅ 성공/실패 횟수
- ⏱️ 실행 시간
- 📝 상세 로그

---

## 🔧 트러블슈팅

### ❌ Docker 컨테이너가 시작되지 않음

**확인사항**:
```bash
# Docker 상태 확인
docker ps -a

# n8n 컨테이너 로그 확인
docker-compose logs n8n

# Docker Desktop 실행 확인 (Windows/Mac)
```

**해결**:
- Docker Desktop이 실행 중인지 확인
- 포트 5678이 이미 사용 중인지 확인
  ```bash
  # Windows
  netstat -ano | findstr :5678
  
  # Mac/Linux
  lsof -i :5678
  ```

---

### ❌ Python 스크립트 실행 오류

**증상**: Execute Command 노드에서 `python: command not found`

**원인**: n8n 컨테이너에 Python이 설치되지 않음

**해결 방법 1**: Python 포함 커스텀 이미지 사용

`Dockerfile` 생성:
```dockerfile
FROM n8nio/n8n:latest

USER root

# Python 및 pip 설치
RUN apk add --no-cache python3 py3-pip

# 필요한 Python 패키지 설치
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

USER node
```

`docker-compose.yml` 수정:
```yaml
services:
  n8n:
    build: .  # image 대신 build 사용
    # ... 나머지 설정 동일
```

빌드 및 실행:
```bash
docker-compose build
docker-compose up -d
```

---

### ❌ 환경변수가 인식되지 않음

**확인**:
1. `.env` 파일이 `docker-compose.yml`과 같은 폴더에 있는지 확인
2. `.env` 파일 내용 확인:
   ```bash
   cat .env
   ```

**해결**:
```bash
# 컨테이너 재시작
docker-compose down
docker-compose up -d
```

---

### ❌ 스케줄이 실행되지 않음

**확인사항**:
1. 워크플로우가 **"Active"** 상태인지 확인
2. n8n 컨테이너가 실행 중인지 확인:
   ```bash
   docker ps | grep n8n
   ```

**해결**:
- 워크플로우 편집 화면에서 우측 상단 **"Active"** 토글 켜기
- 컨테이너 재시작:
  ```bash
  docker-compose restart n8n
  ```

---

### ❌ Teams 알림이 오지 않음

**확인**:
1. n8n Executions 탭에서 실행 로그 확인
2. Python 스크립트 실행 성공 여부 확인
3. Webhook URL이 올바른지 확인

**해결**:
```bash
# 로컬에서 스크립트 직접 테스트
cd /path/to/media_monitor
python scraper.py
```

---

## 🎨 워크플로우 구조

```
[Schedule Trigger]
    ↓
[Execute Command: python scraper.py]
    ↓
[IF: Exit Code = 0?]
    ↓ Yes         ↓ No
[성공 로그]    [에러 로그]
```

**각 노드의 역할**:
1. **Schedule Trigger**: 지정된 시간에 자동 실행
2. **Execute Command**: Python 스크립트 실행
3. **IF**: 실행 성공 여부 확인
4. **성공/에러 로그**: 결과 기록

---

## 💻 명령어 모음

### Docker 컨테이너 관리
```bash
# n8n 시작
docker-compose up -d

# n8n 중지
docker-compose down

# n8n 재시작
docker-compose restart

# 로그 실시간 보기
docker-compose logs -f n8n

# 컨테이너 상태 확인
docker ps

# 컨테이너 내부 접속 (디버깅)
docker exec -it media-monitor-n8n sh
```

### n8n 데이터 관리
```bash
# 모든 워크플로우 백업
docker cp media-monitor-n8n:/home/node/.n8n ./n8n-backup

# 데이터 복원
docker cp ./n8n-backup/. media-monitor-n8n:/home/node/.n8n

# 데이터 완전 삭제 (주의!)
docker-compose down -v
```

---

## 📦 파일 구조

```
media_monitor/
├── docker-compose.yml          # Docker Compose 설정
├── n8n-workflow.json           # n8n 워크플로우 (임포트용)
├── .env                        # 환경변수 (생성 필요)
├── .env.example                # 환경변수 예시
├── scraper.py                  # 메인 스크립트
├── requirements.txt            # Python 패키지
├── media_list_cleaned.txt      # 언론사 리스트
└── N8N_QUICK_START.md          # 이 파일
```

---

## 🌐 외부 접속 설정 (선택사항)

### 방법 1: ngrok 사용 (가장 쉬움)

집 밖에서도 n8n에 접속하려면:

```bash
# ngrok 설치 (https://ngrok.com)
ngrok http 5678
```

ngrok이 제공하는 URL로 접속 가능:
```
https://abc123.ngrok.io
```

### 방법 2: 클라우드 서버에 배포

**AWS EC2 / Google Cloud / Azure**에 배포:
1. 서버 인스턴스 생성
2. Docker 설치
3. 동일한 `docker-compose.yml` 사용
4. 방화벽에서 포트 5678 오픈

---

## 🎯 n8n vs GitHub Actions 비교

| 항목 | GitHub Actions (무료) | n8n (self-hosted) |
|------|---------------------|-------------------|
| **스케줄 정확도** | ❌ 10분~1시간 지연 | ✅ 정확함 |
| **비용** | ✅ 무료 | ✅ 무료 |
| **설정 난이도** | 🟢 쉬움 | 🟡 보통 |
| **모니터링** | 🟡 기본 | ✅ 실시간 대시보드 |
| **수동 실행** | 🟡 가능 | ✅ 원클릭 |
| **로그** | 🟡 텍스트만 | ✅ 시각적 |
| **유연성** | 🟡 제한적 | ✅ 매우 높음 |

---

## 🔄 업데이트 방법

### 코드 변경 시:
```bash
# 1. 코드 수정 (scraper.py 등)
# 2. Docker 컨테이너 재시작
docker-compose restart n8n

# 또는 워크플로우에서 수동 실행
```

### n8n 버전 업데이트:
```bash
docker-compose pull
docker-compose up -d
```

---

## ✨ 추가 기능 아이디어

n8n에서 추가로 구현 가능한 기능:

1. **Slack 알림 추가**
   - HTTP Request 노드로 Slack Webhook 호출

2. **이메일 알림**
   - Email 노드로 이메일 전송

3. **데이터베이스 저장**
   - PostgreSQL 노드로 기사 데이터 저장

4. **에러 알림**
   - 실패 시 특정 채널로 알림

5. **통계 대시보드**
   - 수집된 데이터를 시각화

---

## 🎉 완료!

이제 n8n이 정확한 시간에 자동으로:
1. ✅ 연합뉴스 스크래핑
2. ✅ Gemini AI 필터링
3. ✅ MS Teams 알림 전송

**n8n의 장점**:
- ⏰ 정확한 스케줄링
- 📊 실시간 모니터링
- 🔄 원클릭 수동 실행
- 💰 완전 무료
- 🎨 시각적 워크플로우

---

## 📞 도움이 필요하면?

1. n8n 로그 확인: `docker-compose logs -f n8n`
2. Python 스크립트 로컬 테스트: `python scraper.py`
3. n8n 커뮤니티: https://community.n8n.io

**수고하셨습니다! 🎉**
