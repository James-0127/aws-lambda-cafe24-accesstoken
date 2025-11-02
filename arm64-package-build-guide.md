# 한국어 - ARM64 패키지 빌드 가이드
AWS Lambda의 ARM64 (Graviton) 런타임 환경에서 psycopg3 또는 C 확장 의존성이 있는 패키지를 빌드할 때는 일반 x86 환경과 달리 네이티브 빌드가 불가능할 수 있습니다. 따라서, Lambda의 실제 런타임과 동일한 환경(manylinux2014_aarch64)에서 Docker 기반으로 패키지를 빌드해야 합니다.

## 목차
- [Dockerfile 예시](#dockerfile-예시)
- [Docker 이미지 빌드](#docker-이미지-빌드)
- [컨테이너 실행](#컨테이너-실행)
- [Lambda Layer 또는 패키지 생성](#lambda-layer-또는-패키지-생성)
	- [Layer 형태 (추천)](#layer-형태-추천)
	- [배포 zip 형태 (단일 함수)](#배포-zip-형태-단일-함수)
- [배포 후 확인](#배포-후-확인)
- [주의사항](#주의사항)


## Dockerfile 예시
```bash
FROM --platform=arm64 public.ecr.aws/lambda/python:3.13

RUN dnf -y update && dnf -y install postgresql15-devel gcc python3-devel && dnf clean all
WORKDIR /opt/python

RUN pip install --no-cache-dir psycopg[binary] python-dotenv
```

## Docker 이미지 빌드
```bash
docker build -t lambda-psycopg3-arm64 .
```

## 컨테이너 실행
```bash
docker run -it --name psycopg3-layer lambda-psycopg3-arm64 /bin/bash
```

컨테이너 내부의 /opt/python 디렉터리에 빌드된 패키지들이 포함됩니다.
```
/opt/python/
 ├── psycopg/
 ├── psycopg_binary/
 ├── psycopg_binary.libs/
 ├── python_dotenv-1.x.dist-info/
 └── ...
```

## Lambda Layer 또는 패키지 생성

### Layer 형태 (추천)
```bash
docker cp psycopg3-layer:/opt/python ./python
zip -r psycopg3-layer.zip python
```
Lambda 콘솔 또는 AWS CLI를 통해 layer를 업로드 후, 각 함수에서 layer ARN을 참조합니다.

### 배포 zip 형태 (단일 함수)
```
docker cp psycopg3-layer:/opt/python ./package
cp lambda_function.py ./package/
cd package
zip -r ../deploy.zip .
cd ..
```

## 배포 후 확인
	•	Lambda Runtime: Python 3.13 (arm64)
	•	zip 또는 layer 구조:
```
psycopg/
psycopg_binary/
psycopg_binary.libs/
lambda_function.py
```

	•	배포 후 CloudWatch 로그에서 Unable to import psycopg 오류가 사라져야 정상 동작.

## 주의사항
	•	macOS ARM 환경(Apple Silicon)에서 로컬 빌드 시, 아키텍처가 호스트와 달라 패키지 호환성이 깨질 수 있습니다. Docker의 --platform=arm64 옵션을 반드시 지정하세요.
	•	Lambda의 기본 빌드 타겟은 manylinux2014_aarch64입니다.
	•	psycopg[binary]를 설치할 때 --only-binary=:all: 옵션은 Lambda 환경에 맞춘 안정적 빌드를 보장합니다.




# ARM64 Package Build Guide (English)

When deploying AWS Lambda functions using the ARM64 (Graviton) runtime, libraries with native C extensions such as psycopg3 must be built in an environment matching the target runtime. This guide explains how to prepare ARM64-compatible packages using Docker.

## Table of contents
- [Example Dockerfile](#1-dockerfile-예시)
- [Build the Docker image](#build-the-docker-image)
- [Run the container](#run-the-container)
- [Create a Lambda Layer or Deployment Package](#create-a-lambda-layer-or-deployment-package)
	- [As a Lambda Layer (Recommended)](#as-a-lambda-layer-recommended)
	- [As a deployment package (single Lambda)](#as-a-deployment-package-single-lambda)
- [Verification](#verification)
- [Notes](#notes)

## Example Dockerfile
```bash
FROM --platform=arm64 public.ecr.aws/lambda/python:3.13

RUN dnf -y update && dnf -y install postgresql15-devel gcc python3-devel && dnf clean all
WORKDIR /opt/python

RUN pip install --no-cache-dir psycopg[binary] python-dotenv
```

## Build the Docker image
```bash
docker build -t lambda-psycopg3-arm64 .
```

## Run the container
```bash
docker run -it --name psycopg3-layer lambda-psycopg3-arm64 /bin/bash
```

Inside the container, the compiled packages are located in /opt/python:
```
/opt/python/
 ├── psycopg/
 ├── psycopg_binary/
 ├── psycopg_binary.libs/
 ├── python_dotenv-1.x.dist-info/
 └── ...
```

## Create a Lambda Layer or Deployment Package

### As a Lambda Layer (Recommended)
```bash
docker cp psycopg3-layer:/opt/python ./python
zip -r psycopg3-layer.zip python
```

Upload this zip as a Lambda Layer and attach the layer ARN to your functions.

### As a deployment package (single Lambda)
```
docker cp psycopg3-layer:/opt/python ./package
cp lambda_function.py ./package/
cd package
zip -r ../deploy.zip .
cd ..
```

## Verification
	•	Lambda Runtime: Python 3.13 (arm64)
	•	Zip/layer contents:
```
psycopg/
psycopg_binary/
psycopg_binary.libs/
lambda_function.py
```

	•	If CloudWatch logs no longer show Unable to import psycopg, the deployment is successful.

## Notes
	•	On macOS ARM (Apple Silicon), use Docker with --platform=arm64 to avoid architecture mismatch.
	•	The target build platform must match Lambda’s base image: manylinux2014_aarch64.
	•	Using --only-binary=:all: ensures a fully precompiled, portable binary for the Lambda runtime.
