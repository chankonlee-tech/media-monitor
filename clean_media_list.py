#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
미디어리스트 정제 스크립트
잘못된 항목을 필터링하고 정규화합니다.
"""

import re
import os
import sys
import io

# Windows 콘솔 한글 출력 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def is_valid_media_name(name):
    """
    유효한 언론사명인지 검증
    
    Args:
        name (str): 검증할 이름
    
    Returns:
        bool: 유효하면 True
    """
    # 빈 문자열 제외
    if not name or len(name.strip()) == 0:
        return False
    
    # HTML 엔티티 포함 제외
    if '&#' in name or '&lt;' in name or '&gt;' in name:
        return False
    
    # 숫자로 시작하는 것 제외 (예: 032LIFE, 0211필라테스)
    if re.match(r'^\d', name):
        return False
    
    # 특수문자가 너무 많은 것 제외
    special_chars = sum(1 for c in name if not c.isalnum() and not c.isspace() and c not in '()[]{}')
    if special_chars > 2:
        return False
    
    # 영어로만 된 짧은 단어 제외 (3글자 이하)
    if len(name) <= 3 and name.isascii():
        return False
    
    # 쉼표가 포함된 경우 제외 (잘못된 데이터)
    if ',' in name:
        return False
    
    return True


def clean_media_list(input_file='media_list.txt', output_file='media_list_cleaned.txt'):
    """
    미디어리스트를 정제하여 새 파일로 저장
    
    Args:
        input_file (str): 원본 파일 경로
        output_file (str): 정제된 파일 저장 경로
    """
    try:
        # 파일 읽기
        encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
        content = None
        
        for encoding in encodings:
            try:
                with open(input_file, 'r', encoding=encoding) as f:
                    content = f.read()
                    break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if content is None:
            print(f"오류: 파일을 읽을 수 없습니다: {input_file}")
            return
        
        # 줄 단위로 분리
        lines = content.split('\n')
        print(f"원본 라인 수: {len(lines)}")
        
        # 정제 및 중복 제거
        valid_media = set()
        invalid_count = 0
        
        for line in lines:
            media_name = line.strip()
            
            if media_name:
                if is_valid_media_name(media_name):
                    valid_media.add(media_name)
                else:
                    invalid_count += 1
                    print(f"제외: {media_name}")
        
        # 정렬
        sorted_media = sorted(valid_media)
        
        print(f"\n정제 결과:")
        print(f"  유효한 항목: {len(sorted_media)}개")
        print(f"  제외된 항목: {invalid_count}개")
        print(f"  중복 제거: {len(lines) - len(valid_media) - invalid_count}개")
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            for media in sorted_media:
                f.write(media + '\n')
        
        print(f"\n✓ 정제된 파일 저장 완료: {output_file}")
        
        # 샘플 출력
        print(f"\n정제된 리스트 샘플 (처음 20개):")
        for idx, media in enumerate(sorted_media[:20], 1):
            print(f"  {idx}. {media}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    clean_media_list()
