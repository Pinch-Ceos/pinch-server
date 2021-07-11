import jwt
from api.models import User
from django.http import JsonResponse
from pinch.settings import JWT_SECRET


def login_decorator(func):

    def wrapper(self, request, *args, **kwargs):

        # 프론트에서 토큰 정보 제공하지 않았을 경우 -> 401 Unauthorized
        if "Authorization" not in request.headers:
            return JsonResponse({"error_code": "INVALID_LOGIN"}, status=401)

        encode_token = request.headers["Authorization"]

        try:
            data = jwt.decode(encode_token, JWT_SECRET, algorithm='HS256')

            user = User.objects.get(id=data["id"])
            request.user = user

        # 잘못된 토큰 (pinch에서 발행한 토큰이 아님)
        except jwt.DecodeError:
            return JsonResponse({
                "error_code": "INVALID_TOKEN"
            }, status=401)

        # 유저의 정보가 없음(유효하지 않은 토큰)
        except User.DoesNotExist:
            return JsonResponse({
                "error_code": "UNKNOWN_USER"
            }, status=401)

        return func(self, request, *args, **kwargs)

    return wrapper
