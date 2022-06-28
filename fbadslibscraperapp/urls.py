from django.urls import path

from . import views

urlpatterns = [
    path('start/', views.startScraper, name='startScraper'),
]