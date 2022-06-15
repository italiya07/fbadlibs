from urllib import response
from django import http
import jwt
from rest_framework.authentication import BaseAuthentication
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model
# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from django.conf import settings
from rest_framework.authentication import CSRFCheck
from decouple import config
from cryptography.fernet import Fernet
from rest_framework.response import Response


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


class SafeJWTAuthentication(BaseAuthentication):
    '''
        custom authentication class for DRF and JWT
        https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py
    '''

    def authenticate(self, request):

        User = get_user_model()
        # authorization_heaader = request.headers.get('Authorization')

        try:
            # header = 'Token xxxxxxxxxxxxxxxxxxxxxxxx'
       
            raw_token = request.COOKIES.get("access_token") or None
            if raw_token is None:
                return None
            try:
                payload = jwt.decode(
                    raw_token, config("SECRET_KEY") , algorithms=['HS256'])
            except Exception:
                raise exceptions.AuthenticationFailed('Access Token is Wrong')
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')

        user = User.objects.filter(email=payload['email']).first()
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('user is inactive')

        # self.enforce_csrf(request)
        return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation
        """
        check = CSRFCheck()
        # populates request.META['CSRF_COOKIE'], which is used in process_view()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.AuthenticationFailed('CSRF Failed: %s' % reason)

