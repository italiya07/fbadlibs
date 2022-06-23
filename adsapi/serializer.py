from dataclasses import fields
from pyexpat import model
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

    def update(self,instance, validated_data):
        if "password" in validated_data:
            print("validate data....", validated_data)
            print("instance data....old", instance.password)
            password=validated_data["password"]
            instance.set_password(password)                                                              
            instance.save()
            print("instance data....", instance.password)
            validated_data.pop("password")
        print("validate data....", validated_data)
        print("instance data....", instance.password)
        return super().update(instance, validated_data)

class SaveAdsSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    class Meta:
        model=SaveAds
        fields="__all__"