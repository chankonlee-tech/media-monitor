#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
필터링 정확도 분석 테스트
수집된 데이터를 언론사 리스트와 비교하여 매칭 정확도 확인
"""

import sys
import io

# Windows 콘솔 한글 출력 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scraper import load_media_list

# 스크래핑된 샘플 데이터 (실제 결과에서 가져옴)
sample_personnel = [
    "[인사] 뉴스인사이드",
    "[인사] 동의대학교",
    "[인사] 코리아리포트",
    "[인사] 아주경제",
    "[인사] 보험연구원",
    "[인사] 코리아타임스",
    "[인사] 부산대학교",
    "[인사] 현대경제신문",
    "[인사] 윈드리버",
    "[인사] 신영증권",
    "[인사] 중앙이코노미뉴스",
    "[인사] 중소벤처기업부",
    "[인사] 고용노동부",
    "[인사] 전남도",
    "[인사] 한경매거진앤북",
    "[인사] 한국경제신문",
    "[인사] 기획예산처",
    "[인사] 행정안전부",
    "[인사] 질병관리청",
    "[인사] KBS",
]

sample_obituary = [
    "[부고] 김경태(남도일보 중서부권취재본부장)씨 부친상",
    "[부고] 최승진(CBS 마케팅본부장)씨 모친상",
    "[부고] 김소양(서울시 미디어콘텐츠 특보)씨 시부상(종합)",
    "[부고] 최경철(매일신문 편집국장)씨 장인상",
    "[부고] 김진호(폴리뉴스 부사장)씨 부친상",
]

def test_filtering_accuracy():
    """필터링 정확도 테스트"""
    print("=" * 70)
    print("필터링 정확도 분석")
    print("=" * 70)
    
    # 언론사 리스트 로드
    media_list = load_media_list('media_list.txt')
    media_set = set(media_list)
    
    print(f"\n관리 언론사 수: {len(media_set)}개")
    
    # 인사 데이터 분석
    print("\n" + "=" * 70)
    print("📰 인사 데이터 분석")
    print("=" * 70)
    
    personnel_matched = []
    personnel_not_matched = []
    
    for title in sample_personnel:
        matched = False
        matched_media = None
        
        # 언론사 리스트에서 제목에 포함된 것 찾기
        for media in media_set:
            if media in title:
                matched = True
                matched_media = media
                break
        
        if matched:
            personnel_matched.append((title, matched_media))
        else:
            personnel_not_matched.append(title)
    
    print(f"\n✓ 매칭된 항목: {len(personnel_matched)}개")
    for title, media in personnel_matched:
        print(f"  • {title}")
        print(f"    → 매칭: {media}")
    
    print(f"\n✗ 매칭 안 된 항목: {len(personnel_not_matched)}개")
    for title in personnel_not_matched:
        print(f"  • {title}")
    
    # 부고 데이터 분석
    print("\n" + "=" * 70)
    print("🖤 부고 데이터 분석")
    print("=" * 70)
    
    obituary_matched = []
    obituary_not_matched = []
    
    for title in sample_obituary:
        matched = False
        matched_media = None
        
        for media in media_set:
            if media in title:
                matched = True
                matched_media = media
                break
        
        if matched:
            obituary_matched.append((title, matched_media))
        else:
            obituary_not_matched.append(title)
    
    print(f"\n✓ 매칭된 항목: {len(obituary_matched)}개")
    for title, media in obituary_matched:
        print(f"  • {title}")
        print(f"    → 매칭: {media}")
    
    print(f"\n✗ 매칭 안 된 항목: {len(obituary_not_matched)}개")
    for title in obituary_not_matched:
        print(f"  • {title}")
    
    # 통계
    print("\n" + "=" * 70)
    print("📊 통계")
    print("=" * 70)
    
    total_items = len(sample_personnel) + len(sample_obituary)
    total_matched = len(personnel_matched) + len(obituary_matched)
    total_not_matched = len(personnel_not_matched) + len(obituary_not_matched)
    
    match_rate = (total_matched / total_items * 100) if total_items > 0 else 0
    
    print(f"\n전체 항목: {total_items}개")
    print(f"  ✓ 언론사 매칭: {total_matched}개 ({match_rate:.1f}%)")
    print(f"  ✗ 매칭 실패: {total_not_matched}개 ({100-match_rate:.1f}%)")
    
    # 매칭 실패 항목 분석
    print(f"\n매칭 실패 원인 분석:")
    print(f"  • 일반 기업/기관: {len([x for x in personnel_not_matched if any(word in x for word in ['대학교', '증권', '연구원', '기업부', '노동부', '청', '처'])])}개")
    print(f"  • 리스트에 없는 언론사: {len([x for x in personnel_not_matched if '뉴스' in x or '리포트' in x or 'KBS' in x])}개")
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

if __name__ == '__main__':
    test_filtering_accuracy()
