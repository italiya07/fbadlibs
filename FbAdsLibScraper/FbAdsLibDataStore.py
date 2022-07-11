from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from decouple import config
import boto3
import requests
import hashlib
import uuid
import datetime
from botocore.errorfactory import ClientError
from decouple import config
import time
import pandas as pd
from datetime import timedelta

class FbAdsLibDataStore:

    def __init__(self):

        region = 'us-east-1'
        host = 'search-fbadslib-dev-vtocnlf6uhf7y24wy53x6cz2u4.us-east-1.es.amazonaws.com'
        service = 'es'
        self.bucket_name = "fbadslib-dev"
        self.index_name = 'fbadslib-dev'

        self.s3 = boto3.client("s3",
                          aws_access_key_id=config("aws_access_key_id"),
                          aws_secret_access_key=config("aws_secret_access_key"))

        awsauth = AWS4Auth(config("aws_access_key_id"), config("aws_secret_access_key"), region, service)

        self.client = OpenSearch(
                        hosts = [{'host': host, 'port': 443}],
                        http_auth = awsauth,
                        use_ssl = True,
                        verify_certs = True,
                        connection_class = RequestsHttpConnection
                        )
        
        self.es_create_index_if_not_exists(self.index_name)

    def es_create_index_if_not_exists(self,index):
        """Create the given ElasticSearch index and ignore error if it already exists"""
        try:
            self.client.indices.create(index)
        except Exception as ex:
            print(ex)
            if ex.error == 'resource_already_exists_exception':
                pass # Index already exists. Ignore.
            else: # Other exception - raise it
                raise ex
                
    def get_today(self):
        today = datetime.date.today()
        # today = (datetime.date.today() + datetime.timedelta(days=1))
        return today
        
            
    def generate_hash(self, fbAdlibItem):

        # Get Data from media URL.
        media_data=requests.get(fbAdlibItem["adMediaURL"],stream=True).raw

        # Create an Object to generate Hash From.
        data={
            'media_data':str(media_data.data),
            'headline':fbAdlibItem["headline"],
            'page_name':fbAdlibItem["pageInfo"]["name"],
            'purchase_url':fbAdlibItem["purchaseURL"],
            'displayURL':fbAdlibItem['displayURL'],
            'purchase_description':fbAdlibItem["purchaseDescription"],
            }
        
        if fbAdlibItem['adMediaType']=='video' and fbAdlibItem['adMediaThumbnail']:
            media_data=requests.get(fbAdlibItem["adMediaThumbnail"],stream=True).raw
            data['ad_media_thumbnail'] = str(media_data.data)
        
        # cobvert to Json Object to string
        a_string = str(data)

        # Generated HASH from String
        hashed_string = hashlib.sha256(a_string.encode('utf-8')).hexdigest()

        #return generated HASH.
        return hashed_string

    def create_new_ad(self, fbAdlibItem):
        today = self.get_today()
        
        # Save Ad Media to S3 Bucket
        mediaResponse = requests.get(fbAdlibItem['adMediaURL'], stream=True).raw

        if fbAdlibItem['adMediaType']=='image':
            filename = "%s.%s" % (uuid.uuid4(), 'jpeg')
        if fbAdlibItem['adMediaType']=='video':
            filename = "%s.%s" % (uuid.uuid4(), 'mp4')
        self.s3.upload_fileobj(mediaResponse, self.bucket_name, fbAdlibItem['adMediaType']+'/'+filename)

        s3_url = f'https://{self.bucket_name}.s3.amazonaws.com/'+fbAdlibItem['adMediaType']+f'/{filename}'
        fbAdlibItem['bucketMediaURL'] = s3_url
        
        # Save Thumbhnail to S3 Bucket
        if fbAdlibItem['adMediaType']=='video' and fbAdlibItem['adMediaThumbnail']:
            mediaResponse = requests.get(fbAdlibItem['adMediaThumbnail'], stream=True).raw
            filename = "%s.%s" % (uuid.uuid4(), 'jpeg')
            self.s3.upload_fileobj(mediaResponse, self.bucket_name, f'thumbnails/{filename}')
            fbAdlibItem['thumbBucketUrl'] = f'https://{self.bucket_name}.s3.amazonaws.com/thumbnails/{filename}'
        
        # Save Page Logo to S3 Bucket
        pageName = fbAdlibItem['pageInfo']['name']
        try:
            # found
            self.s3.head_object(Bucket=self.bucket_name, Key=f'pages/{pageName}.jpeg')
            fbAdlibItem['pageInfo']['bucketLogoURL'] = f'https://{self.bucket_name}.s3.amazonaws.com/pages/{pageName}.jpeg'
        except ClientError:
            # Not found
            mediaResponse = requests.get(fbAdlibItem['pageInfo']['logo'], stream=True).raw
            self.s3.upload_fileobj(mediaResponse, self.bucket_name, f'pages/{pageName}.jpeg')
            fbAdlibItem['pageInfo']['bucketLogoURL'] = f'https://{self.bucket_name}.s3.amazonaws.com/pages/{pageName}.jpeg'
        
        yesterday = today - timedelta(days = 1)
        fbAdlibItem['history'] = [{"date": (yesterday - datetime.timedelta(days=x)).strftime('%d/%m'), "noOfCopyAds": None} for x in range(29)]
        fbAdlibItem['history'].append({"date": today.strftime('%d/%m'), "noOfCopyAds": fbAdlibItem['noOfCopyAds']})
        try:
            fbAdlibItem['lastUpdatedTime'] = int(time.time() * 1000)
            fbAdlibItem['lastUpdatedDate'] = today.strftime("%d/%m/%Y")
            res=self.client.index(index=self.index_name, body=fbAdlibItem, refresh = True)
            print("Record created successfully !!!!!")
        except Exception as e:
            print("Exception Occured while creating an Ad to Elastic Search :")
            print(e)
        finally:
            return
        return res
    
    def update_all_ads(self):
        today = self.get_today()
        
        query1 = {
              "query": {
                "bool": {
                  "must_not": [
                    {
                      "term": {
                        "lastUpdatedDate": {
                          "value": today.strftime("%d/%m/%Y")
                        }
                      }
                    }
                  ]
                }
              }, 
             "script": {
               "lang":"painless",
               "inline": "ctx._source.history.add(params)",
               "params":{
                         "date":today.strftime("%d/%m"),
                         "noOfCopyAds": None
                         }}
            }
        
        try:
            query_res=self.client.update_by_query(index=self.index_name,body=query1, refresh = True)
            print("Record updated successfully !!!!!")
        except Exception as e:
            print("Exception Occured while updating an Ad to Elastic Search :")
            print(e)
        finally:
            return

        

    def update_ad(self, oldFbAdlibItem, updateQuery):
        today = self.get_today()
        print("Update Query ::::" + updateQuery)
        print("oldFbAdlibItem hash ::::" + oldFbAdlibItem["hash"])
        query1={
                "script":{
                    "inline":updateQuery,
                    "lang": "painless"
                },
                "query":{
                    "bool": {
                        "must": [
        {
          "match": {
            "hash": oldFbAdlibItem["hash"]
          }
        },
        {
          "match": {
            "status": oldFbAdlibItem['status']
          }
        },
                            {
          "match": {
            "adMediaURL": oldFbAdlibItem['adMediaURL']}
          }
      ]
                    }
                    }
            }

        try:
            query_res=self.client.update_by_query(index=self.index_name,body=query1, refresh = True)
            print("Record updated successfully !!!!!")
        except Exception as e:
            print("Exception Occured while updating an Ad to Elastic Search :")
            print(e)
        finally:
            return

    def save_ad(self,newFbAdlibItem):
        try:
            today = self.get_today()
            newFbAdlibItem["hash"]=self.generate_hash(newFbAdlibItem)
            
            print(f"Generated Hash :- {newFbAdlibItem['hash']}")

            query={
            "query": {
                "bool": {
                "must": [
                    {
                    "match": {
                        "hash": newFbAdlibItem["hash"]
                    }
                    }
                ]
                }
            }
            }

            result=self.client.search(index=self.index_name, body=query)
            
            print(f"Got the Match :- {result['hits']['hits']}")
            
            if len(result['hits']['hits']) > 0:
                """Hash Matched go for media url match"""
                for storedAdData in result['hits']['hits']:
                    storedAd = storedAdData["_source"]
                    if storedAd['adMediaURL'] == newFbAdlibItem['adMediaURL']:
                        """Media URL is also matched go for Status Check!!"""
                        print("Media URL is also matched go for Status Check!!")
                        print(f"Status is :- {storedAd['status']}")

                        if newFbAdlibItem['status'] == "Active":
                            if storedAd["status"] == 'Active':
                                """Just Update No. Of ads and finish !!"""
                                print('new --> active & old --> active |||| Just Update No. Of ads and finish !!')
                                
                                storedAd['history'][-1]['noOfCopyAds'] = newFbAdlibItem['noOfCopyAds']
                                self.update_ad(storedAd, 
                                            f"ctx._source.history={storedAd['history']};ctx._source.noOfCopyAds={newFbAdlibItem['noOfCopyAds']};ctx._source.lastUpdatedTime={int(time.time() * 1000)};ctx._source.lastUpdatedDate={today.strftime('%d/%m/%Y')}")
                            elif storedAd["status"] == 'Inactive':
                                """Make it Active and update ad count!!"""
                                print('new --> active & old --> Inactive |||| Make old Active and update ad count!!')
                                storedAd['history'][-1]['noOfCopyAds'] = newFbAdlibItem['noOfCopyAds']
                                self.update_ad(storedAd, 
                                            f"ctx._source.history={storedAd['history']};ctx._source.status='Active';ctx._source.noOfCopyAds={newFbAdlibItem['noOfCopyAds']};ctx._source.lastUpdatedTime={int(time.time() * 1000)};ctx._source.lastUpdatedDate={today.strftime('%d/%m/%Y')}")

                        elif newFbAdlibItem['status'] == "Inactive":
                            if storedAd["status"] == 'Active':
                                """Just Update No. Of ads and finish !!"""
                                print('new --> Inactive & old --> active |||| Make old Inactive and update ad count!!')
                                storedAd['history'][-1]['noOfCopyAds'] = newFbAdlibItem['noOfCopyAds']
                                self.update_ad(storedAd, 
                                            f"ctx._source.history={storedAd['history']};ctx._source.status='Inactive';ctx._source.noOfCopyAds={newFbAdlibItem['noOfCopyAds']};ctx._source.lastUpdatedTime={int(time.time() * 1000)};ctx._source.lastUpdatedDate={today.strftime('%d/%m/%Y')}")
                            elif storedAd["status"] == 'Inactive':
                                """Make it Active and update ad count!!"""
                                print('new --> Inactive & old --> Inactive |||| Just Update No. Of ads and finish !!')
                                storedAd['history'][-1]['noOfCopyAds'] = newFbAdlibItem['noOfCopyAds']
                                self.update_ad(storedAd, 
                                            f"ctx._source.history={storedAd['history']};ctx._source.noOfCopyAds={newFbAdlibItem['noOfCopyAds']};ctx._source.lastUpdatedTime={int(time.time() * 1000)};ctx._source.lastUpdatedDate={today.strftime('%d/%m/%Y')}")

                    else:
                        """Media URL is not matched now go for Status Check!!"""
                        print("Data Points are same but media url is different")
                        if storedAd["status"] == 'Active':
                            """Make Active ad as Inactive"""
                            """Create new ad"""
                            print("Make Active ad as Inactive")
                            print("Create new ad")
                            self.update_ad(storedAd, "ctx._source.status='Inactive'")
                            self.create_new_ad(newFbAdlibItem)
            else:
                self.create_new_ad(newFbAdlibItem)

            print(f"SuccessFull Data Stored for Ad :- {newFbAdlibItem['adID']}")
            self.update_all_ads()
        except Exception as ex:
            print("Exception Occured while saving ad")
            print(ex)

        return newFbAdlibItem