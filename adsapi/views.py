from django.shortcuts import render
from rest_framework import viewsets
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from rest_framework.response import Response
import boto3
# Create your views here.

es=Elasticsearch(
    ['https://search-fbadslib-dev-vtocnlf6uhf7y24wy53x6cz2u4.us-east-1.es.amazonaws.com/'],
    http_auth=('Denis-Godhani', 'Godhani@@123'),
    )

s3_resource = boto3.resource('s3',aws_access_key_id = "AKIATXXBU2MXKGPCVQH6",aws_secret_access_key = "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")
client = boto3.client("s3",
                          aws_access_key_id="AKIATXXBU2MXKGPCVQH6",
                          aws_secret_access_key="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")



es_indice='fbadslib-dev'
es.indices.create(index=es_indice,ignore=400)
bucket_name="fbadslib-dev"

class getAllAds(viewsets.ViewSet):
    def list(self,request):
        print(es.ping())
        query={
            "size": 10000,
            "query": {
                "match_all": {}
            }
        }

        res=es.search(index=es_indice,body=query)
        data=[]
        if res["hits"]["hits"]:
            for d in res["hits"]["hits"]:
                url=str(d["_source"].get("bucketMediaURL")).replace("https://fbadslib-dev.s3.amazonaws.com/","")
                pre_signed_url = client.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name,'Key': url},
                                                  ExpiresIn=3600*24)
                print(pre_signed_url)
                d["_source"]["bucketMediaURL"]=pre_signed_url
                data.append(d["_source"])
            return Response({"data":data,"msg":"Data fetched successfully"}) 
        return Response("Data is not available")