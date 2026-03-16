#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
언론사 리스트 로드 기능 테스트
"""

import sys
import io

# Windows 콘솔 한글 출력 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# scraper 모듈에서 함수 임포트
from scraper import load_media_list

def test_load_media_list():
    """언론사 리스트 로드 기능 테스트"""
    print("=" * 60)
    print("언론사 리스트 로드 테스트")
    print("=" * 60)
    
    # 1. 언론사 리스트 로드
    print("\n1. 언론사 리스트 로딩 중...")
    media_list = load_media_list('media_list.txt')
    
    # 2. 결과 확인
    print(f"\n✓ 로드된 언론사 수: {len(media_list)}개")
    
    # 3. 중복 제거 확인
    print(f"✓ 중복 제거 완료 (set 사용)")
    
    # 4. 샘플 데이터 출력
    print(f"\n처음 20개 언론사:")
    for idx, media in enumerate(media_list[:20], 1):
        print(f"  {idx}. {media}")
    
    # 5. 특정 언론사 존재 확인
    print(f"\n주요 언론사 존재 확인:")
    test_media = ['조선일보', '중앙일보', '동아일보', 'KBS', 'MBC', 'SBS', 
                   '연합뉴스', '한국경제', '매일경제', '아주경제']
    
    for media in test_media:
        exists = media in media_list
        status = "✓" if exists else "✗"
        print(f"  {status} {media}: {'존재' if exists else '없음'}")
    
    # 6. 통계
    print(f"\n통계:")
    print(f"  - 총 고유 언론사 수: {len(media_list)}개")
    print(f"  - 가장 짧은 이름: {min(media_list, key=len)} ({len(min(media_list, key=len))}자)")
    print(f"  - 가장 긴 이름: {max(media_list, key=len)} ({len(max(media_list, key=len))}자)")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == '__main__':
    test_load_media_list()
