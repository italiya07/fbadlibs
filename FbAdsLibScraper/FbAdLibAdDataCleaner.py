import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class FbAdLibAdDataCleaner:

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

            #adDescription
            adDataToBeCleaned["adDescription"]=adDataToBeCleaned["adDescription"].replace("\n","").strip()
            
            # REST Perameters
            adDataToBeCleaned["status"]=adDataToBeCleaned["status"].strip()
            adDataToBeCleaned["adID"]=adDataToBeCleaned["adID"].strip()
            adDataToBeCleaned["adMediaURL"]=adDataToBeCleaned["adMediaURL"].strip()
            adDataToBeCleaned["adMediaType"]=adDataToBeCleaned["adMediaType"].strip()
            adDataToBeCleaned["adDescription"]=adDataToBeCleaned["adDescription"].strip()
            adDataToBeCleaned["ctaStatus"]=adDataToBeCleaned["ctaStatus"].strip()
            adDataToBeCleaned["displayURL"]=adDataToBeCleaned["displayURL"].strip()
            adDataToBeCleaned["headline"]=adDataToBeCleaned["headline"].strip()
            adDataToBeCleaned["purchaseURL"]=adDataToBeCleaned["purchaseURL"].strip()
            parsed_url = urlparse(adDataToBeCleaned["purchaseURL"])
            adDataToBeCleaned["purchaseURL"] = parse_qs(parsed_url.query)["u"][0]
            adDataToBeCleaned["pageInfo"]["name"]=adDataToBeCleaned["pageInfo"]["name"].strip()
            adDataToBeCleaned["pageInfo"]["url"]=adDataToBeCleaned["pageInfo"]["url"].strip()
            adDataToBeCleaned["pageInfo"]["logo"]=adDataToBeCleaned["pageInfo"]["logo"].strip()

            print(f"SuccessFull Data Cleaning For Ad :---{adDataToBeCleaned['adID']}")
        except Exception as ex:
            print(f"Exception Occured at Data Cleaning For Ad :---{adDataToBeCleaned['adID']}")
            print(ex)

        print("After clean ad data :", adDataToBeCleaned["noOfCopyAds"])

        return adDataToBeCleaned
