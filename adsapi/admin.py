from django.contrib import admin
from django.contrib.auth import get_user_model
# Register your models here.


User=get_user_model()

class Useradmin(admin.ModelAdmin):
    search_fields= ['email','username']
    list_filter=['email','username']
    list_display = ['email','username']
admin.site.register(User,Useradmin)
