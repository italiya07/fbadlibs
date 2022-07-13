from concurrent.futures import ThreadPoolExecutor
from FbAdLibAdDataCleaner import FbAdLibAdDataCleaner
from FbAdLibAdSpider import FbAdLibAdSpider
from FbAdLibDomainSpider import FbAdLibDomainSpider
from FbAdsLibDataStore import FbAdsLibDataStore
from datetime import timedelta


class FbAdsLibScraper:

    def __init__(self, proxyUrls, fbadslibdomains):
        self.scraperInput = { "proxyUrls" : proxyUrls, "fbadslibdomains" : fbadslibdomains }

    def startDataCleaner(self,fbAdlibItem):
        fbAdLibAdDataCleaner = FbAdLibAdDataCleaner()
        cleanedFbAdlibItem = fbAdLibAdDataCleaner.clean_data(fbAdlibItem)
        return cleanedFbAdlibItem

    def startDataStore(self,cleanedFbAdlibItem):
        fbAdsLibDataStore = FbAdsLibDataStore()
        storedFbAdlibItem = fbAdsLibDataStore.save_ad(cleanedFbAdlibItem)
        return storedFbAdlibItem

    def startAdScraper(self,combinedProxyAd):

        fbAdLibAdSpider = FbAdLibAdSpider(combinedProxyAd["activeProxies"])
        fbAdlibItem = fbAdLibAdSpider.process_ad(combinedProxyAd['fbAdlibItem'])

        cleanedFbAdlibItem = self.startDataCleaner(fbAdlibItem)
        storedFbAdlibItem  = self.startDataStore(cleanedFbAdlibItem)

        print(f"Data is successfully stored for Ad : {storedFbAdlibItem['adID']}")

    def startDomainScraper(self, combinedProxyDomain):

        fbAdLibDomainSpider = FbAdLibDomainSpider(combinedProxyDomain["activeProxies"])
        try:
            fbAdLibItemList = fbAdLibDomainSpider.process_domain(combinedProxyDomain["domain"])
            

            combinedProxyAdList = []
            for fbAdLibItem in fbAdLibItemList:
                adProxies = {}
                adProxies["activeProxies"] = combinedProxyDomain["activeProxies"]
                adProxies["fbAdlibItem"] = fbAdLibItem
                combinedProxyAdList.append(adProxies)
            

            # print(combinedProxyAdList)
            # combinedProxyAdList = [{'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '407772404648087', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '619425476273055', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '412188680951450', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '755426949212809', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '572163717960681', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '1046915255941250', 'noOfCopyAds': '3 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '571894457664395', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '1475953919514184', 'noOfCopyAds': '6 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '437851988216441', 'noOfCopyAds': '4 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 11, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '390803249813594', 'noOfCopyAds': '5 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 10, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '739007587340431', 'noOfCopyAds': '5 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 10, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '434649898541158', 'noOfCopyAds': '15 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 9, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '589702935870525', 'noOfCopyAds': '10 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 9, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '558450706014028', 'noOfCopyAds': '4 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 9, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '776947466652081', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '1071592113766729', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '3311208842491753', 'noOfCopyAds': '1 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '386132510070006', 'noOfCopyAds': '3 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '745526376591011', 'noOfCopyAds': '3 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '498134222078277', 'noOfCopyAds': '17 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '1897573780434062', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 8, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '568949827981473', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 7, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '423926079635138', 'noOfCopyAds': '9 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 7, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '821882302118251', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 7, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '1398756973978721', 'noOfCopyAds': '6 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 6, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '493546045907728', 'noOfCopyAds': '4 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 6, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '732970418024251', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 6, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '821735279194136', 'noOfCopyAds': '2 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 6, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '483262866900613', 'noOfCopyAds': '31 ads'}}, {'activeProxies': ['198.204.249.42:19002', '69.30.217.114:19001', '107.150.42.146:19017', '198.204.249.42:19020'], 'fbAdlibItem': {'domain': 'reshline.com', 'status': 'Active', 'startDate': 'Started running on Jul 5, 2022', 'platforms': ['Facebook', 'Audience Network', 'Messenger'], 'adID': '1713664265649033', 'noOfCopyAds': '1 ads'}}]
            print(f"Got All the Ads for : {combinedProxyDomain['domain']}")

            result = []
            with ThreadPoolExecutor(max_workers=30) as exe:
                result = exe.map(self.startAdScraper,combinedProxyAdList[:1])

        except Exception as ex:
            print(f'fn.startDomainScraper Exception Occured !!!')
            print(ex)
        
    def startScraper(self):

        try:
            combinedProxyDomainList = []
            for domain in self.scraperInput["fbadslibdomains"]:
                domainProxies = {}
                domainProxies["activeProxies"] = self.scraperInput["proxyUrls"]
                domainProxies["domain"]       = domain
                combinedProxyDomainList.append(domainProxies)

            with ThreadPoolExecutor(max_workers=100) as exe:
                result = exe.map(self.startDomainScraper,combinedProxyDomainList)

        except Exception as ex:
            print("Fn.startScraper Exception Occured !!!")
            print(ex)


        

