from functools import partial
from django.shortcuts import render
from rest_framework import viewsets
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from rest_framework.response import Response
import boto3
from decouple import config
import utils.response_handler as rh
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model, login, logout,authenticate
from .utils import token
import datetime
from django.conf import settings
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from rest_framework import serializers
from .serializer import *
import uuid
from django.views.decorators.csrf import ensure_csrf_cookie
from .helpers import send_forgot_password_email
from .forms import ChangePasswordCustomForm
from django.contrib import messages

# Create your views here.

User = get_user_model()

es=Elasticsearch(
    [config("elasticsearch_host")],
    http_auth=(config("elasticsearch_username"), config("elasticsearch_password")),
    )

s3_resource = boto3.resource('s3',aws_access_key_id = config("aws_access_key_id"),aws_secret_access_key = config("aws_secret_access_key"))
client = boto3.client("s3",
                          aws_access_key_id=config("aws_access_key_id"),
                          aws_secret_access_key=config("aws_secret_access_key"))



es_indice='fbadslib-dev'
es.indices.create(index=es_indice,ignore=400)
bucket_name="fbadslib-dev"


@api_view(['POST'])
@permission_classes([AllowAny])
# @ensure_csrf_cookie
def loginview(request):
    email=request.data.get('email')
    password=request.data.get('password')
    # decMessage = fernet.decrypt(password.encode('utf-8')).decode()
    user=User.objects.filter(email=email).first()
    if user and user.check_password(password) and user.is_active:
        authenticate(email=email, password=user.check_password(password))
        response = Response() 
        access_token = token.generate_access_token(user)
        refresh_token = token.generate_refresh_token(user)
        response.set_cookie(
                    key = 'access_token', 
                    value = access_token,
                    expires = datetime.datetime.utcnow()+timedelta(seconds=int(config("ACCESS_TOKEN_EXPIRE_TIME_SECONDS"))),
                    secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                )
        response.set_cookie(
                    key = 'refresh_token', 
                    value = refresh_token,
                    expires = datetime.datetime.utcnow()+timedelta(seconds=int(config('REFRESH_TOKEN_EXPIRE_TIME_SECONDS'))),
                    secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                )
        # csrf.get_token(request)
        response.data={
            "error": False,
            "data":{},
            "message": "Successfully Login"
        }
        return response
    else:
        r=rh.ResponseMsg(data={},error=True,msg="Username and Password does not exist.")
        return Response(r.response, status=status.HTTP_404_NOT_FOUND)

class getAllAds(viewsets.ViewSet):
    def list(self,request):
        print(es.ping())
        query={
            "size": 10000,
            "query": {
                "match_all": {}
            }
        }

        res=es.search(index=es_indice,body=query)
        data=[]
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                pre_signed_url = client.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name,'Key': url},
                                                  ExpiresIn=3600*24)
                d["_source"]["bucketMediaURL"]=pre_signed_url
                data.append(d["_source"])
            r=rh.ResponseMsg(data=data,error=False,msg="API is working successfully")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=True,msg="Data is not available") 
        return Response(r.response)

class userManager(viewsets.ViewSet):
    def create(self,request):
        data=request.data
        serializer=UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            r=rh.ResponseMsg(data=serializer.data,error=False,msg="User created")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=True,msg="User creation failed")
        return Response(r.response)

    def destroy(self,request,pk=None):
        user=User.objects.get(pk=pk)
        user.delete()
        r=rh.ResponseMsg(data={},error=False,msg="User Deleted")
        return Response(r.response)
    
    def update(self,request,pk=None):
        user=User.objects.get(pk=pk)
        data=request.data
        serializer=UserSerializer(user,data=data,partial=True)
        if serializer.is_valid():
            serializer.save(password=data["password"])
            r=rh.ResponseMsg(data=serializer.data,error=False,msg="User Updated")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=True,msg="User updation failed")
        return Response(r.response)

@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def Forgotpasswordview(request):
    email=request.data.get('email')
    user_obj=User.objects.filter(email=email).first()
    if not user_obj:
        r=rh.ResponseMsg(data={},error=True,msg="Sorry, This email Id does not exist with us")
        return Response(r.response, status=status.HTTP_404_NOT_FOUND)
    user_obj_token=ForgotPassword.objects.filter(user__email=user_obj.email).first()
    token=str(uuid.uuid4())
    if user_obj_token:
        user_obj_token.forgot_password_token=token
        user_obj_token.save()
    else:
        new_token_obj=ForgotPassword.objects.create(user=user_obj,forgot_password_token=token)
        new_token_obj.save()
    send_forgot_password_email(request,token,email)
    r=rh.ResponseMsg(data={},error=False,msg="Success")
    return Response(r.response, status=status.HTTP_200_OK)    
    

@permission_classes([AllowAny])
@ensure_csrf_cookie
def Change_password(request,token):
    if request.method == 'POST':
        form = ChangePasswordCustomForm(request.POST)
        if form.is_valid():
            print("hello")
            user_obj=ForgotPassword.objects.filter(forgot_password_token=token).first()
            if user_obj: 
                password=form.cleaned_data.get("new_password2")
                user_obj.user.set_password(password)
                user_obj.user.save()
                print(user_obj.user,password)
                messages.success(request, 'Your password was successfully updated!')
                user_obj.delete()
                return render(request, 'success.html')
            else:
                return render(request, 'error.html')
        else:
            print(form.errors)
            return render(request, 'error.html')
    else:
        user_obj=ForgotPassword.objects.filter(forgot_password_token=token).first()
        if user_obj:
            form = ChangePasswordCustomForm()
        else:
            return render(request, 'error.html')
    return render(request, 'change_password.html', {
        'form': form
    })    

class contactSupport(viewsets.ViewSet):
    def create(self,request):
        sender = 'parthbhanderi16@gmail.com'
        receivers = 'parth.flyontechsolution@gmail.com'
