from functools import wraps
from decouple import config
import stripe
from .models import *
from rest_framework.response import Response
from rest_framework import status
import utils.response_handler as rh
API_KEY = config("STRIPE_SECRET_KEY")

def subscription_required(view_func):
    def wrap(request,*args,**kwargs):
        stripe.api_key = API_KEY
        sub_obj=Subscription_details.objects.filter(user=request.user).first()
        print(sub_obj)
        if sub_obj:
            if sub_obj.sub_status == False:
                r=rh.ResponseMsg(data={"subscription":False},error=True,msg="Subscription Required")
                return Response(r.response,status=status.HTTP_403_FORBIDDEN)

            sub_status=stripe.Subscription.retrieve(
                sub_obj.subscription_id,
            )
            if sub_status.status == "active":
                return view_func(request,*args,**kwargs)

        r=rh.ResponseMsg(data={"subscription":False},error=True,msg="Subscription Required")
        return Response(r.response,status=status.HTTP_403_FORBIDDEN)
    return wrap
    