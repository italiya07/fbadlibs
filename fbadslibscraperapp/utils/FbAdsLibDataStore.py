from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import requests
import hashlib
import uuid

class FbAdsLibDataStore:

    def __init__(self):

        region = 'us-east-1'
        host = 'search-fbadslib-dev-vtocnlf6uhf7y24wy53x6cz2u4.us-east-1.es.amazonaws.com'
        service = 'es'
        self.bucket_name = "fbadslib-dev"
        self.index_name = 'fbadslib-dev-test'
        
        credentials = boto3.Session().get_credentials()

        self.s3 = boto3.client("s3")
        # self.s3 = boto3.client(
        #     service_name='s3',
        #     region_name=region,
        #     aws_access_key_id=credentials.access_key,
        #     aws_secret_access_key=credentials.secret_key
        #     )

        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

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
            
    def generate_hash(self, fbAdlibItem):

        # Get Data from media URL.
        media_data=requests.get(fbAdlibItem["adMediaURL"],stream=True).raw

        # Create an Object to generate Hash From.
        data={
            'media_data':str(media_data.data),
            'headline':fbAdlibItem["headline"],
            'page_name':fbAdlibItem["pageInfo"]["name"],
            'ad_id':fbAdlibItem["adID"],
            'purchase_url':fbAdlibItem["purchaseURL"],
            'displayURL':fbAdlibItem['displayURL'],
            'purchase_description':fbAdlibItem["purchaseDescription"],
            }
        
        # cobvert to Json Object to string
        a_string = str(data)

        # Generated HASH from String
        hashed_string = hashlib.sha256(a_string.encode('utf-8')).hexdigest()

        #return generated HASH.
        return hashed_string

    def create_new_ad(self, fbAdlibItem):
        mediaResponse = requests.get(fbAdlibItem['adMediaURL'], stream=True).raw

        if fbAdlibItem['adMediaType']=='image':
            filename = "%s.%s" % (uuid.uuid4(), 'jpeg')
        if fbAdlibItem['adMediaType']=='video':
            filename = "%s.%s" % (uuid.uuid4(), 'mp4')
        self.s3.upload_fileobj(mediaResponse, self.bucket_name, fbAdlibItem['adMediaType']+'/'+filename)

        s3_url = f'https://{self.bucket_name}.s3.amazonaws.com/'+fbAdlibItem['adMediaType']+f'/{filename}'
        fbAdlibItem['bucketMediaURL'] = s3_url
        
        try:
            res=self.client.index(index=self.index_name, body=fbAdlibItem, refresh = True)
            print("Record created successfully !!!!!")
        except Exception as e:
            print("Exception Occured while creating an Ad to Elastic Search :")
            print(e)
        finally:
            return
        return res

    def update_ad(self, oldFbAdlibItem, updateQuery):
        print("Update Query ::::" + updateQuery)
        print("oldFbAdlibItem adID ::::" + oldFbAdlibItem["adID"])
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
                            "adID": oldFbAdlibItem["adID"]
                            }
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
        newFbAdlibItem["hash"]=self.generate_hash(newFbAdlibItem)

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
        
        if len(result['hits']['hits']) > 0:
            """Hash Matched go for media url match"""
            for storedAdData in result['hits']['hits']:
                storedAd = storedAdData["_source"]
                if storedAd['adMediaURL'] == newFbAdlibItem['adMediaURL']:
                    """Media URL is also matched go for Status Check!!"""
                    if storedAd["status"] == 'Active':
                        """Just Update No. Of ads and finish !!"""
                        self.update_ad(storedAd, "ctx._source.noOfCopyAds={}".format(newFbAdlibItem['noOfCopyAds']))
                    elif storedAd["status"] == 'Inactive':
                        """Make it Active and update ad count!!"""
                        self.update_ad(storedAd, "ctx._source.status='Active';ctx._source.noOfCopyAds={}".format(newFbAdlibItem['noOfCopyAds']))
                else:
                    """Media URL is not matched now go for Status Check!!"""
                    if storedAd["status"] == 'Active':
                        """Make Active ad as Inactive"""
                        """Create new ad"""
                        self.update_ad(storedAd, "ctx._source.status=='Inactive'")
                        self.create_new_ad(newFbAdlibItem)
        else:
            self.create_new_ad(newFbAdlibItem)

        return newFbAdlibItem