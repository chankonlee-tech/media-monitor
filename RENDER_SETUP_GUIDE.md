# Render로 미디어 모니터 배포하기 🚀

**예상 소요 시간**: 10분  
**비용**: 무료 ✅

---

## 📋 사전 준비사항

1. ✅ GitHub 계정 (이미 있음)
2. ✅ Render 계정 (없으면 가입 필요)
3. ✅ MS Teams Webhook URL
4. ✅ Gemini API Key

---

## 🎯 1단계: GitHub 저장소 확인

### 현재 상태 확인
```bash
git status
```

### 필요한 파일들이 있는지 확인:
- ✅ `scraper.py` - 메인 스크립트
- ✅ `requirements.txt` - Python 패키지
- ✅ `render.yaml` - Render 설정 파일
- ✅ `media_list_cleaned.txt` 또는 `media_list.txt` - 언론사 리스트

### 변경사항 커밋 및 푸시
```bash
git add .
git commit -m "feat: Render 배포 설정 추가"
git push origin main
```

---

## 🌐 2단계: Render 계정 만들기

### 1. Render 웹사이트 접속
https://render.com

### 2. 회원가입
- **GitHub 계정으로 가입** 추천 (자동 연동)
- 또는 이메일로 가입

### 3. 이메일 인증
- 가입 후 이메일 인증 링크 클릭

---

## ⚙️ 3단계: Render에서 Cron Job 생성

### 1. Dashboard에서 "New +" 버튼 클릭

### 2. "Cron Job" 선택

### 3. GitHub 저장소 연결
- "Connect a repository" 클릭
- GitHub 계정 연결 (권한 승인)
- `media_monitor` 저장소 선택
- "Connect" 클릭

### 4. 기본 설정 입력

| 항목 | 값 |
|------|-----|
| **Name** | `media-monitor-cron` (또는 원하는 이름) |
| **Region** | `Singapore` 추천 (한국과 가까움) |
| **Branch** | `main` (또는 `master`) |
| **Runtime** | `Python 3` (자동 감지됨) |

### 5. Build & Start Commands

**Render가 자동으로 `render.yaml`을 감지합니다!**

만약 수동 입력이 필요하면:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python scraper.py`

### 6. 스케줄 설정

**Cron Expression**: `0 1,3,5,7,9 * * *`

이 설정은 UTC 기준:
- UTC 01:00 = 한국시간 10:00
- UTC 03:00 = 한국시간 12:00
- UTC 05:00 = 한국시간 14:00
- UTC 07:00 = 한국시간 16:00
- UTC 09:00 = 한국시간 18:00

### 7. Plan 선택
- **Free** 선택 (무료!)

---

## 🔐 4단계: 환경변수 설정

### 1. "Environment" 탭 클릭

### 2. 환경변수 추가

#### GEMINI_API_KEY
- Key: `GEMINI_API_KEY`
- Value: (본인의 Gemini API 키 입력)
- "Add Environment Variable" 클릭

#### TEAMS_WEBHOOK_URL
- Key: `TEAMS_WEBHOOK_URL`
- Value: (본인의 Teams Webhook URL 입력)
- "Add Environment Variable" 클릭

### 3. "Save Changes" 클릭

---

## ✅ 5단계: 배포 완료!

### 1. "Create Cron Job" 버튼 클릭

### 2. 초기 빌드 대기
- 첫 빌드는 2-3분 정도 소요
- Logs 탭에서 진행 상황 확인 가능

### 3. 성공 확인
```
✓ Build succeeded
✓ Dependencies installed
✓ Ready to run
```

---

## 🧪 6단계: 테스트 실행

### 수동으로 즉시 실행하기:

1. Render Dashboard → Cron Job 선택
2. 오른쪽 상단 "Trigger Run" 버튼 클릭
3. "Logs" 탭에서 실행 결과 확인

### 확인할 내용:
```
✓ 연합뉴스 인사/부고 스크래퍼 시작...
✓ 언론사 리스트 로드 완료
✓ 인사: X개 게시물 수집 완료
✓ 부고: X개 게시물 수집 완료
✓ MS Teams 메시지 전송 완료
```

### MS Teams에서 알림 확인
- 정상 작동하면 Teams에 카드 형식의 알림이 옵니다!

---

## 📊 7단계: 모니터링

### Render Dashboard에서 확인 가능:

1. **Recent Runs**: 최근 실행 기록
2. **Logs**: 각 실행의 상세 로그
3. **Metrics**: 성공/실패 통계
4. **Next Run**: 다음 예정 실행 시간

### 로그 보는 법:
- Dashboard → Cron Job 선택 → "Logs" 탭
- 각 실행별로 펼쳐서 상세 로그 확인

---

## 🔧 트러블슈팅

### ❌ Build Failed

**원인**: 의존성 설치 실패

**해결**:
```bash
# 로컬에서 테스트
pip install -r requirements.txt
python scraper.py
```

로컬에서 정상 작동하면:
```bash
git add .
git commit -m "fix: requirements.txt 수정"
git push
```

---

### ❌ 환경변수 오류

**증상**: `GEMINI_API_KEY` 또는 `TEAMS_WEBHOOK_URL`이 없다는 에러

**해결**:
1. Render Dashboard → Cron Job → "Environment" 탭
2. 환경변수가 제대로 입력되었는지 확인
3. 값에 공백이나 특수문자가 잘못 들어갔는지 확인
4. "Save Changes" 클릭
5. "Manual Deploy" → "Redeploy" 클릭

---

### ❌ 언론사 리스트 로드 실패

**증상**: `언론사 리스트 파일을 찾을 수 없습니다`

**해결**:
```bash
# 파일이 GitHub에 있는지 확인
git status
git add media_list_cleaned.txt media_list.txt
git commit -m "fix: 언론사 리스트 파일 추가"
git push
```

---

### ❌ 스케줄이 실행되지 않음

**원인**: Render 무료 티어는 비활성화될 수 있음

**해결**:
1. Render Dashboard에서 Cron Job이 "Active" 상태인지 확인
2. 무료 플랜은 90일간 활동이 없으면 자동 정지될 수 있음
3. "Trigger Run"으로 수동 실행하면 다시 활성화됨

---

### ❌ Teams 알림이 오지 않음

**증상**: 스크립트는 성공했지만 Teams에 알림 없음

**해결**:
1. Webhook URL이 올바른지 확인
2. Webhook이 만료되지 않았는지 확인 (Teams에서 재생성 가능)
3. 로그에서 "✓ MS Teams 메시지 전송 완료" 메시지 확인

---

## 🎉 완료!

이제 설정한 시간마다 자동으로:
1. ✅ 연합뉴스에서 인사/부고 스크래핑
2. ✅ Gemini AI로 언론사 필터링
3. ✅ 중복 제거
4. ✅ MS Teams로 알림 전송

**Render의 장점**:
- ⏰ 정확한 스케줄링 (GitHub Actions보다 훨씬 안정적)
- 📊 실시간 로그 및 모니터링
- 🔄 자동 재배포 (GitHub push 시)
- 💰 완전 무료!

---

## 🔄 코드 업데이트하는 방법

### 1. 로컬에서 코드 수정
```bash
# 예: scraper.py 수정
code scraper.py
```

### 2. 변경사항 커밋 및 푸시
```bash
git add .
git commit -m "feat: 새로운 기능 추가"
git push
```

### 3. Render에서 자동 배포
- Render가 자동으로 감지하고 재배포합니다!
- 또는 수동: Dashboard → "Manual Deploy" → "Clear build cache & deploy"

---

## 📈 업그레이드 옵션 (필요시)

### 무료 플랜 제약:
- ✅ 스케줄 실행 무제한
- ✅ 빌드/실행 시간 무제한
- ⚠️ 90일간 활동 없으면 자동 일시정지

### 유료 플랜 ($7/month):
- ✅ 자동 일시정지 없음
- ✅ 우선순위 빌드
- ✅ 더 많은 리소스

**현재 무료 플랜으로 충분합니다!**

---

## 📞 도움이 필요하면?

1. Render Dashboard에서 로그 확인
2. 로컬에서 `python scraper.py` 실행해보기
3. GitHub Issues에 질문 남기기

---

## 🎯 다음 단계

배포가 완료되면:
1. ⏰ 다음 예정 실행 시간 확인
2. 📱 Teams에서 첫 알림 대기
3. 📊 Render Dashboard에서 실행 기록 모니터링

**수고하셨습니다! 🎉**
