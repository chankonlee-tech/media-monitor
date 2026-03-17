#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
연합뉴스 인사/부고 스크래퍼
오늘 날짜로 올라온 게시물의 제목과 링크를 수집합니다.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import sys
import io
import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Windows 콘솔 한글 출력 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def scrape_yna_page(url, section_type):
    """
    연합뉴스 페이지에서 오늘 날짜의 게시물 수집
    
    Args:
        url (str): 스크래핑할 페이지 URL
        section_type (str): 섹션 타입 ('personnel' 또는 'obituary')
    
    Returns:
        list: [{"title": "제목", "link": "링크"}] 형태의 리스트
    """
    try:
        # HTTP 요청
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 오늘 날짜 (한국 시간 KST = UTC+9)
        kst_now = datetime.utcnow() + timedelta(hours=9)
        today_mmdd = kst_now.strftime('%m-%d')  # 03-17
        today_yyyymmdd = kst_now.strftime('%Y%m%d')  # 20260317
        
        print(f"오늘 날짜 (한국 시간): {today_mmdd} (YYYYMMDD: {today_yyyymmdd})")
        
        # 섹션 이름 매핑
        section_map = {
            'personnel': 'people/personnel',
            'obituary': 'people/obituary-notice'
        }
        section_path = section_map.get(section_type, '')
        
        # 결과 리스트
        results = []
        
        # 모든 기사 링크 찾기
        article_links = soup.find_all('a', href=lambda x: x and '/view/' in x)
        
        for link in article_links:
            href = link.get('href', '')
            
            # 섹션 필터링: 해당 섹션의 게시물만 포함
            if section_path and f'section={section_path}' not in href:
                continue
            
            # 전체 URL 생성
            if href.startswith('http'):
                full_url = href
            else:
                full_url = 'https://www.yna.co.kr' + href
            
            # 제목 추출
            title = link.get_text(strip=True)
            
            if not title or len(title) < 5:  # 너무 짧은 제목은 제외
                continue
            
            # 방법 1: URL에서 날짜 추출 (AKR20260316... 형식)
            import re
            url_date_match = re.search(r'AKR(\d{8})', href)
            url_date_valid = False
            
            if url_date_match:
                url_date = url_date_match.group(1)
                if url_date == today_yyyymmdd:
                    url_date_valid = True
            
            # 방법 2: 텍스트에서 날짜 추출 (MM-DD HH:MM 형식)
            text_date_valid = False
            current = link
            for _ in range(5):  # 최대 5단계 상위까지 검색
                parent = current.parent
                if not parent:
                    break
                
                parent_text = parent.get_text()
                
                # 날짜 형식: MM-DD HH:MM (예: 03-16 14:26)
                date_pattern = rf'{today_mmdd}\s+\d{{2}}:\d{{2}}'
                if re.search(date_pattern, parent_text):
                    text_date_valid = True
                    break
                
                current = parent
            
            # URL의 날짜 또는 텍스트의 날짜가 오늘이면 추가
            if url_date_valid or text_date_valid:
                # 중복 제거 (같은 URL이 이미 있는지 확인)
                if not any(item['link'] == full_url for item in results):
                    results.append({
                        'title': title,
                        'link': full_url
                    })
        
        return results
        
    except requests.RequestException as e:
        print(f"네트워크 오류 발생: {e}")
        return []
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_article_content(article_url, max_retries=2):
    """
    연합뉴스 기사 URL에서 제목과 본문 내용 추출
    
    Args:
        article_url (str): 기사 URL
        max_retries (int): 최대 재시도 횟수 (기본값: 2)
    
    Returns:
        dict: {'title': '제목', 'content': '본문 내용'} 또는 None (실패 시)
    """
    import re
    import time
    
    for attempt in range(max_retries):
        try:
            # HTTP 요청
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 추출
            title = None
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # 본문 추출
            content = ""
            
            # article 태그 내의 p 태그들에서 본문 추출
            article_tag = soup.find('article')
            if article_tag:
                paragraphs = article_tag.find_all('p')
                content_parts = []
                
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    
                    # 저작권, 제보, 기자 정보 등 불필요한 텍스트 필터링
                    skip_patterns = [
                        r'저작권자.*연합뉴스',
                        r'무단 전재',
                        r'제보는 카카오톡',
                        r'^\(서울=연합뉴스\)$',
                        r'^\(.*=연합뉴스\)$',
                        r'^이미지 확대$',
                        r'^\d{4}/\d{2}/\d{2}$',  # 날짜 형식만 단독
                        r'^\d{4}년\d{2}월\d{2}일$',  # 한글 날짜만 단독
                        r'^송고$',
                        r'^구독구독중$',
                        r'^구독$',
                        r'^이전$',
                        r'^다음$',
                        r'^AI 학습 및 활용 금지$',
                        r'^\d{2}시\d{2}분\s*송고$'
                    ]
                    
                    should_skip = False
                    for pattern in skip_patterns:
                        if re.search(pattern, text):
                            should_skip = True
                            break
                    
                    # 짧은 텍스트도 포함 (인사 정보는 보통 짧음)
                    if not should_skip and text and len(text) > 5:
                        content_parts.append(text)
                
                content = ' '.join(content_parts)
            
            # 본문이 너무 짧으면 .story-news에서 재시도
            if len(content) < 50:
                story_elem = soup.find(class_='story-news')
                if story_elem:
                    # script, style 태그 제거
                    for tag in story_elem.find_all(['script', 'style', 'figure', 'div']):
                        tag.decompose()
                    
                    text = story_elem.get_text(separator=' ', strip=True)
                    
                    # 불필요한 텍스트 패턴 제거
                    text = re.sub(r'저작권자.*?연합뉴스.*?(금지|배포)', '', text)
                    text = re.sub(r'제보는 카카오톡.*?okjebo', '', text)
                    text = re.sub(r'<.*?AI 학습 및 활용 금지>', '', text)  # AI 학습 금지 문구
                    text = re.sub(r'AI 학습 및 활용 금지', '', text)  # AI 학습 금지 문구 (단독)
                    text = re.sub(r'\d{4}년\d{2}월\d{2}일\s+\d{2}시\d{2}분\s+송고', '', text)  # 한글 날짜 시간 송고
                    text = re.sub(r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}\s+송고', '', text)  # 영문 날짜 시간 송고
                    text = re.sub(r'\(.*?=연합뉴스\)', '', text)
                    text = re.sub(r'이미지 확대', '', text)
                    text = re.sub(r'기자구독구독중', '', text)
                    text = re.sub(r'이전다음', '', text)
                    text = re.sub(r'\s+', ' ', text)  # 여러 공백을 하나로
                    
                    content = text.strip()
            
            # 최소한의 데이터가 있으면 반환
            if title:
                # 본문이 없는 경우에만 fallback 메시지 사용
                if not content or len(content.strip()) == 0:
                    content = f"인사 발령 소식입니다. 자세한 내용은 기사를 확인해주세요."
                
                return {
                    'title': title,
                    'content': content[:1000] if len(content) > 1000 else content  # 최대 1000자로 제한
                }
            
            return None
            
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"  ⚠ 기사 본문 가져오기 실패 (재시도 {attempt + 1}/{max_retries - 1}): {e}")
                time.sleep(1)
                continue
            else:
                print(f"  ✗ 기사 본문 가져오기 최종 실패: {e}")
                return None
        except Exception as e:
            print(f"  ✗ 기사 본문 파싱 오류: {e}")
            return None
    
    return None


def normalize_media_name(name):
    """
    언론사명을 정규화하여 매칭률 향상
    
    Args:
        name (str): 원본 언론사명
    
    Returns:
        str: 정규화된 언론사명
    """
    import re
    
    # 괄호 및 괄호 안 내용 제거 (예: "세계일보(디지털미디어국)" → "세계일보")
    name = re.sub(r'\([^)]*\)', '', name)
    
    # 공백 제거
    name = name.strip()
    
    return name


def extract_core_media_names(media_list):
    """
    언론사 리스트에서 핵심 언론사명만 추출 (중복 제거 및 정규화)
    
    Args:
        media_list (list): 원본 언론사 리스트
    
    Returns:
        tuple: (정규화된 set, 원본 리스트)
    """
    normalized_set = set()
    
    for media in media_list:
        normalized = normalize_media_name(media)
        if normalized:
            normalized_set.add(normalized)
    
    return normalized_set, media_list


def load_media_list(filepath='media_list.txt'):
    """
    언론사 리스트를 파일에서 로드하고 중복 제거 및 정규화
    
    Args:
        filepath (str): 언론사 리스트 파일 경로
    
    Returns:
        tuple: (정규화된 언론사명 set, 원본 리스트)
    """
    try:
        # 현재 스크립트 디렉토리 기준으로 파일 경로 설정
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, filepath)
        
        media_set = set()
        
        # 여러 인코딩 시도
        encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
        content = None
        
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if content is None:
            print(f"경고: 파일 인코딩을 감지할 수 없습니다: {filepath}")
            return set(), []
        
        # 줄 단위로 분리하여 처리
        total_lines = 0
        for line in content.split('\n'):
            # 공백 제거 및 빈 줄 제외
            media_name = line.strip()
            if media_name:
                media_set.add(media_name)
                total_lines += 1
        
        # 원본 리스트 생성
        media_list = sorted(media_set)
        
        # 정규화된 버전 생성
        normalized_set, _ = extract_core_media_names(media_list)
        
        print(f"언론사 리스트 로드 완료: 중복 제거 후 {len(media_list)}개 (원본: {total_lines}줄)")
        print(f"정규화 후 핵심 언론사: {len(normalized_set)}개")
        
        return normalized_set, media_list
        
    except FileNotFoundError:
        print(f"경고: 언론사 리스트 파일을 찾을 수 없습니다: {filepath}")
        print("기본 필터링 모드로 전환합니다.")
        return set(), []
    except Exception as e:
        print(f"언론사 리스트 로드 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return set(), []


def create_media_variations(media_name):
    """
    언론사명의 다양한 변형을 생성 (매칭률 향상)
    
    Args:
        media_name (str): 원본 언론사명
    
    Returns:
        set: 다양한 변형들의 집합
    """
    import re
    
    variations = {media_name}
    
    # 괄호 제거 버전
    no_parens = re.sub(r'\([^)]*\)', '', media_name).strip()
    if no_parens:
        variations.add(no_parens)
    
    # 공백 제거 버전
    no_space = media_name.replace(' ', '')
    variations.add(no_space)
    
    # 특정 접미사 제거 버전
    suffixes = ['신문', '일보', '방송', 'TV', '뉴스', '경제', '타임즈', '저널']
    for suffix in suffixes:
        if media_name.endswith(suffix):
            base = media_name[:-len(suffix)]
            if base:
                variations.add(base)
    
    return variations


def filter_media_news(news_items, api_key, media_data=None):
    """
    Gemini API를 사용하여 언론사 관련 뉴스만 필터링 (정교화된 버전)
    
    Args:
        news_items (list): [{"title": "...", "link": "..."}] 형태의 리스트
        api_key (str): Gemini API 키
        media_data (tuple): (정규화된 언론사 set, 원본 리스트) 또는 None
    
    Returns:
        list: 언론사 관련 소식만 필터링된 리스트
    """
    if not news_items:
        return []
    
    if not api_key:
        print("경고: Gemini API 키가 없습니다. 필터링을 건너뜁니다.")
        return news_items
    
    try:
        # Gemini API 설정
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # 제목만 추출
        titles = [item['title'] for item in news_items]
        
        # media_data 처리
        if media_data and isinstance(media_data, tuple) and len(media_data) == 2:
            normalized_media_set, original_media_list = media_data
            has_media_list = len(normalized_media_set) > 0
        else:
            normalized_media_set = set()
            original_media_list = []
            has_media_list = False
        
        # 프롬프트 구성
        if has_media_list:
            # 핵심 언론사만 샘플링 (프롬프트 길이 제한)
            sample_size = min(200, len(normalized_media_set))
            media_sample = sorted(normalized_media_set)[:sample_size]
            media_list_str = ', '.join(media_sample)
            
            more_text = f" (총 {len(normalized_media_set)}개 중 대표 {sample_size}개)" if len(normalized_media_set) > sample_size else ""
            
            prompt = f"""당신은 언론계/미디어 업계 전문가입니다. 다음 인사/부고 뉴스 제목 중에서 언론사/방송사/미디어 관련 소식만 골라주세요.

**우리 회사가 관리하는 언론사 리스트**{more_text}:
{media_list_str}

**필터링 규칙:**
1. 위 리스트에 포함된 언론사의 인사/부고 소식만 선택하세요.
2. 제목에 언론사명이 명시적으로 언급되거나, 해당 언론사 소속임이 명확한 경우만 포함하세요.
3. 부분 매칭도 허용합니다:
   - "조선일보 논설위원" → 조선일보가 리스트에 있으면 ✓ 포함
   - "MBC 보도국장" → MBC가 리스트에 있으면 ✓ 포함
   - "머니투데이 스타뉴스 기자" → 머니투데이가 리스트에 있으면 ✓ 포함
   - "세계일보(디지털미디어국)" → 세계일보가 리스트에 있으면 ✓ 포함
4. 괄호나 접미사는 무시하고 핵심 언론사명이 일치하면 포함하세요.
5. 미디어 플랫폼/포털 기업의 미디어 관련 직책도 포함하세요:
   - "네이버 미디어 본부장", "카카오 콘텐츠 대표" 등 → ✓ 포함
   - 단, 일반 직책 (개발, 재무 등)은 제외
6. 리스트에 없는 언론사라도 명백한 미디어 조직 또는 미디어 업계 전문지면 포함할 수 있습니다:
   - 예: "트루스데일리", "화장품신문", "뷰티한국" 등
7. 일반 기업/기관 (금융, 제조업, IT 기업, 공공기관, 교육, 의료 등)은 제외하세요.

제목 리스트:
{json.dumps(titles, ensure_ascii=False, indent=2)}

위 기준에 따라 언론/미디어 관련 제목만 골라서 다음 JSON 형식으로 반환하세요:
{{"filtered_titles": ["필터링된 제목1", "필터링된 제목2", ...]}}

만약 해당하는 제목이 하나도 없다면:
{{"filtered_titles": []}}
"""
        else:
            # 기본 모드 (하드코딩된 예시 사용)
            prompt = f"""당신은 언론계/미디어 업계 전문가입니다. 다음 인사/부고 뉴스 제목 중에서 언론사/방송사/미디어 관련 소식만 골라주세요.

**포함해야 할 조직 (언론/미디어 관련):**
- 신문사: 조선일보, 중앙일보, 동아일보, 한국일보, 경향신문, 한겨레, 매일경제, 한국경제, 서울신문, 지역 일간지 등
- 방송사: KBS, MBC, SBS, JTBC, TV조선, MBN, 채널A, YTN, 연합뉴스TV 등
- 통신사: 연합뉴스, 뉴시스, 뉴스1 등
- 인터넷/뉴미디어: 네이버, 카카오, 다음, 온라인 신문사, 포털 미디어 등
- 출판/잡지: 출판사, 잡지사, 미디어 콘텐츠 제작사 등
- 광고/PR: 광고대행사, PR 에이전시 등
- 화장품/뷰티 전문 매체: 화장품신문, 코스인코리아, 뷰티한국 등

**제외해야 할 조직 (일반 기업/기관):**
- 금융: 은행, 증권사, 보험사, 카드사 등
- 제조업: 자동차, 전자, 화학, 식품, 제약 등 (미디어 제외)
- IT: 소프트웨어, 하드웨어, 통신 서비스 등 (미디어 플랫폼 제외)
- 공공기관: 정부 부처, 지자체, 공기업 등 (공영방송 제외)
- 교육: 대학, 학교, 학원 등
- 의료: 병원, 의료기관 등
- 서비스업: 유통, 외식, 호텔, 건설 등

**판단 기준:**
1. 제목에 명시적으로 언론사/방송사/미디어 회사명이 나오면 포함
2. "기자", "논설위원", "보도국장", "편집국장" 등 언론 직책이 나오면 포함 가능성 높음
3. 애매한 경우 제외하는 것이 안전합니다

**예시:**
- "[인사] MBC 보도국장 김철수" → **포함** (방송사)
- "[부고] 조선일보 논설위원" → **포함** (신문사)
- "[인사] 삼성전자 부사장" → **제외** (제조업)
- "[부고] 국민은행 지점장" → **제외** (금융)
- "[인사] 네이버 미디어 본부장" → **포함** (인터넷 미디어)
- "[부고] 화장품신문 대표이사" → **포함** (업계 전문지)

제목 리스트:
{json.dumps(titles, ensure_ascii=False, indent=2)}

위 기준에 따라 언론/미디어 관련 제목만 골라서 다음 JSON 형식으로 반환하세요:
{{"filtered_titles": ["필터링된 제목1", "필터링된 제목2", ...]}}

만약 해당하는 제목이 하나도 없다면:
{{"filtered_titles": []}}
"""
        
        # API 호출
        if has_media_list:
            print(f"\nGemini API 호출 중... (총 {len(titles)}개 제목, 관리 언론사: {len(normalized_media_set)}개)")
        else:
            print(f"\nGemini API 호출 중... (총 {len(titles)}개 제목, 기본 모드)")
        print("디버깅: 원본 제목 목록:")
        for idx, title in enumerate(titles, 1):
            print(f"  {idx}. {title}")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                response_mime_type="application/json"
            )
        )
        
        # 응답 파싱
        result_text = response.text
        print(f"\n디버깅: Gemini API 응답:\n{result_text}\n")
        
        result_json = json.loads(result_text)
        filtered_titles = result_json.get('filtered_titles', [])
        
        # 제목 정규화 (불필요한 따옴표 제거)
        normalized_filtered_titles = []
        for title in filtered_titles:
            # 앞뒤 따옴표 제거
            clean_title = title.strip('"').strip("'")
            normalized_filtered_titles.append(clean_title)
        
        filtered_titles = normalized_filtered_titles
        
        print(f"필터링 결과: {len(filtered_titles)}개 제목 선택됨")
        if filtered_titles:
            print("선택된 제목:")
            for idx, title in enumerate(filtered_titles, 1):
                print(f"  ✓ {idx}. {title}")
        else:
            print("  (언론사 관련 소식 없음)")
        
        # 필터링된 제목에 해당하는 원본 아이템 반환
        filtered_items = []
        for item in news_items:
            if item['title'] in filtered_titles:
                filtered_items.append(item)
        
        return filtered_items
        
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        print("필터링 없이 원본 데이터를 반환합니다.")
        return news_items


def send_to_teams(personnel_data, obituary_data, webhook_url):
    """
    MS Teams Incoming Webhook으로 Adaptive Cards v1.5 형식의 메시지 전송
    
    Args:
        personnel_data (list): 인사 소식 리스트 [{"title": "...", "link": "...", "content": "..."}, ...]
        obituary_data (list): 부고 소식 리스트 [{"title": "...", "link": "...", "content": "..."}, ...]
        webhook_url (str): MS Teams Incoming Webhook URL
    
    Returns:
        bool: 전송 성공 여부
    """
    
    try:
        # 현재 시간 (한국 시간 KST = UTC+9)
        now = datetime.utcnow() + timedelta(hours=9)
        current_time = now.strftime('%Y년 %m월 %d일 %H:%M')
        
        # Adaptive Card body 구성
        card_body = []
        
        # 헤더 섹션
        card_body.append({
            "type": "TextBlock",
            "text": "📰 언론계 인사/부고 소식",
            "size": "ExtraLarge",
            "weight": "Bolder",
            "color": "Accent"
        })
        
        card_body.append({
            "type": "TextBlock",
            "text": current_time,
            "size": "Small",
            "color": "Default",
            "spacing": "None"
        })
        
        # 구분선
        card_body.append({
            "type": "Container",
            "spacing": "Medium",
            "separator": True,
            "items": []
        })
        
        # 빈 데이터인 경우 안내 메시지 표시
        if not personnel_data and not obituary_data:
            card_body.append({
                "type": "TextBlock",
                "text": "현재까지 추가된 인사/부고가 없습니다",
                "size": "Medium",
                "weight": "Bolder",
                "color": "Attention",
                "spacing": "Medium",
                "wrap": True,
                "horizontalAlignment": "Center"
            })
            
            card_body.append({
                "type": "TextBlock",
                "text": "새로운 언론계 인사/부고 소식이 올라오면 알려드리겠습니다",
                "size": "Small",
                "color": "Default",
                "spacing": "Small",
                "wrap": True,
                "horizontalAlignment": "Center"
            })
            
            # 메시지 전송 (빈 데이터)
            adaptive_card = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.5",
                            "body": card_body,
                            "msteams": {
                                "width": "Full"
                            }
                        }
                    }
                ]
            }
            
            response = requests.post(
                webhook_url,
                headers={"Content-Type": "application/json"},
                json=adaptive_card,
                timeout=10
            )
            
            response.raise_for_status()
            print(f"✓ MS Teams 메시지 전송 완료 (새 소식 없음)")
            return True
        
        # 인사 섹션
        if personnel_data:
            card_body.append({
                "type": "TextBlock",
                "text": "📰 인사",
                "size": "Large",
                "weight": "Bolder",
                "color": "Good",
                "spacing": "Medium"
            })
            
            for idx, item in enumerate(personnel_data, 1):
                # 각 기사를 Container로 감싸기
                article_container = {
                    "type": "Container",
                    "spacing": "Medium",
                    "separator": idx > 1,
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": item.get('title', '제목 없음'),
                            "size": "Medium",
                            "weight": "Bolder",
                            "wrap": True,
                            "color": "Accent"
                        }
                    ]
                }
                
                # 본문 내용 추가
                content = item.get('content', '')
                if content and len(content) > 10:
                    article_container["items"].append({
                        "type": "TextBlock",
                        "text": content,
                        "size": "Default",
                        "wrap": True,
                        "spacing": "Small",
                        "color": "Default"
                    })
                
                # 기사 전체보기 버튼
                article_container["items"].append({
                    "type": "ActionSet",
                    "spacing": "Small",
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "기사 전체보기",
                            "url": item.get('link', ''),
                            "style": "positive"
                        }
                    ]
                })
                
                card_body.append(article_container)
        
        # 부고 섹션
        if obituary_data:
            # 인사와 부고 사이 구분선
            if personnel_data:
                card_body.append({
                    "type": "Container",
                    "spacing": "Large",
                    "separator": True,
                    "items": []
                })
            
            card_body.append({
                "type": "TextBlock",
                "text": "🖤 부고",
                "size": "Large",
                "weight": "Bolder",
                "color": "Warning",
                "spacing": "Medium"
            })
            
            for idx, item in enumerate(obituary_data, 1):
                # 각 기사를 Container로 감싸기
                article_container = {
                    "type": "Container",
                    "spacing": "Medium",
                    "separator": idx > 1,
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": item.get('title', '제목 없음'),
                            "size": "Medium",
                            "weight": "Bolder",
                            "wrap": True,
                            "color": "Default"
                        }
                    ]
                }
                
                # 본문 내용 추가
                content = item.get('content', '')
                if content and len(content) > 10:
                    article_container["items"].append({
                        "type": "TextBlock",
                        "text": content,
                        "size": "Default",
                        "wrap": True,
                        "spacing": "Small",
                        "color": "Default"
                    })
                
                # 기사 전체보기 버튼
                article_container["items"].append({
                    "type": "ActionSet",
                    "spacing": "Small",
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "기사 전체보기",
                            "url": item.get('link', ''),
                            "style": "default"
                        }
                    ]
                })
                
                card_body.append(article_container)
        
        # Adaptive Card 완성
        adaptive_card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.5",
                        "body": card_body,
                        "msteams": {
                            "width": "Full"
                        }
                    }
                }
            ]
        }
        
        # HTTP POST 요청
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=adaptive_card,
            timeout=10
        )
        
        response.raise_for_status()
        print(f"✓ MS Teams 메시지 전송 완료 (인사: {len(personnel_data)}개, 부고: {len(obituary_data)}개)")
        return True
        
    except requests.RequestException as e:
        print(f"✗ Teams 메시지 전송 실패 (네트워크 오류): {e}")
        return False
    except Exception as e:
        print(f"✗ Teams 메시지 전송 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_previous_sent_items(filepath='sent_items.json'):
    """
    이전에 발송한 항목들을 로드
    
    Args:
        filepath (str): 발송 내역 JSON 파일 경로
    
    Returns:
        dict: {'personnel': [...], 'obituary': [...]} 형태의 이전 발송 내역
    """
    if not os.path.exists(filepath):
        print(f"이전 발송 내역 파일이 없습니다: {filepath}")
        return {'personnel': [], 'obituary': []}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            personnel_count = len(data.get('personnel', []))
            obituary_count = len(data.get('obituary', []))
            timestamp = data.get('timestamp', 'N/A')
            print(f"✓ 이전 발송 내역 로드 완료: 인사 {personnel_count}개, 부고 {obituary_count}개 (마지막 발송: {timestamp})")
            return data
    except Exception as e:
        print(f"이전 발송 내역 로드 실패: {e}")
        return {'personnel': [], 'obituary': []}


def save_sent_items(personnel_data, obituary_data, filepath='sent_items.json'):
    """
    발송한 항목들을 저장
    
    Args:
        personnel_data (list): 발송한 인사 소식 리스트
        obituary_data (list): 발송한 부고 소식 리스트
        filepath (str): 저장할 JSON 파일 경로
    """
    try:
        # 한국 시간(KST) 기준으로 타임스탬프 저장
        kst_now = datetime.utcnow() + timedelta(hours=9)
        sent_items = {
            'personnel': [{'title': item['title'], 'link': item['link']} for item in personnel_data],
            'obituary': [{'title': item['title'], 'link': item['link']} for item in obituary_data],
            'timestamp': kst_now.isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sent_items, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 발송 내역 저장 완료: {filepath}")
    except Exception as e:
        print(f"발송 내역 저장 실패: {e}")
        import traceback
        traceback.print_exc()


def filter_duplicates(current_items, previous_items):
    """
    이전에 발송한 항목 제외
    
    Args:
        current_items (list): 현재 수집된 항목 리스트
        previous_items (list): 이전에 발송한 항목 리스트
    
    Returns:
        list: 중복이 제거된 새로운 항목만 포함한 리스트
    """
    previous_links = {item['link'] for item in previous_items}
    new_items = [item for item in current_items if item['link'] not in previous_links]
    
    filtered_count = len(current_items) - len(new_items)
    if filtered_count > 0:
        print(f"  → 중복 제거: {filtered_count}개 항목 (이미 발송됨)")
    
    return new_items


def main():
    """
    메인 함수: 인사와 부고 페이지를 스크래핑하고 결과를 JSON으로 반환
    """
    print("연합뉴스 인사/부고 스크래퍼 시작...\n")
    
    # URL 정의
    personnel_url = 'https://www.yna.co.kr/people/personnel'
    obituary_url = 'https://www.yna.co.kr/people/obituary-notice'
    
    # 스크래핑 실행
    print(f"인사 페이지 스크래핑 중... ({personnel_url})")
    personnel_data = scrape_yna_page(personnel_url, 'personnel')
    print(f"인사: {len(personnel_data)}개 게시물 수집 완료\n")
    
    print(f"부고 페이지 스크래핑 중... ({obituary_url})")
    obituary_data = scrape_yna_page(obituary_url, 'obituary')
    print(f"부고: {len(obituary_data)}개 게시물 수집 완료\n")
    
    # 원본 데이터 개수
    original_personnel_count = len(personnel_data)
    original_obituary_count = len(obituary_data)
    
    # Gemini API로 필터링
    api_key = os.getenv('GEMINI_API_KEY')
    
    if api_key:
        print("=" * 60)
        print("언론사 관련 소식 필터링 중...")
        print("=" * 60)
        
        # 언론사 리스트 로드 (정제된 버전 우선 사용)
        print("\n언론사 리스트 로딩 중...")
        
        # 정제된 버전이 있으면 우선 사용
        media_list_files = ['media_list_cleaned.txt', 'media_list.txt']
        media_data = None
        
        for filename in media_list_files:
            if os.path.exists(filename):
                print(f"시도: {filename}")
                media_data = load_media_list(filename)
                if isinstance(media_data, tuple) and len(media_data) == 2:
                    normalized_media_set, original_media_list = media_data
                    if len(normalized_media_set) > 0:
                        print(f"✓ 언론사 리스트 로드 완료 ({filename}):")
                        print(f"  - 중복 제거 후: {len(original_media_list)}개")
                        print(f"  - 정규화 후: {len(normalized_media_set)}개")
                        print(f"  예시: {', '.join(sorted(normalized_media_set)[:5])}...")
                        break
        
        if media_data is None or (isinstance(media_data, tuple) and len(media_data[0]) == 0):
            print("⚠ 언론사 리스트를 로드하지 못했습니다. 기본 모드로 진행합니다.")
            media_data = None
        
        print()
        
        # 인사와 부고를 합쳐서 한 번에 필터링 (API 호출 최소화)
        all_items = personnel_data + obituary_data
        filtered_items = filter_media_news(all_items, api_key, media_data)
        
        # 필터링된 결과를 다시 인사/부고로 분리
        personnel_links = {item['link'] for item in personnel_data}
        filtered_personnel = [item for item in filtered_items if item['link'] in personnel_links]
        filtered_obituary = [item for item in filtered_items if item['link'] not in personnel_links]
        
        personnel_data = filtered_personnel
        obituary_data = filtered_obituary
        
        print("\n" + "=" * 60)
        print("필터링 결과:")
        print("=" * 60)
        print(f"원본 수집: 인사 {original_personnel_count}개, 부고 {original_obituary_count}개")
        print(f"필터링 후: 인사 {len(personnel_data)}개, 부고 {len(obituary_data)}개")
        print("=" * 60)
    else:
        print("\n경고: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("필터링 없이 전체 결과를 반환합니다.\n")
    
    # 중복 제거 로직 (이전 발송 내역과 비교)
    print("\n" + "=" * 60)
    print("중복 발송 방지 체크 중...")
    print("=" * 60)
    
    previous_sent = load_previous_sent_items('sent_items.json')
    
    # 필터링 전 개수 저장
    before_dedup_personnel = len(personnel_data)
    before_dedup_obituary = len(obituary_data)
    
    # 중복 제거
    personnel_data = filter_duplicates(personnel_data, previous_sent.get('personnel', []))
    obituary_data = filter_duplicates(obituary_data, previous_sent.get('obituary', []))
    
    print(f"\n중복 제거 결과:")
    print(f"  인사: {before_dedup_personnel}개 → {len(personnel_data)}개 (새로운 항목)")
    print(f"  부고: {before_dedup_obituary}개 → {len(obituary_data)}개 (새로운 항목)")
    print("=" * 60)
    
    # 기사 본문 스크래핑 (새로운 항목만 대상)
    if personnel_data or obituary_data:
        print("\n" + "=" * 60)
        print("기사 본문 스크래핑 중...")
        print("=" * 60)
        
        # 인사 기사 본문 가져오기
        if personnel_data:
            print(f"\n인사 기사 본문 수집 중... (총 {len(personnel_data)}개)")
            for idx, item in enumerate(personnel_data, 1):
                print(f"  [{idx}/{len(personnel_data)}] {item['title'][:50]}...")
                article_content = fetch_article_content(item['link'])
                if article_content:
                    item['content'] = article_content['content']
                    item['full_title'] = article_content['title']
                    print(f"    ✓ 본문 수집 완료 ({len(article_content['content'])}자)")
                else:
                    item['content'] = f"{item['title']} (본문 정보를 가져올 수 없습니다)"
                    item['full_title'] = item['title']
                    print(f"    ⚠ 본문 수집 실패 - 기본 메시지 사용")
        
        # 부고 기사 본문 가져오기
        if obituary_data:
            print(f"\n부고 기사 본문 수집 중... (총 {len(obituary_data)}개)")
            for idx, item in enumerate(obituary_data, 1):
                print(f"  [{idx}/{len(obituary_data)}] {item['title'][:50]}...")
                article_content = fetch_article_content(item['link'])
                if article_content:
                    item['content'] = article_content['content']
                    item['full_title'] = article_content['title']
                    print(f"    ✓ 본문 수집 완료 ({len(article_content['content'])}자)")
                else:
                    item['content'] = f"{item['title']} (본문 정보를 가져올 수 없습니다)"
                    item['full_title'] = item['title']
                    print(f"    ⚠ 본문 수집 실패 - 기본 메시지 사용")
        
        print("\n✓ 기사 본문 스크래핑 완료")
        print("=" * 60)
    
    # 결과 구성
    result = {
        'personnel': personnel_data,
        'obituary': obituary_data
    }
    
    # MS Teams로 메시지 전송
    webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    if webhook_url:
        # 항상 메시지 전송 (새 항목이 없어도 알림)
        print("\n" + "=" * 60)
        print("MS Teams 메시지 전송 중...")
        print("=" * 60)
        success = send_to_teams(personnel_data, obituary_data, webhook_url)
        
        # 메시지 전송 성공 시 발송 내역 저장 (새 항목이 있는 경우만)
        if success and (personnel_data or obituary_data):
            print("\n발송 내역 저장 중...")
            save_sent_items(personnel_data, obituary_data, 'sent_items.json')
    else:
        print("\n경고: TEAMS_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        print("Teams 메시지 전송을 건너뜁니다.\n")
    
    # JSON 형태로 출력
    print("\n" + "=" * 60)
    print("수집 결과:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == '__main__':
    main()
