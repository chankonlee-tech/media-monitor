# n8n으로 미디어 모니터 자동화하기

## 📦 n8n 설치 방법

### Docker로 실행 (추천)
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

브라우저에서 `http://localhost:5678` 접속

### npm으로 설치
```bash
npm install n8n -g
n8n start
```

## 🔧 방법 1: Python 스크립트 직접 실행 (간단함)

### n8n 워크플로우 구성:

1. **Schedule Trigger 노드**
   - Mode: `Custom`
   - Cron Expression: `0 1,3,5,7,9 * * *` (UTC 기준)
   
2. **Execute Command 노드**
   - Command: `cd /path/to/media_monitor && python scraper.py`
   - Environment Variables:
     ```
     GEMINI_API_KEY=your_key_here
     TEAMS_WEBHOOK_URL=your_webhook_here
     ```

### 장점:
- 기존 Python 코드 그대로 사용
- 설정 간단

### 단점:
- n8n이 Python 환경 필요
- 의존성 관리 필요

---

## 🎨 방법 2: n8n으로 전체 로직 구현 (더 안정적)

### 워크플로우 설계:

```
[Schedule Trigger]
    ↓
[HTTP Request 1: 인사 페이지]
    ↓
[Code: HTML 파싱 + 날짜 필터링]
    ↓
[HTTP Request 2: 부고 페이지]
    ↓
[Code: HTML 파싱 + 날짜 필터링]
    ↓
[Code: 데이터 병합]
    ↓
[HTTP Request 3: Gemini API 필터링]
    ↓
[Code: 중복 체크 (이전 발송 내역)]
    ↓
[IF: 새 항목 있음?]
    ↓ Yes
[HTTP Request 4: Teams Webhook]
    ↓
[Code: 발송 내역 저장]
```

### 주요 노드별 설정:

#### 1️⃣ Schedule Trigger
```json
{
  "mode": "custom",
  "cronExpression": "0 1,3,5,7,9 * * *"
}
```

#### 2️⃣ HTTP Request (연합뉴스)
```json
{
  "method": "GET",
  "url": "https://www.yna.co.kr/people/personnel",
  "options": {
    "headers": {
      "User-Agent": "Mozilla/5.0"
    }
  }
}
```

#### 3️⃣ Code (HTML 파싱)
```javascript
// cheerio를 사용한 HTML 파싱
const cheerio = require('cheerio');
const $ = cheerio.load($input.item.json.body);

const results = [];
const today = new Date();
const todayMMDD = `${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

$('a[href*="/view/"]').each((i, elem) => {
  const href = $(elem).attr('href');
  const title = $(elem).text().trim();
  
  // 날짜 체크 로직
  if (href.includes(todayMMDD) || $(elem).parent().text().includes(todayMMDD)) {
    results.push({
      title: title,
      link: href.startsWith('http') ? href : 'https://www.yna.co.kr' + href
    });
  }
});

return results.map(item => ({ json: item }));
```

#### 4️⃣ HTTP Request (Gemini API)
```json
{
  "method": "POST",
  "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent",
  "authentication": "genericCredentialType",
  "genericAuthType": "queryAuth",
  "queryParameters": {
    "key": "={{$env.GEMINI_API_KEY}}"
  },
  "body": {
    "contents": [{
      "parts": [{
        "text": "필터링 프롬프트..."
      }]
    }]
  }
}
```

#### 5️⃣ Code (중복 체크)
```javascript
// n8n의 Static Data를 사용하여 이전 발송 내역 관리
const currentItems = $input.all();
const previousItems = $('Static Data').all() || [];

const previousLinks = new Set(previousItems.map(item => item.json.link));
const newItems = currentItems.filter(item => !previousLinks.has(item.json.link));

return newItems;
```

#### 6️⃣ HTTP Request (Teams Webhook)
```json
{
  "method": "POST",
  "url": "={{$env.TEAMS_WEBHOOK_URL}}",
  "body": {
    "type": "message",
    "attachments": [
      {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
          "type": "AdaptiveCard",
          "version": "1.5",
          "body": "={{$json.cardBody}}"
        }
      }
    ]
  }
}
```

---

## 🌐 방법 3: n8n Cloud (가장 편리)

### n8n Cloud 무료 티어:
- 월 5,000 워크플로우 실행
- 정확한 스케줄링
- 관리 불필요

### 가격:
- **무료**: 5,000 executions/month
- **Pro**: $20/month (20,000 executions)

### 사용법:
1. https://n8n.cloud 가입
2. 워크플로우 생성 (위 방법 1 또는 2)
3. 자동 실행

---

## 📊 비교표

| 방법 | 난이도 | 안정성 | 비용 | 추천도 |
|------|--------|--------|------|--------|
| n8n (self-hosted) | 중간 | ⭐⭐⭐⭐⭐ | 무료 | ⭐⭐⭐⭐ |
| n8n Cloud | 쉬움 | ⭐⭐⭐⭐⭐ | 무료/유료 | ⭐⭐⭐⭐⭐ |
| Railway | 쉬움 | ⭐⭐⭐⭐ | $5/month | ⭐⭐⭐⭐ |
| Render | 쉬움 | ⭐⭐⭐⭐⭐ | 무료 | ⭐⭐⭐⭐⭐ |
| AWS Lambda | 어려움 | ⭐⭐⭐⭐⭐ | 무료 한도 | ⭐⭐⭐ |

---

## 🎯 추천 시나리오

### 상황 1: 빠르게 해결하고 싶다
→ **Render Cron Jobs** (기존 코드 그대로 사용)

### 상황 2: n8n을 배우고 싶다
→ **n8n Cloud** 무료 티어로 시작

### 상황 3: 완전 무료로 운영하고 싶다
→ **n8n self-hosted** (Docker)

### 상황 4: 다른 자동화도 많이 할 예정
→ **n8n Cloud Pro** ($20/month)

---

## 📝 n8n 워크플로우 JSON 파일

필요하시면 즉시 사용 가능한 n8n 워크플로우 JSON 파일을 만들어드릴 수 있습니다.

어떤 방법을 원하시는지 말씀해주세요!
