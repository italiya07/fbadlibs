from cgi import print_directory
from functools import partial
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
from .helpers import send_forgot_password_email
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
from datetime import datetime
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

# def pre_signed_url_generator(url):
#     pre_signed_url = client.generate_presigned_url('get_object',
#                                                   Params={'Bucket': bucket_name,'Key': url},
#                                                   ExpiresIn=3600*24)
#     return pre_signed_url

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

@api_view(['GET'])
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

# @method_decorator(subscription_required,name='list')
class getAllAds(viewsets.ViewSet):
    def list(self,request):
        user_obj=request.user
        query={
            "size": 10000,
            "query": {
                "match_all": {}
            }
        }

        ad_ids=[]
        saved_ad_obj=SaveAds.objects.filter(user__id=user_obj.id).all()
        serializer=SaveAdsSerializer(saved_ad_obj,many=True)
        for i in serializer.data:
            ad_ids.append(i["ad"])

        res=es.search(index=es_indice,body=query)
        data=[]
        final_data=[]
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
                # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
                d["_source"]["id"]=d["_id"]
                data.append(d["_source"])
            final_data.append({"saved_ads":ad_ids})
            final_data.append({"all_ads": data})
            r=rh.ResponseMsg(data=final_data,error=False,msg="API is working successfully")
            return Response(r.response)

        r=rh.ResponseMsg(data={},error=True,msg="Data is not available") 
        return Response(r.response)

class userManager(viewsets.ViewSet):
    permission_classes=[IsPostOrIsAuthenticated]
# 89
    def create(self,request):
        data=request.data
        serializer=UserSerializer(data=data)
        obj=User.objects.filter(email=data["email"]).first()
        if obj:
            r=rh.ResponseMsg(data={},error=True,msg="User already exist")
            return Response(r.response)
        if serializer.is_valid():
            serializer.save()
            r=rh.ResponseMsg(data=serializer.data,error=False,msg="User created")
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
            r=rh.ResponseMsg(data={},error=True,msg="Password mismatch")
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
    print(user_obj_token)
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
                user_obj.email.set_password(password)
                user_obj.email.save()
                print(user_obj.email,password)
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

class ManageSaveAds(viewsets.ViewSet):
    # permission_classes=[AllowAny]
    # def create(self,request):
    #     data=request.data
    #     user=request.user
    #     print(user)
    #     serializer=SaveAdsSerializer(data=data)
    #     print("seri......", serializer)
    #     if serializer.is_valid():
    #         print("seri......valid..", serializer.validated_data)
    #         serializer.save(user=user)
    #         r=rh.ResponseMsg(data=serializer.data,error=False,msg="Ad Saved")
    #         return Response(r.response)
    #     r=rh.ResponseMsg(data={},error=True,msg="Ad not saved")
    #     return Response(r.response)
    
    # @method_decorator(subscription_required)
    def create(self,request):
        data=request.data
        user=request.user
        ad_obj=SaveAds.objects.filter(ad=data["ad"]).first()
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
        r=rh.ResponseMsg(data={},error=True,msg="Ad not saved")
        return Response(r.response)
 
 
    # @method_decorator(subscription_required)
    def destroy(self,request,pk=None):
        user_obj=request.user
        ad_obj=SaveAds.objects.get(user__id=user_obj.id,ad=pk)
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
    
    # def list(self,request,pk=None):
    #     user=request.user
    #     if user:
    #         obj=SaveAds.objects.filter(user__id=user.id)
    #         serializer=SaveAdsSerializer(obj,many=True)
    #         r=rh.ResponseMsg(data=serializer.data,error=False,msg="All saved ads for this user")
    #         return Response(r.response)
    #     r=rh.ResponseMsg(data={},error=False,msg="Data not found")
    #     return Response(r.response)
    
    # @method_decorator(subscription_required)
    def list(self,request,pk=None):
        user=request.user
        add=[]
        if user:
            obj=SaveAds.objects.filter(user__id=user.id)
            serializer=SaveAdsSerializer(obj,many=True)
            for i in serializer.data:
                query={
                            "size": 10000,
                            "query": {
                                "match": {
                                    "_id" : i["ad"]
                                }
                            }
                        }
                res=es.search(index=es_indice,body=query) 
                if res["hits"]["hits"]:
                    for d in res["hits"]["hits"]:
                        # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                        # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
                        # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                        # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
                        # kidfoflnm
                        d["_source"]["id"]=i["ad"]
                        add.append(d["_source"])
            r=rh.ResponseMsg(data=add,error=False,msg="All saved ads for this user")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=False,msg="Data not found")
        return Response(r.response)

class contactSupport(viewsets.ViewSet):
    # @method_decorator(subscription_required)
    def create(self,request):
        email_sender=request.data.get('email')
        name=request.data.get('name')
        msg=request.data.get('message')

        sender = config("From_email_fp")
        server = smtplib.SMTP("smtp.zoho.in", 587)
        server.starttls()
        server.login(config("From_email_fp"),config("password_fp"))
        MSG = f"Subject: mail from {name} :\n\nSender Name :- {name}\n\nMessage     :- {msg} \n\nreply back on {email_sender}"
        server.sendmail("drashti.flyontechsolution@gmail.com",config("From_email_fp"),MSG)
        server.quit()
        
        r=rh.ResponseMsg(data={},error=False,msg="Email sent")
        return Response(r.response)


class subAllAds(viewsets.ViewSet):
    # @method_decorator(subscription_required)
    def create(self,request):
        ad_name = request.data.get('ad_name')
        query={
            "size": 10000,
            "query": {
                "match": {
                    "pageInfo.name": ad_name
                }
            }
        }
 
        res=es.search(index=es_indice,body=query)
        data=[]
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
                # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
                d["_source"]["id"]=d["_id"]
                data.append(d["_source"])
            r=rh.ResponseMsg(data=data,error=False,msg="sub ads")
            return Response(r.response)
        r=rh.ResponseMsg(data={},error=True,msg="Data is not available") 
        return Response(r.response)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
# @subscription_required
@ensure_csrf_cookie
def FilterView(request):
    s = request.data.get('keywords')
    str1=" AND ".join(s)
    print(str1)
    query={
        "query": {
            "query_string": {
            "fields": ["*"],
            "query": str1
            }
        }
    }

    res=es.search(index=es_indice,body=query)
    data=[]

    if res["hits"]["hits"]:
        for d in res["hits"]["hits"]:
            # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
            # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
            d["_source"]["id"]=d["_id"]
            data.append(d["_source"])
        r=rh.ResponseMsg(data=data,error=False,msg="sub ads")
        return Response(r.response)

    r=rh.ResponseMsg(data={},error=False,msg="Success")
    return Response(r.response, status=status.HTTP_200_OK)    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
# @subscription_required
@ensure_csrf_cookie
def SavedAdFilterView(request):
    savedad_obj=SaveAds.objects.filter(user__id=request.user.id)
    serializer=SaveAdsSerializer(savedad_obj,many=True)
    ad_list=[]
    
    for i in serializer.data:
        print(i)
        ad_list.append(i["ad"])

    print(ad_list)

    s = request.data.get('keywords')
    str1=" AND ".join(s)
    print(str1)
    query={
    "query": {
        "bool": {
        "must": [
            {
            "terms": {
                "_id": ad_list
            }
            },
            {
            "query_string": {
                "fields": ["*"],
                "query": str1
            }
            }
        ]
        }
    }
    }

    res=es.search(index=es_indice,body=query)
    data=[]

    if res["hits"]["hits"]:
        for d in res["hits"]["hits"]:
            # url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["bucketMediaURL"]=pre_signed_url_generator(url)
            # url=str(d["_source"].get("thumbBucketUrl")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
            # d["_source"]["thumbBucketUrl"]=pre_signed_url_generator(url)
            d["_source"]["id"]=d["_id"]
            data.append(d["_source"])
        r=rh.ResponseMsg(data=data,error=False,msg="sub ads")
        return Response(r.response)

    r=rh.ResponseMsg(data={},error=False,msg="Success")
    return Response(r.response, status=status.HTTP_200_OK)    


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @ensure_csrf_cookie
# def Stripe_Payment_Method(request):
#     stripe.api_key = API_KEY
#     plan = request.data.get('plan')
#     automatic = 'on'
#     payment_method = 'card'

#     plan_inst = VideosPlan(plan_id=plan)

#     payment_intent = stripe.PaymentIntent.create(
#         amount=plan_inst.amount,
#         currency=plan_inst.currency,
#         payment_method_types=['card']
#     )

#     context = {}

#     if payment_method == 'card':
#         context['secret_key'] = payment_intent.client_secret
#         context['STRIPE_PUBLISHABLE_KEY'] = config('STRIPE_PUBLISHABLE_KEY')
#         context['customer_email'] = request.user.email
#         context['payment_intent_id'] = payment_intent.id
#         context['automatic'] = automatic
#         context['stripe_plan_id'] = plan_inst.stripe_plan_id
#         r=rh.ResponseMsg(data=context,error=False,msg="Success")
#         return Response(r.response, status=status.HTTP_200_OK)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @ensure_csrf_cookie
# def card(request):
#     payment_intent_id = request.data.get('payment_intent_id')
#     payment_method_id = request.data.get('payment_method_id')
#     stripe_plan_id = request.data.get('stripe_plan_id')
#     automatic = request.data.get('automatic')
#     stripe.api_key = API_KEY

#     if automatic == 'on':
#         # create subs
#         customer = stripe.Customer.create(
#             # name="Parth Bhanderi",
#             # address={
#             #     "line1": "510 Townsend St",
#             #     "postal_code": "98140",
#             #     "city": "San Francisco",
#             #     "state": "CA",
#             #     "country": "US",
#             # },
#             email=request.user.email,
#             payment_method=payment_method_id,
#             invoice_settings={
#                 'default_payment_method': payment_method_id
#             }
#         )
#         s = stripe.Subscription.create(
#             customer=customer.id,
#             items=[
#                 {
#                     'plan': stripe_plan_id
#                 },
#             ]
#         )

#         latest_invoice = stripe.Invoice.retrieve(s.latest_invoice)
#         print(latest_invoice)
#         ret = stripe.PaymentIntent.confirm(
#             latest_invoice.payment_intent
#         )

#         if ret.status == 'requires_action':
#             pi = stripe.PaymentIntent.retrieve(
#                 latest_invoice.payment_intent
#             )
#             context = {}

#             context['payment_intent_secret'] = pi.client_secret
#             context['STRIPE_PUBLISHABLE_KEY'] = settings.STRIPE_PUBLISHABLE_KEY

#             r=rh.ResponseMsg(data=context,error=False,msg="Action Required!!!")
#             return Response(r.response, status=status.HTTP_200_OK)
    
#     else:
#         stripe.PaymentIntent.modify(
#             payment_intent_id,
#             payment_method=payment_method_id
#         )

#     r=rh.ResponseMsg(data={},error=False,msg="Thank You for Payment !!!")
#     return Response(r.response, status=status.HTTP_200_OK)


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
# @subscription_required
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    stripe.api_key = API_KEY
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    print(sub_obj.subscription_id)
    cancel_sub=stripe.Subscription.delete(
        sub_obj.subscription_id,
    )
    stripe.Customer.delete(sub_obj.customer_id)
    sub_obj.delete()
    r=rh.ResponseMsg(data={},error=False,msg="Deleted successfully")
    return Response(r.response, status=status.HTTP_200_OK)
 
@api_view(['GET'])
# @subscription_required
@permission_classes([IsAuthenticated])
def fetch_payment_method(request):
    stripe.api_key = API_KEY
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    payment_details=stripe.PaymentMethod.list(
        customer=sub_obj.customer_id,
        type="card",
    )
    r=rh.ResponseMsg(data={"paydement_method_id":payment_details.data[0].id,"card_brand":payment_details.data[0].card["brand"],"country":payment_details.data[0].card["country"],"exp_month":payment_details.data[0].card["exp_month"],"exp_year":payment_details.data[0].card["exp_year"],"last4":payment_details.data[0].card["last4"],"funding":payment_details.data[0].card["funding"]},error=False,msg="Thank You for Payment !!!")
    return Response(r.response, status=status.HTTP_200_OK)

@api_view(['GET'])
# @subscription_required
@permission_classes([IsAuthenticated])
def check_sub_status(request):
    stripe.api_key = API_KEY
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    sub_status=stripe.Subscription.retrieve(
        sub_obj.subscription_id,
    )
    print(sub_status)
    end_date=sub_status.current_period_end
    plan_type=sub_status.plan.nickname
    r=rh.ResponseMsg(data={"status":sub_status.status,"end_date":datetime.utcfromtimestamp(end_date).strftime('%b %d, %Y'),"plan_type":plan_type},error=False,msg="Subscription status !!!!")
    return Response(r.response, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    stripe.api_key =API_KEY
    sub_obj=Subscription_details.objects.filter(user=request.user).first()
    if sub_obj:
        sub_status=stripe.Subscription.retrieve(
            sub_obj.subscription_id,
        )
        if sub_status.status == "active":
            r=rh.ResponseMsg(data={},error=False,msg="Subscription is already exist !!!!")
            return Response(r.response, status=status.HTTP_200_OK)

    try:
        
        # prices = stripe.Price.list(
        #     lookup_keys=[request.data.get("lookup_key")],
        #     expand=['data.product']

        # )
        # print("prices")
        # print(prices)
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            line_items=[
                {
                    'price': request.data.get("lookup_key"),
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=config("front_end") +'/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=config("front_end") + '/cancel.html',
        )
        r=rh.ResponseMsg(data={"url":checkout_session.url},error=False,msg="Subscription status !!!!")
        return Response(r.response, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        r=rh.ResponseMsg(data={},error=True,msg=str(e))
        return Response(r.response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)