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
    path('savedad_filters/',SavedAdFilterView,name='savedad_filters'),
    # path('stripe_paymentmethod/',Stripe_Payment_Method,name='Stripe_Payment_Method'),
    # path('card/',card,name='card'),
    path('stripe_webhooks/',stripe_webhooks,name='stripe_webhooks'),
    path('create_checkout_session/',create_checkout_session,name='create_checkout_session'),
    path('cancel_subscription/',cancel_subscription,name='cancel_subscription'),
    path('fetch_payment_method/',fetch_payment_method,name='fetch_payment_method'),
    path('get_cta_status/',getCtaStatus,name='getCtaStatus'),
    # path('check_sub_status/',check_sub_status,name='check_sub_status'),
    path('', include(router.urls)),
]
