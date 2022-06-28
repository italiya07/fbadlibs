from django.shortcuts import render
import time
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from fbadslibscraperapp.utils.FbAdsLibScraper import *

@api_view(['POST'])
@permission_classes([AllowAny])
# @ensure_csrf_cookie
def startScraper(request):
    print("1. Scraper Started !!!")
    t1 = time.perf_counter()
    proxyUrls=request.data.get('proxyUrls')
    fbadslibpages=request.data.get('fbadslibpages')
    fbAdsLibScraper = FbAdsLibScraper(proxyUrls, fbadslibpages)
    fbAdsLibScraper.startScraper()
    t2 = time.perf_counter()
    print(f'MultiThreaded Code Took:{t2 - t1} seconds')
    response=Response()
    response.data={
            "error": False,
            "data":{},
            "message": "Scraper Successfully Started !!!"
        }
    return response
