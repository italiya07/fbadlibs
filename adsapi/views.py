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
from cryptography.fernet import Fernet
import datetime
from django.conf import settings
from datetime import timedelta
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