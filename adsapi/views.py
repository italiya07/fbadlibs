from django.shortcuts import render
from rest_framework import viewsets
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from rest_framework.response import Response
# Create your views here.

es=Elasticsearch(
    ['https://search-fbadslib-dev-vtocnlf6uhf7y24wy53x6cz2u4.us-east-1.es.amazonaws.com/'],
    http_auth=('Denis-Godhani', 'Godhani@@123'),
    )

es.indices.create(index='fbadslib-dev',ignore=400)

class getAllAds(viewsets.ViewSet):
    def list(self,request):
        print(es.ping())
        query={
            "size": 10000,
            "query": {
                "match_all": {}
            }
        }

        res=es.search(index="scraping_project",body=query)
        data=[]
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                data.append(d["_source"])
            return Response({"data":data,"msg":"Data fetched successfully"}) 
        return Response("Data is not available")

