FROM n8nio/n8n:latest

USER root

# Python 및 필수 패키지 설치
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    gcc \
    musl-dev

# Python 패키지 설치를 위한 디렉토리 생성
WORKDIR /workspace

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# 프로젝트 파일들 복사
COPY scraper.py ./
COPY media_list_cleaned.txt ./
COPY media_list.txt ./

# 권한 설정
RUN chown -R node:node /workspace

USER node

# n8n 기본 작업 디렉토리로 돌아가기
WORKDIR /home/node/.n8n
