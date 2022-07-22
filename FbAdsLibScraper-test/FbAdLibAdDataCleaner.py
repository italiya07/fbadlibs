import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from random import randint

class FbAdLibAdDataCleaner:

    def random_with_N_digits(self,n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)

    def clean_data(self, adDataToBeCleaned):

        try:
            #Formatting Start Date.
            adDataToBeCleaned["startDate"] = adDataToBeCleaned["startDate"].replace("Started running on","").strip()
            m,d,y=adDataToBeCleaned["startDate"].split(" ")
            d= d.replace(',', '').strip()
            my_date_string = f"{m} {d} {y}"
            try:
                date_time_obj = datetime.strptime(my_date_string, '%b %d %Y')
            except:
                d,m,y=adDataToBeCleaned["startDate"].split(" ")
                d= d.replace(',', '').strip()
                my_date_string = f"{m} {d} {y}"
                date_time_obj = datetime.strptime(my_date_string, '%b %d %Y')
            adDataToBeCleaned["startDate"] = date_time_obj.strftime("%Y-%m-%d")

            #noOfCopyAds
            adDataToBeCleaned["noOfCopyAds"]=int(adDataToBeCleaned["noOfCopyAds"].replace("ads","").strip())
            # adDataToBeCleaned["noOfCopyAds"] = self.random_with_N_digits(2)
            #adDescription
            adDataToBeCleaned["adDescription"]=adDataToBeCleaned["adDescription"].replace("\n","").strip()
            
            # REST Perameters
            adDataToBeCleaned["status"]=adDataToBeCleaned["status"].strip()
            adDataToBeCleaned["adID"]=adDataToBeCleaned["adID"].strip()
            adDataToBeCleaned["adMediaURL"]=adDataToBeCleaned["adMediaURL"].strip()
            adDataToBeCleaned["adMediaThumbnail"]=adDataToBeCleaned["adMediaThumbnail"].strip()
            adDataToBeCleaned["adMediaType"]=adDataToBeCleaned["adMediaType"].strip()
            adDataToBeCleaned["adDescription"]=adDataToBeCleaned["adDescription"].strip()
            adDataToBeCleaned["ctaStatus"]=adDataToBeCleaned["ctaStatus"].strip()
            adDataToBeCleaned["displayURL"]=adDataToBeCleaned["displayURL"].strip()
            adDataToBeCleaned["headline"]=adDataToBeCleaned["headline"].strip()
            adDataToBeCleaned["purchaseURL"]=adDataToBeCleaned["purchaseURL"].strip()
            try:
                parsed_url = urlparse(adDataToBeCleaned["purchaseURL"])
                adDataToBeCleaned["purchaseURL"] = parse_qs(parsed_url.query)["u"][0]
            except Exception as ex:
                # print(f"Exception purchaseURL :-- {adDataToBeCleaned['purchaseURL']}")
                # print(ex)
                pass

            adDataToBeCleaned["pageInfo"]["name"]=adDataToBeCleaned["pageInfo"]["name"].strip()
            adDataToBeCleaned["pageInfo"]["url"]=adDataToBeCleaned["pageInfo"]["url"].strip()
            adDataToBeCleaned["pageInfo"]["logo"]=adDataToBeCleaned["pageInfo"]["logo"].strip()
        except Exception as ex:
            pass
            # print(f"Exception Occured at Data Cleaning For Ad :---{adDataToBeCleaned['adID']}")
            # print(ex)

        return adDataToBeCleaned
