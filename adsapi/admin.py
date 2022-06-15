from django.contrib import admin
from django.contrib.auth import get_user_model
# Register your models here.


User=get_user_model()

class Useradmin(admin.ModelAdmin):
    search_fields= ['email']
    list_filter=['email']
    list_display = ['email']
admin.site.register(User,Useradmin)
