#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""인코딩 테스트"""
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']

for encoding in encodings:
    try:
        with open('media_list.txt', 'r', encoding=encoding) as f:
            lines = [l.strip() for l in f if l.strip()]
            unique_lines = list(set(lines))
            
            print(f"\n{encoding} 인코딩:")
            print(f"  - 전체 줄: {len(lines)}개")
            print(f"  - 고유 줄: {len(unique_lines)}개")
            print(f"  - 코리아타임스: {'있음' if '코리아타임스' in unique_lines else '없음'}")
            print(f"  - KBS: {'있음' if 'KBS' in unique_lines else '없음'}")
            print(f"  - 샘플 (116-119): {lines[116:119]}")
            
    except Exception as e:
        print(f"\n{encoding}: 실패 - {e}")
