from functools import wraps
from decouple import config
import stripe
from .models import *
from rest_framework.response import Response
from rest_framework import status
API_KEY = config("STRIPE_SECRET_KEY")

def subscription_required(view_func):
    def wrap(request,*args,**kwargs):
        stripe.api_key = API_KEY
        sub_obj=Subscription_details.objects.filter(user=request.user).first()
        if sub_obj:
            if sub_obj.sub_status == False:
                return Response("Subscription Required", status=status.HTTP_200_OK)

            sub_status=stripe.Subscription.retrieve(
                sub_obj.subscription_id,
            )
            if sub_status.status == "active":
                return view_func(request,*args,**kwargs)
        return Response("Subscription Required", status=status.HTTP_200_OK)
    return wrap
    