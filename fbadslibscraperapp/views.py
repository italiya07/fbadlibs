from django.shortcuts import render
import time
from datetime import datetime
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from fbadslibscraperapp.utils.FbAdsLibScraper import *
import logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
# @ensure_csrf_cookie
def startScraper(request):
    try:
        t1 = time.perf_counter()
        logger.info(f"***********************************Scraper Start : { datetime.now().strftime('%d/%m/%Y %H:%M:%S') } ***********************")
        proxyUrls=request.data.get('proxyUrls')
        fbadslibpages=request.data.get('fbadslibpages')
        fbAdsLibScraper = FbAdsLibScraper(proxyUrls, fbadslibpages)
        fbAdsLibScraper.startScraper()
        t2 = time.perf_counter()
        logger.info(f"***********************************Scraper End : { datetime.now().strftime('%d/%m/%Y %H:%M:%S') } ***********************")
        logger.info(f'MultiThreaded Code Took:{t2 - t1} seconds')
        response=Response()
        response.data={
                "error": False,
                "data":{},
                "message": "Scraper Successfully Started !!!"
            }
        return response
    except Exception as ex:
        response.data={
                "error": True,
                "data":{},
                "message": ex
            }
        return response


    
