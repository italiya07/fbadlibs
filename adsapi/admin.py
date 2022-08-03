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

admin.site.register(SaveAds)
admin.site.register(Subscription_details)
