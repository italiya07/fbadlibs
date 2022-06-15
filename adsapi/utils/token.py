import datetime
import jwt
from django.conf import settings
from decouple import config


def generate_access_token(user):

    access_token_payload = {
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=int(config("ACCESS_TOKEN_EXPIRE_TIME_SECONDS"))),
        'iat': datetime.datetime.utcnow(),
    }
    # print(access_token_payload)
    access_token = jwt.encode(access_token_payload,config('SECRET_KEY'),algorithm='HS256').decode('utf-8')
    print(access_token)
    return access_token


def generate_refresh_token(user):
    refresh_token_payload = {
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=int(config("REFRESH_TOKEN_EXPIRE_TIME_SECONDS"))),
        'iat': datetime.datetime.utcnow()
    }
    refresh_token = jwt.encode(refresh_token_payload, config("REFRESH_TOKEN_SECRET") , algorithm='HS256').decode('utf-8')

    return refresh_token