import json
from datetime import datetime

class FbAdLibAdDataCleaner:

    def clean_data(self, adDataToBeCleaned):

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
        adDataToBeCleaned["noOfCopyAds"]=adDataToBeCleaned["noOfCopyAds"].replace("ads","").strip()

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
        adDataToBeCleaned["pageInfo"]["name"]=adDataToBeCleaned["pageInfo"]["name"].strip()
        adDataToBeCleaned["pageInfo"]["url"]=adDataToBeCleaned["pageInfo"]["url"].strip()
        adDataToBeCleaned["pageInfo"]["logo"]=adDataToBeCleaned["pageInfo"]["logo"].strip()

        return adDataToBeCleaned
