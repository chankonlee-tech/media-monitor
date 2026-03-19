# n8n으로 미디어 모니터 시작하기 (5분 완성) ⚡

## 🚀 빠른 시작

### 1단계: 환경변수 설정 (1분)

`.env` 파일 생성:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

`.env` 파일을 열고 본인의 값으로 변경:
```env
TEAMS_WEBHOOK_URL=https://실제-웹훅-URL
GEMINI_API_KEY=실제-API-키
N8N_BASIC_AUTH_PASSWORD=원하는-비밀번호
```

### 2단계: Docker로 n8n 시작 (3분)

```bash
# Docker 이미지 빌드 및 실행
docker-compose up -d

# 로그 확인 (선택사항)
docker-compose logs -f
```

### 3단계: n8n 접속 및 워크플로우 임포트 (1분)

1. 브라우저에서 http://localhost:5678 접속
2. 로그인:
   - Username: `admin`
   - Password: `.env`에 설정한 비밀번호
3. 좌측 메뉴 **"Workflows"** → **"Import from File"**
4. `n8n-workflow.json` 파일 선택
5. 우측 상단 **"Active"** 토글 켜기 ✅

## ✅ 완료!

이제 한국시간 10시, 12시, 14시, 16시, 18시에 자동 실행됩니다!

---

## 🧪 즉시 테스트하기

워크플로우 화면에서:
1. 좌측 **"Schedule Trigger"** 노드 클릭
2. 우측 상단 **"Test workflow"** 버튼 클릭
3. MS Teams에서 알림 확인!

---

## 📊 실행 기록 확인

좌측 메뉴 **"Executions"**에서 모든 실행 기록 확인 가능

---

## 🔧 문제 해결

### Docker가 없다면?
https://www.docker.com/products/docker-desktop 에서 설치

### 포트 5678이 사용 중이라면?
`docker-compose.yml` 파일에서 포트 변경:
```yaml
ports:
  - "8080:5678"  # 8080으로 변경
```

### 자세한 가이드
`N8N_QUICK_START.md` 파일 참고

---

## 💡 명령어 모음

```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 재시작
docker-compose restart

# 로그 보기
docker-compose logs -f
```

---

**더 궁금한 점은 `N8N_QUICK_START.md`를 확인하세요!**
