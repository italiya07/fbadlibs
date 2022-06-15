from .utils import token
from django.conf import settings
import datetime
import jwt
from decouple import config
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from datetime import timedelta


User = get_user_model()
class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        access_token = request.COOKIES.get('access_token')
        if access_token:
            response = self.get_response(request)
            return response
        else:
            refresh_token=request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    payload = jwt.decode(
                        refresh_token, config("REFRESH_TOKEN_SECRET"), algorithms=['HS256'])
                except jwt.ExpiredSignatureError:
                    response.delete_cookie("access_token")
                    response.delete_cookie("refresh_token")
                    raise exceptions.AuthenticationFailed(
                        'expired refresh token, please login again.')

                user = User.objects.filter(email=payload.get('email')).first()
                if user is None:
                    raise exceptions.AuthenticationFailed('User not found')

                if not user.is_active:
                    raise exceptions.AuthenticationFailed('user is inactive')
                access = token.generate_access_token(user)
                request.COOKIES["access_token"]=access

                response = self.get_response(request)

                response.set_cookie(
                                key = settings.SIMPLE_JWT['AUTH_COOKIE'], 
                                value = access,
                                expires = datetime.datetime.utcnow()+timedelta(seconds=int(config("ACCESS_TOKEN_EXPIRE_TIME_SECONDS"))),
                                secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                                httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                                samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                            )
                return response
            else:
                # request.user=User.objects.filter(id=4).first()
                response = self.get_response(request)
                return response
        # Code to be executed for each request/response after
        # the view is called.

                