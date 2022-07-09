from concurrent.futures import ThreadPoolExecutor
from FbAdLibAdDataCleaner import FbAdLibAdDataCleaner
from FbAdLibAdSpider import FbAdLibAdSpider
from FbAdLibDomainSpider import FbAdLibDomainSpider
from FbAdsLibDataStore import FbAdsLibDataStore

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

            print(f"Got All the Ads for : {combinedProxyDomain['domain']}")

            result = []
            with ThreadPoolExecutor(max_workers=30) as exe:
                result = exe.map(self.startAdScraper,combinedProxyAdList)

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


        

