# Lambda Python 3.13 base image (arm64)
FROM --platform=arm64 public.ecr.aws/lambda/python:3.13

# 레이어/빌드 산출물을 모을 디렉토리
WORKDIR /opt/python

# pip 최신화
RUN pip install --upgrade pip

# psycopg3 (binary build) + dotenv 설치를 /opt/python 에 바로 깐다
# 이 디렉토리 구조(/opt/python)는 Lambda Layer 규약과 호환된다.
RUN pip install "psycopg[binary]" python-dotenv -t /opt/python

# 디버그용 버전 출력 (빌드 시점에 실패 여부 확인)
RUN python -c "import psycopg, sys; print('✅ psycopg version:', psycopg.__version__, 'python:', sys.version)"

# 컨테이너가 뜬 다음, /opt/python 내용을 docker cp 해서 호스트로 가져와서
# zip으로 만들면 곧바로 Lambda Layer 또는 함수 배포 ZIP으로 쓸 수 있음.
#
# 예)
# docker build -t lambda-psycopg3-arm64 .
# docker create --name extract lambda-psycopg3-arm64
# docker cp extract:/opt/python ./python
# zip -r psycopg-layer.zip python
# -> 이 zip을 Lambda Layer로 업로드 (Runtime: Python 3.13, Arch: arm64)
#
# 또는 함수 ZIP으로 쓰고 싶으면:
# 1) ./python 안의 내용물을 ./package 로 복사
# 2) lambda_function.py를 ./package 에 같이 넣고
# 3) zip -r deploy.zip package/*  (zip 루트에 파일들이 바로 있도록)
#
# ※ .env.local은 절대 zip에 넣지 말 것