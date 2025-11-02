from lambda_function import lambda_handler

def main():
    """
    DB에 저장된 인증코드가 있을 경우 아래 인증 코드 방식은 필요 없음.
    Cafe24 redirect에서 받은 실제 code를 여기에 넣어 테스트할 수 있음.
    - 실제 유효 code로 바꿔서 테스트하면 진짜 Cafe24에 요청 가고 DB upsert까지 감.
    """
    auth_code = "ewUoEfKMKULmCl4rwoktwA"

    event = {
        "queryStringParameters": {
            "code": auth_code
        }
    }

    resp = lambda_handler(event, None)
    print("Lambda response:")
    print(resp["statusCode"])
    print(resp["body"])

if __name__ == "__main__":
    main()