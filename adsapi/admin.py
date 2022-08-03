from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import *
# Register your models here.


User=get_user_model()

class Useradmin(admin.ModelAdmin):
    search_fields= ['email']
    list_filter=['email']
    list_display = ['email']
admin.site.register(User,Useradmin)

class SaveAdsadmin(admin.ModelAdmin):
    search_fields=['user']
    list_filter=['user']
    list_display=['user','ad']
admin.site.register(SaveAds,SaveAdsadmin)

class Subadmin(admin.ModelAdmin):
    search_fields=['user','sub_status']
    list_filter=['user','sub_status','created_at']
    list_display=['user','customer_id','subscription_id','sub_status','created_at']

admin.site.register(Subscription_details)
