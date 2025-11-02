# 서버리스 환경에서 Cafe24 액세스 토큰 발급 및 저장
가장 최근 저장된 인증코드(oauth_authorization_codes의 최신 row)를 읽어 Cafe24 OAuth 토큰을 발급 받고,
cafe24.oauth_tokens에 UPSERT한다.
API Gateway 미노출(내부 실행) 권장.

## 목차
- [아키텍처](##아키텍처)
- [요구 스펙](#요구-스펙)
- [환경 변수](#환경-변수)
- [IAM 권한](#iam-권한)
- [VPC/네트워크](#vpc네트워크)
- [핸들러](#핸들러)
- [배포](#배포)
- [API 사양 (API Gateway)](#api-사양-apigateway)
- [로깅/모니터링](#로깅모니터링)
- [트러블슈팅](#트러블슈팅)

## 아키텍처
•	(내부 호출) → Lambda(이 함수) → Cafe24 API(인터넷) + RDS(PostgreSQL, VPC)

•	인터넷 아웃바운드 필요 + DB 사설 접근 → NAT 게이트웨이 권장

## 요구 스펙
•	Python 3.13 (AWS Lambda Runtime)

•	의존성: psycopg[binary]

•	선택: 로컬 테스트용 python-dotenv

•   DB: PostgreSQL 17

•	DB 스키마(예시):

```sql
create table cafe24.oauth_tokens
(
    id                       bigserial
        primary key,
    access_token             text                                            not null,
    expires_at               timestamp with time zone                        not null,
    refresh_token            text                                            not null,
    refresh_token_expires_at timestamp with time zone default now()          not null,
    client_id                text,
    mall_id                  text                                            not null,
    user_id                  text,
    scopes                   text[],
    token_type               text                     default 'bearer'::text not null,
    issued_at                timestamp with time zone default now()          not null,
    updated_at               timestamp with time zone default now()          not null,
    status                   text                     default 'active'::text not null
);

create unique index ux_oauth_tokens_mall_id
    on cafe24.oauth_tokens (mall_id);
```

## 환경 변수
	•	PGHOST
	•	PGPORT
	•	PGUSER
	•	PGPASSWORD
	•	PGDATABASE
	•	CAFE24_MALL_ID
	•	CAFE24_CLIENT_ID
	•	CAFE24_CLIENT_SECRET
	•	CAFE24_REDIRECT_URI

## IAM 권한
	•	AWSLambdaVPCAccessExecutionRole
	•	위와 동일 + CloudWatch 기본 정책

## VPC/네트워크
	•	Lambda: 프라이빗 서브넷
	•	라우팅: 0.0.0.0/0 → NAT Gateway (Cafe24 호출용)
	•	SG:
		•	Lambda SG → RDS SG(TCP 5432) 인바운드 허용
		•	Lambda SG 아웃바운드 all

## 동작 요약
	1.	cafe24.authorization_codes 에서 최신 authorization code 조회
	2.	Cafe24 /api/v2/oauth/token에 grant_type=authorization_code POST
	•	헤더: Authorization: Basic base64(client_id:client_secret)
	•	폼: code, redirect_uri, grant_type=authorization_code
	3.	응답(JSON)을 oauth_tokens에 UPSERT

## 배포
```bash
pip install --platform manylinux2014_aarch64 --only-binary=:all: \
  --implementation cp --python-version 3.13 \
  --target ./package psycopg[binary]

cp -r package/* .
zip -r deploy.zip *.py
aws lambda update-function-code --function-name <FUNC_NAME> --zip-file fileb://deploy.zip
```

[ARM64 환경 패키지 빌드](./arm64-package-build-guide.md)

## 실행
수동 실행: 콘솔 → Test → {} 빈 이벤트로 invoke

## 로깅/모니터링
	•	네트워크 Timeout 발생 시: NAT/서브넷 라우트 확인
	•	DB upsert 실패: 필드 매핑/타임존 파싱 확인

## 트러블슈팅
	•	<urlopen error timed out>: VPC 프라이빗 + NAT 부재 → NAT 추가
	•	psycopg import 에러: manylinux2014 aarch64 바이너리로 패키징 확인
