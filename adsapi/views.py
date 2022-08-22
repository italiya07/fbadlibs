from calendar import c
from cgi import print_directory
from email.policy import HTTP
from functools import partial
from typing_extensions import final
from django.shortcuts import render
from elastic_transport import Serializer
from rest_framework import viewsets
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from rest_framework.response import Response
import boto3
from decouple import config
import utils.response_handler as rh
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes 
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny,IsAuthenticated
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
from .helpers import send_forgot_password_email,send_activation_email, send_support_email
from .forms import ChangePasswordCustomForm
from django.contrib import messages
import jwt
import json
import stripe
from payments.stripe import (VideosPlan, set_paid_until)
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import logging
from django.http import (
    HttpResponse,
    HttpResponseRedirect
)
from .decorators import subscription_required
from .custom_permission import IsPostOrIsAuthenticated
# Create your views here.

User = get_user_model()
logger = logging.getLogger(__name__)

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

API_KEY = config("STRIPE_SECRET_KEY")

@api_view(['GET'])
@permission_classes([AllowAny])
def Isalive(request): 
    access_token = request.COOKIES.get('access_token')
    if access_token:
        r=rh.ResponseMsg(data={"is_alive":True},error=False,msg="success")
        return Response(r.response,status=status.HTTP_200_OK)
    else:
        refresh_token = request.COOKIES.get('refresh_token')
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
            response=Response()
            response.set_cookie(
                            key = settings.SIMPLE_JWT['AUTH_COOKIE'], 
                            value = access,
                            expires = datetime.datetime.utcnow()+settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                            secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                            httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                            samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                        )
            response.data={
                    "error": False,
                    "data":{"is_alive":True},
                    "message": "Accesstoken Updated"
                }
            return response
        else:
            r=rh.ResponseMsg(data={"is_alive":False},error=False,msg="success")
            return Response(r.response,status=status.HTTP_200_OK)

# Use login
@api_view(['POST'])
@permission_classes([AllowAny])
# @ensure_csrf_cookie
def loginview(request):
    email=request.data.get('email')
    password=request.data.get('password')
    # decMessage = fernet.decrypt(password.encode('utf-8')).decode()
    user=User.objects.filter(email=email).first()
    if user :
        if user.is_active:
            if user.check_password(password):
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

                response.status_code=200
                return response
        
            else:
                r=rh.ResponseMsg(data={},error=True,msg="Invalid email address or password")
                return Response(r.response, status=status.HTTP_400_BAD_REQUEST)
        else:
            r=rh.ResponseMsg(data={},error=True,msg="Please verify your email address")
            return Response(r.response, status=status.HTTP_401_UNAUTHORIZED)
    r=rh.ResponseMsg(data={},error=True,msg="User does not exist with us.")
    return Response(r.response, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logoutview(request):
    response = Response()
    logout(request)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.data={
        "error":False,
        "data":{},
        "message":"logout successfully!!!"
    }
    return response


@api_view(['POST'])
@subscription_required
def getAllSavedAds(request):
        user=request.user
        page_index=request.data.get("page_index")
        startdate=request.data.get("startdate")
        enddate=request.data.get("enddate")
        adcount=request.data.get("adcount")
        adstatus=request.data.get("adstatus")
        fb_likes=request.data.get("fb_likes")
        insta_followers=request.data.get("insta_followers")
        media_type=request.data.get("media_type")
        ctaStatus=request.data.get("cta_status")
        s = request.data.get('keywords')
        p = request.data.get('phrase')
        sort_param=request.data.get('sort_by')
        order_by=request.data.get('order_by')
        increased=request.data.get('increaseCount')
        page_size=request.data.get('number_of_pagead')

        ad_list=[]
        if user:
            obj=SaveAds.objects.filter(user__id=user.id)
            serializer=SaveAdsSerializer(obj,many=True)
            for i in serializer.data:
                ad_list.append(i["ad"])

        if ad_list:
            query={
            # "from": int(page_index)*int(page_size),
            "size":10000,
            "query": {
                    "bool": {
                    "must": [
                        {
                        "terms": {
                                "_id": ad_list
                            }
                        }
                    ]
                    }
                },
            "sort": []
            }

            if startdate and enddate :
                date_query={
                    "range": {
                        "startDate": {
                        "gte": startdate,
                        "lte": enddate
                        }
                    }
                }
                query["query"]["bool"]["must"].append(date_query)

            if adcount:
                adcount_query={
                    "range": {
                    "noOfCopyAds": {
                        "gte": int(adcount[0]),
                        "lte": int(adcount[1])
                        }
                    }
                }
                query["query"]["bool"]["must"].append(adcount_query)

            if adstatus:
                status_query={
                    "match": {
                        "status.keyword": adstatus
                    }
                }
                query["query"]["bool"]["must"].append(status_query)
            
            if fb_likes:
                likes_query={
                    "range": {
                    "pageInfo.platforms.likes": {
                        "gte": int(fb_likes[0]),
                        "lte": int(fb_likes[1])
                        }
                    }
                }
                query["query"]["bool"]["must"].append(likes_query)
            
            if insta_followers:
                followers_query={
                    "range": {
                        "pageInfo.platforms.followers": {
                        "gte": int(insta_followers[0]),
                        "lte": int(insta_followers[1])
                        }
                    }
                }
                query["query"]["bool"]["must"].append(followers_query)
            
            if media_type:
                media_query={
                    "match": {
                        "adMediaType.keyword": media_type
                    }
                }
                query["query"]["bool"]["must"].append(media_query)

            if ctaStatus:
                cta_query={
                    "match": {
                        "ctaStatus": ctaStatus
                    }
                }
                query["query"]["bool"]["must"].append(cta_query)

            if s:
                str1=[]
                for i in s:
                    str1.append(i)
                
                str1=" AND ".join(str1)
                
                keyword_query={
                        "query_string": {
                        "fields": ["*"],
                        "query": str1
                        }
                    }
                
                query["query"]["bool"]["must"].append(keyword_query)

            if p:
                for i in p:
                    phrase_query={
                            "multi_match": {
                                "query": i.strip(),
                                "type": "phrase", 
                                "fields": ["*"]
                            }
                    }
                query["query"]["bool"]["must"].append(phrase_query)

            if increased:
                increament_query={
                    "match": {
                            "increaseCount": increased
                        }
                    }
                query["query"]["bool"]["must"].append(increament_query)
            
            if sort_param and order_by:
                sort_query={
                    sort_param:{"order":order_by}
                }
                query["sort"].append(sort_query)
        
            res=es.search(index=es_indice,body=query)
            data=[]

            # import math
            # if int(res["hits"]["total"]["value"]) % int(page_size) == 0:
            #     number_of_pages=(int(res["hits"]["total"]["value"])/int(page_size))
            # elif int(res["hits"]["total"]["value"]) <= int(page_size):
            #     number_of_pages=1
            # else:
            #     number_of_pages=math.ceil(int(res["hits"]["total"]["value"])/int(page_size))   

            final_data={}

            if res["hits"]["hits"]:
                for d in res["hits"]["hits"]:
                    # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                    # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
                    # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                    # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
                    d["_source"]["id"]=d["_id"]
                    data.append(d["_source"])

                final_data["total_ads"]=res["hits"]["total"]["value"]
                final_data["all_ads"]= data

                r=rh.ResponseMsg(data=final_data,error=False,msg="API is working successfully")
                return Response(r.response)
        r=rh.ResponseMsg(data=[],error=True,msg="Data is not available") 
        return Response(r.response)

@method_decorator(subscription_required,name='create')
class getAllAds(viewsets.ViewSet):
    # @method_decorator(subscription_required)
    def create(self,request):
        print(request.data)
        page_index=request.data.get("page_index")
        startdate=request.data.get("startdate")
        enddate=request.data.get("enddate")
        adcount=request.data.get("adcount")
        adstatus=request.data.get("adstatus")
        fb_likes=request.data.get("fb_likes")
        insta_followers=request.data.get("insta_followers")
        media_type=request.data.get("media_type")
        ctaStatus=request.data.get("cta_status")
        s = request.data.get('keywords')
        p = request.data.get('phrase')
        sort_param=request.data.get('sort_by')
        order_by=request.data.get('order_by')
        increased=request.data.get('increaseCount')
        user_obj=request.user
        page_size=request.data.get('number_of_pagead')
        query={
            "from": int(page_index)*int(page_size),
            "size": int(page_size),
            "query": {
                "bool":{
                    "must":[]
                }
            },
            "sort": []
        }

        if startdate and enddate :
            date_query={
                "range": {
                    "startDate": {
                    "gte": startdate,
                    "lte": enddate
                    }
                }
            }
            query["query"]["bool"]["must"].append(date_query)

        if adcount:
            adcount_query={
                "range": {
                "noOfCopyAds": {
                    "gte": int(adcount[0]),
                    "lte": int(adcount[1])
                    }
                }
            }
            query["query"]["bool"]["must"].append(adcount_query)

        if adstatus:
            status_query={
                "match": {
                    "status.keyword": adstatus
                }
            }
            query["query"]["bool"]["must"].append(status_query)
        
        if fb_likes:
            likes_query={
                "range": {
                "pageInfo.platforms.likes": {
                    "gte": int(fb_likes[0]),
                    "lte": int(fb_likes[1])
                    }
                }
            }
            query["query"]["bool"]["must"].append(likes_query)
        
        if insta_followers:
            followers_query={
                "range": {
                    "pageInfo.platforms.followers": {
                    "gte": int(insta_followers[0]),
                    "lte": int(insta_followers[1])
                    }
                }
            }
            query["query"]["bool"]["must"].append(followers_query)
        
        if media_type:
            media_query={
                "match": {
                    "adMediaType.keyword": media_type
                }
            }
            query["query"]["bool"]["must"].append(media_query)

        if ctaStatus:
            cta_query={
                "match": {
                    "ctaStatus": ctaStatus
                }
            }
            query["query"]["bool"]["must"].append(cta_query)

        if s:
            str1=[]
            for i in s:
                str1.append(i)
            
            str1=" AND ".join(str1)
            
            keyword_query={
                    "query_string": {
                    "fields": ["*"],
                    "query": str1
                    }
            }
            query["query"]["bool"]["must"].append(keyword_query)

        if p:
            for i in p:
                phrase_query={
                        "multi_match": {
                            "query": i.strip(),
                            "type": "phrase", 
                            "fields": ["*"]
                        }
                }
            query["query"]["bool"]["must"].append(phrase_query)

        if increased:
            increament_query={
                "match": {
                        "increaseCount": increased
                    }
                }
            query["query"]["bool"]["must"].append(increament_query)
        
        if sort_param and order_by:
            sort_query={
                sort_param:{"order":order_by}
            }
            query["sort"].append(sort_query)
       
        

        ad_ids=[]
        saved_ad_obj=SaveAds.objects.filter(user__id=user_obj.id).all()
        serializer=SaveAdsSerializer(saved_ad_obj,many=True)
        for i in serializer.data:
            ad_ids.append(i["ad"])
        
        res=es.search(index=es_indice,body=query)

        import math
        if int(res["hits"]["total"]["value"]) % int(page_size) == 0:
            number_of_pages=(int(res["hits"]["total"]["value"])/int(page_size))
        elif int(res["hits"]["total"]["value"]) <= int(page_size):
            number_of_pages=1
        else:
            number_of_pages=math.ceil(int(res["hits"]["total"]["value"])/int(page_size))   

        data=[]
        final_data={}
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
                # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
                d["_source"]["id"]=d["_id"]
                data.append(d["_source"])
            final_data["total_pages"]=number_of_pages
            final_data["saved_ads"]=ad_ids
            final_data["all_ads"]= data
            
        
            r=rh.ResponseMsg(data=final_data,error=False,msg="API is working successfully")
            return Response(r.response)

        r=rh.ResponseMsg(data={"saved_ads":[], "all_ads":[]},error=True,msg="Data is not available") 
        return Response(r.response)

@api_view(['POST'])
# @subscription_required
def checkAdByFilter(request):
    # @method_decorator(subscription_required)
    print(request.data)
    print(request.data.get("adId"))
    adId= request.data.get("adId")
    startdate=request.data.get("startdate")
    enddate=request.data.get("enddate")
    adcount=request.data.get("adcount")
    adstatus=request.data.get("adstatus")
    fb_likes=request.data.get("fb_likes")
    insta_followers=request.data.get("insta_followers")
    media_type=request.data.get("media_type")
    ctaStatus=request.data.get("cta_status")
    s = request.data.get('keywords')
    p = request.data.get('phrase')
    sort_param=request.data.get('sort_by')
    order_by=request.data.get('order_by')
    increased=request.data.get('increaseCount')
    page_index=request.data.get("page_index")
    page_size=request.data.get('number_of_pagead')
    query={
        "query": {
            "bool":{
                "must":[]
            }
        },
        "sort": []
    }

    ad_query={
        "match": {
            "_id": adId
        }
    }

    query["query"]["bool"]["must"].append(ad_query)

    if startdate and enddate :
        date_query={
            "range": {
                "startDate": {
                "gte": startdate,
                "lte": enddate
                }
            }
        }
        query["query"]["bool"]["must"].append(date_query)

    if adcount:
        adcount_query={
            "range": {
            "noOfCopyAds": {
                "gte": int(adcount[0]),
                "lte": int(adcount[1])
                }
            }
        }
        query["query"]["bool"]["must"].append(adcount_query)

    if adstatus:
        status_query={
            "match": {
                "status.keyword": adstatus
            }
        }
        query["query"]["bool"]["must"].append(status_query)
    
    if fb_likes:
        likes_query={
            "range": {
            "pageInfo.platforms.likes": {
                "gte": int(fb_likes[0]),
                "lte": int(fb_likes[1])
                }
            }
        }
        query["query"]["bool"]["must"].append(likes_query)
    
    if insta_followers:
        followers_query={
            "range": {
                "pageInfo.platforms.followers": {
                "gte": int(insta_followers[0]),
                "lte": int(insta_followers[1])
                }
            }
        }
        query["query"]["bool"]["must"].append(followers_query)
    
    if media_type:
        media_query={
            "match": {
                "adMediaType.keyword": media_type
            }
        }
        query["query"]["bool"]["must"].append(media_query)

    if ctaStatus:
        cta_query={
            "match": {
                "ctaStatus": ctaStatus
            }
        }
        query["query"]["bool"]["must"].append(cta_query)

    if s:
        str1=[]
        for i in s:
            str1.append("*"+i+"*")
        
        str1=" AND ".join(str1)
        
        keyword_query={
                "query_string": {
                "fields": ["*"],
                "query": str1
                }
        }
        query["query"]["bool"]["must"].append(keyword_query)

    if p:
        for i in p:
            phrase_query={
                    "multi_match": {
                        "query": i.strip(),
                        "type": "phrase", 
                        "fields": ["*"]
                    }
            }
        query["query"]["bool"]["must"].append(phrase_query)

    if increased:
        increament_query={
            "match": {
                    "increaseCount": increased
                }
            }
        query["query"]["bool"]["must"].append(increament_query)
    
    if sort_param and order_by:
        sort_query={
            sort_param:{"order":order_by}
        }
        query["sort"].append(sort_query)
    
    res=es.search(index=es_indice,body=query)

    if res["hits"]["hits"]:
        if len(res["hits"]["hits"]) > 0 :
            ad = res["hits"]["hits"][0]
            ad["_source"]["id"]=ad["_id"]
            r=rh.ResponseMsg(data={"AdDetails": ad["_source"],"valid":True},error=False,msg="API is working successfully")
        else:
            r=rh.ResponseMsg(data={},error=False,msg="API is working successfully")
        return Response(r.response)

    r=rh.ResponseMsg(data=False,error=True,msg="Data is not available") 
    return Response(r.response)        

class userManager(viewsets.ViewSet):
    permission_classes=[IsPostOrIsAuthenticated]

    def create(self,request):
        data=request.data
        if len(data["password"])<7:
            r=rh.ResponseMsg(data={},error=True,msg="Password is too short")
            return Response(r.response)
        serializer=UserSerializer(data=data)
        obj=User.objects.filter(email=data["email"]).first()
        
        if obj:
            r=rh.ResponseMsg(data={},error=True,msg="User already exist")
            return Response(r.response)

        if serializer.is_valid():
            serializer.save()   
            user=User.objects.get(email=serializer.data.get("email"))
            email_token=token.generate_activation_token(user)
            print(email_token)
            send_activation_email(request,email_token,serializer.data.get("email"))
            r=rh.ResponseMsg(data=serializer.data,error=False,msg="Check your email to activate your account")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=True,msg="User creation failed")
        return Response(r.response)

    # @method_decorator(subscription_required)
    def destroy(self,request,pk=None):
        user=User.objects.filter(id=pk).first()
        user.delete()
        r=rh.ResponseMsg(data={},error=False,msg="User Deleted")
        return Response(r.response)
    
    # @method_decorator(subscription_required)
    def update(self,request,pk=None):
        user=User.objects.filter(id=pk).first()
        data=request.data

        if "c_password" in request.data.keys():
            if user.check_password(data["c_password"]):
                serializer=UserSerializer(user,data=data,partial=True)
                if serializer.is_valid():
                    serializer.save(password=data["n_password"])
                    r=rh.ResponseMsg(data=serializer.data,error=False,msg="Password Updated")
                    return Response(r.response)
            r=rh.ResponseMsg(data={},error=True,msg="Current password mismatch")
            return Response(r.response)
        else:
            serializer=UserSerializer(user,data=data,partial=True)
            if serializer.is_valid():
                serializer.save()
                r=rh.ResponseMsg(data=serializer.data,error=False,msg="User Updated")
                return Response(r.response)
    
        r=rh.ResponseMsg(data={},error=True,msg="Error in updation")
        return Response(r.response)

    # @method_decorator(subscription_required)
    def list(self,request):
        user=User.objects.get(id=request.user.id)
        serializer=UserSerializer(user)
        r=rh.ResponseMsg(data=serializer.data,error=False,msg="User found")
        return Response(r.response)

@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def Forgotpasswordview(request):
    email=request.data.get('email')
    user_obj=User.objects.filter(email=email).first()
    print(email,user_obj)
    if not user_obj:
        r=rh.ResponseMsg(data={},error=True,msg="Sorry, This email Id does not exist with us")
        return Response(r.response, status=status.HTTP_404_NOT_FOUND)
    user_obj_token=ForgotPassword.objects.filter(email__email=user_obj.email).first()
    token=str(uuid.uuid4())
    if user_obj_token:
        user_obj_token.forgot_password_token=token
        user_obj_token.save()
    else:
        new_token_obj=ForgotPassword.objects.create(email=user_obj,forgot_password_token=token)
        new_token_obj.save()
    send_forgot_password_email(request,token,email)
    r=rh.ResponseMsg(data={},error=False,msg="Success")
    return Response(r.response, status=status.HTTP_200_OK)    
    
@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def Change_password(request):
    password=request.data.get("password")
    token=request.data.get("token")
    fp_obj=ForgotPassword.objects.filter(forgot_password_token=token).first()
    
    if fp_obj:
        fp_obj.email.set_password(password)
        fp_obj.email.save()
        fp_obj.delete()
        r=rh.ResponseMsg(data={},error=False,msg="Password updated")
        return Response(r.response, status=status.HTTP_200_OK)

    r=rh.ResponseMsg(data={},error=True,msg="Token is not valid")
    return Response(r.response, status=status.HTTP_200_OK)
    

@api_view(["GET"])
@permission_classes([AllowAny])
def Verify_Email(request):
    token=request.GET.get('token')
    if token:
        
        try:
            payload = jwt.decode(token, config("SECRET_KEY"), algorithms=['HS256'])
        except:
            r=rh.ResponseMsg(data={},error=True,msg="Token has already been expired")
            return Response(r.response, status=status.HTTP_200_OK)
        
        if payload:
            user_obj=User.objects.filter(email=payload["email"]).first()
            if user_obj.is_active:
                r=rh.ResponseMsg(data={},error=True,msg="User account has already been activated.")
                return Response(r.response, status=status.HTTP_200_OK)
            
            user_obj.is_active=True
            user_obj.save()
            r=rh.ResponseMsg(data={},error=False,msg="User Verified")
            return Response(r.response, status=status.HTTP_200_OK)

class ManageSaveAds(viewsets.ViewSet):
    permission_classes=[IsPostOrIsAuthenticated]
    
    # @method_decorator(subscription_required)
    def create(self,request):
        data=request.data
        user=request.user
        ad_obj=SaveAds.objects.filter(ad=data["ad"], user=user).first()
        if ad_obj:
            r=rh.ResponseMsg(data={"id":ad_obj.id,"ad":ad_obj.ad},error=True,msg="Ad already saved")
            return Response(r.response)
        serializer=SaveAdsSerializer(data=data)
        query={
            "size": 10000,
            "query": {
                "match": {
                    "_id" : data["ad"]
                }
            }
        }
        res=es.search(index=es_indice,body=query)
        add=[]
        # fdata=[]
        if res["hits"]["hits"]:
            # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
            # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
            res["hits"]["hits"][0]["_source"]["id"]=data["ad"]
            add.append(res["hits"]["hits"][0]["_source"])
             
        if serializer.is_valid():
            serializer.save(user=user)
            # d["_source"]["saved_id"]=serializer.data["id"]
            # fdata.append({"ad_detail":add})
            # fdata.append({"id":serializer.data["id"], "ad":serializer.data["ad"]})
            r=rh.ResponseMsg(data=add,error=False,msg="Ad Saved")
            return Response(r.response)
        r=rh.ResponseMsg(data=[],error=True,msg="Ad not saved")
        return Response(r.response)
 
 
    # @method_decorator(subscription_required)
    def destroy(self,request,pk=None):
        user_obj=request.user
        ad_obj=SaveAds.objects.filter(user__id=user_obj.id,ad=pk).all()
        add=[]
        query={
                "size": 10000,
                "query": {
                    "match": {
                        "_id" : ad_obj.ad
                    }
                }
            }
        res=es.search(index=es_indice,body=query)
        if res["hits"]["hits"]:
            res["hits"]["hits"][0]["_source"]["id"]=ad_obj.ad
            add.append(res["hits"]["hits"][0]["_source"])
        ad_obj.delete()
        r=rh.ResponseMsg(data=add,error=False,msg="Ad deleted successfully")
        return Response(r.response)
    

class contactSupport(viewsets.ViewSet):
    def create(self,request):
        email_sender=request.data.get('email')
        name=request.data.get('name')
        message=request.data.get('message')

        result=send_support_email(email_sender,name,message)

        if result:
            r=rh.ResponseMsg(data={},error=False,msg="Email sent")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=True,msg="Email not sent")
        return Response(r.response)

# @method_decorator(subscription_required,name='list')
class subAllAds(viewsets.ViewSet):
    # @method_decorator(subscription_required)
    def create(self,request):
        page_name = request.data.get('page_name')
        page_index=request.data.get("page_index")
        page_size=request.data.get('number_of_pagead')
        query={
            "from": int(page_index)*int(page_size),
            "size": int(page_size),
            "query": {
                "match": {
                    "pageInfo.name": page_name
                }
            }
        }

        res=es.search(index=es_indice,body=query)
        import math
        if int(res["hits"]["total"]["value"]) % int(page_size) == 0:
            number_of_pages=(int(res["hits"]["total"]["value"])/int(page_size))
        elif int(res["hits"]["total"]["value"]) <= int(page_size):
            number_of_pages=1
        else:
            number_of_pages=math.ceil(int(res["hits"]["total"]["value"])/int(page_size))   

        final_data={}
        data=[]
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
                # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
                d["_source"]["id"]=d["_id"]
                data.append(d["_source"])
            final_data["data"]=data
            final_data["total_pages"]=number_of_pages
            r=rh.ResponseMsg(data=final_data,error=False,msg="sub ads")
            return Response(r.response)
        r=rh.ResponseMsg(data=[],error=True,msg="Data is not available") 
        return Response(r.response)



@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhooks(request):

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config("STRIPE_WEBHOOK_SIGNING_KEY")
        )
        logger.info("Event constructed correctly")
    except ValueError:
        # Invalid payload
        logger.warning("Invalid Payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.warning("Invalid signature")
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'charge.succeeded':
        pass   

    if event.type == 'invoice.payment_succeeded':
        print("---------------------------------------------------------------------")
        set_paid_until(event.data.object)
    
    r=rh.ResponseMsg(data={},error=False,msg="Webhook triggered")
    return Response(r.response, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    stripe.api_key = API_KEY
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    print(sub_obj.subscription_id)
    cancel_sub=stripe.Subscription.delete(
        sub_obj.subscription_id,
    )
    sub_obj.sub_status=False
    sub_obj.save()
    r=rh.ResponseMsg(data={'status':'Deactivated'},error=False,msg="Deleted successfully")
    return Response(r.response, status=status.HTTP_200_OK)
 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_payment_method(request):
    stripe.api_key = API_KEY
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    if sub_obj:
        payment_details=stripe.PaymentMethod.list(
            customer=sub_obj.customer_id,
            type="card",
        )
        if sub_obj.sub_status == True:
            sub_status=stripe.Subscription.retrieve(
                sub_obj.subscription_id,
            )
            if sub_status.status == "active":
                end_date=sub_status.current_period_end
                r=rh.ResponseMsg(data={"status":sub_status.status,"end_date":datetime.datetime.utcfromtimestamp(end_date).strftime('%b %d, %Y'),"plan_type":sub_status.plan.nickname,"paydement_method_id":payment_details.data[0].id,"card_brand":payment_details.data[0].card["brand"],"country":payment_details.data[0].card["country"],"exp_month":payment_details.data[0].card["exp_month"],"exp_year":payment_details.data[0].card["exp_year"],"last4":payment_details.data[0].card["last4"],"funding":payment_details.data[0].card["funding"]},error=False,msg="Thank You for Payment !!!")
                return Response(r.response, status=status.HTTP_200_OK)
        
        r=rh.ResponseMsg(data={"status":"Canceled","paydement_method_id":payment_details.data[0].id,"card_brand":payment_details.data[0].card["brand"],"country":payment_details.data[0].card["country"],"exp_month":payment_details.data[0].card["exp_month"],"exp_year":payment_details.data[0].card["exp_year"],"last4":payment_details.data[0].card["last4"],"funding":payment_details.data[0].card["funding"]},error=False,msg="Subscription is cancelled")
        return Response(r.response, status=status.HTTP_200_OK)
    r=rh.ResponseMsg(data={"status":"Inactive"},error=False,msg="No subscription is active")
    return Response(r.response, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    stripe.api_key =API_KEY
    
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    print(sub_obj)
    if sub_obj:
        sub_status=stripe.Subscription.retrieve(
            sub_obj.subscription_id,
        )

        if sub_status.status == "active":
            r=rh.ResponseMsg(data={},error=False,msg="Subscription is already exist !!!!")
            return Response(r.response, status=status.HTTP_200_OK)
        
        else:
            customer_id=sub_obj.customer_id
            try:
                checkout_session = stripe.checkout.Session.create(
                    # customer_email=request.user.email,
                    customer=customer_id,
                    line_items=[
                        {
                            'price': request.data.get("lookup_key"),
                            'quantity': 1,
                        },
                    ],
                    mode='subscription',
                    success_url=f'{config("front_end")}/',
                    cancel_url=f'{config("front_end")}/plans',
                )
                r=rh.ResponseMsg(data={"url":checkout_session.url},error=False,msg="Subscription status !!!!")
                return Response(r.response, status=status.HTTP_200_OK)

            except Exception as e:
                print(e)
                r=rh.ResponseMsg(data={},error=True,msg=str(e))
                return Response(r.response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            line_items=[
                {
                    'price': request.data.get("lookup_key"),
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'{config("front_end")}/',
            cancel_url=f'{config("front_end")}/plans',
        )
        r=rh.ResponseMsg(data={"url":checkout_session.url},error=False,msg="Subscription status !!!!")
        return Response(r.response, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        r=rh.ResponseMsg(data={},error=True,msg=str(e))
        return Response(r.response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getCtaStatus(request):
    query={
        "query": {
            "match_all": {}
        }
    }

    res=es.search(index=es_indice,body=query)
    cta_status=[]
    if res["hits"]["hits"]:
        for d in res["hits"]["hits"]:
            cta_status.append((d["_source"]["ctaStatus"]).lower())
        
        set_cta=set(cta_status)
        list_using_comp = [var.title() for var in list(set_cta) if len(var)>0 ]
        r=rh.ResponseMsg(data={"cta_status":list_using_comp},error=False,msg="API is working successfully")
        return Response(r.response)

    r=rh.ResponseMsg(data={},error=True,msg="Data is not available") 
    return Response(r.response)

@api_view(["POST"])
def Databyid(request):
    id=request.data.get("id")
    if id:
        query={
                "query": {
                    "match": {
                        "_id" : id
                    }
                }
        }
        res=es.search(index=es_indice,body=query)
        
        if res["hits"]["hits"]:
            # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
            # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
            r=rh.ResponseMsg(data=res["hits"]["hits"][0]["_source"],error=False,msg="Ad Saved")
            return Response(r.response)

        r=rh.ResponseMsg(data={},error=True,msg="Ad not found")
        return Response(r.response)

@api_view(["POST"])
@permission_classes([AllowAny])
def resendVerificationEmail(request):
    email=request.data.get("email")
    user=User.objects.get(email=email)
    
    if user:
        
        if user.is_active:
            r=rh.ResponseMsg(data={},error=False,msg="User is already verified.")
            return Response(r.response)

        email_token=token.generate_activation_token(user)
        print(email_token)
        send_activation_email(request,email_token,email)
        r=rh.ResponseMsg(data={},error=False,msg="Email sent")
        return Response(r.response)
    
    r=rh.ResponseMsg(data={},error=True,msg="User with this email address does not exist with us.")
    return Response(r.response)
