"""fbadslib URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path,include
from .views import *
from rest_framework.routers import DefaultRouter

router=DefaultRouter()
router.register('allads',getAllAds,basename="AllAds")
router.register('support',contactSupport,basename="support")
router.register('usermanager',userManager,basename="registeruser")
router.register('saveadmanager',ManageSaveAds,basename="ManageSaveAds")
router.register('adsbypage', subAllAds, basename="adsByPage" )

urlpatterns = [
    path('login/', loginview, name='Login'),
    path('logout/', logoutview , name='Logout'),
    path('forgot_password/', Forgotpasswordview , name='forgotpassword'),
    path('change_password/<str:token>', Change_password , name='change_password'),
    path('isalive/', Isalive , name='alive'),
    path('filters/',FilterView,name='FilterView'),
    path('', include(router.urls)),
]
