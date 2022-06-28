from concurrent.futures import ThreadPoolExecutor
from fbadslibscraperapp.utils.FbAdLibPageSpider import *
from fbadslibscraperapp.utils.FbAdLibAdSpider import *
from fbadslibscraperapp.utils.FbAdLibAdDataCleaner import *
from fbadslibscraperapp.utils.FbAdsLibDataStore import *

class FbAdsLibScraper:

    def __init__(self, proxyUrls, fbadslibpages):

        self.scraperInput = { "proxyUrls" : proxyUrls, "fbadslibpages" : fbadslibpages }

    def startAdScraper(self,combinedProxyAd):
        fbAdLibAdSpider = FbAdLibAdSpider(combinedProxyAd["activeProxies"])
        fbAdlibItem = fbAdLibAdSpider.process_ad(combinedProxyAd['fbAdlibItem'])

        print("3. Got Ad Data !!!")
        print(fbAdlibItem)

        fbAdLibAdDataCleaner = FbAdLibAdDataCleaner()
        cleanedFbAdlibItem = fbAdLibAdDataCleaner.clean_data(fbAdlibItem)

        print("4. Clean Ad Data !!!")
        print(cleanedFbAdlibItem)

        fbAdsLibDataStore = FbAdsLibDataStore()
        storedFbAdlibItem = fbAdsLibDataStore.save_ad(cleanedFbAdlibItem)

        print("4. Saved Ad Data !!!")
        print(storedFbAdlibItem)

        return f'Ad with ID : {storedFbAdlibItem["adID"]} stored successfully'

    def startPageScraper(self, combinedProxyPage):
        fbAdLibPageSpider = FbAdLibPageSpider(combinedProxyPage["activeProxies"])
        fbAdLibItemList = fbAdLibPageSpider.process_page(combinedProxyPage["pageURL"])

        combinedProxyAdList = []
        for fbAdLibItem in fbAdLibItemList:
            adProxies = {}
            adProxies["activeProxies"] = combinedProxyPage["activeProxies"]
            adProxies["fbAdlibItem"] = fbAdLibItem
            combinedProxyAdList.append(adProxies)

        print("2. Collected List Of Ads !!!")
        print(combinedProxyAdList)

        result = []
        with ThreadPoolExecutor(max_workers=5) as exe:
            result = exe.map(self.startAdScraper,combinedProxyAdList)
        
    def startScraper(self):

        combinedProxyPageList = []
        for page in self.scraperInput["fbadslibpages"]:
            pageProxies = {}
            pageProxies["activeProxies"] = self.scraperInput["proxyUrls"]
            pageProxies["pageURL"]       = page
            combinedProxyPageList.append(pageProxies)

        result = []
        with ThreadPoolExecutor(max_workers=2) as exe:
            result = exe.map(self.startPageScraper,combinedProxyPageList)

