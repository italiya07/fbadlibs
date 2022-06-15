from dataclasses import fields
from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User=get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields="__all__"
        extra_kwargs = {
            'password': {'write_only': True},
            "is_active": {'read_only': True},
            "is_staff": {'read_only': True},
            "is_superuser": {'read_only': True}
        }
        
    def create(self, validated_data):
        password=validated_data["password"]
        obj=User.objects.create(**validated_data)
        obj.set_password(password)
        obj.save()
        return obj