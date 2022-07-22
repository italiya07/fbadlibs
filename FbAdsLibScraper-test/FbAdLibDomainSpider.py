from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import boto3
from webdriver_manager.chrome import ChromeDriverManager
from decouple import config
from selenium.webdriver.chrome.options import Options
import sys
from FbAdLibAdDataCleaner import FbAdLibAdDataCleaner
from FbAdLibAdSpider import FbAdLibAdSpider
from FbAdsLibDataStore import FbAdsLibDataStore

class FbAdLibDomainSpider:

    def __init__(self, proxylist):
        self.proxylist = proxylist
        self.proxyToBeUsed = ''
        self.maxPollingCount = 25
        self.bucket_name = "fbadslib-dev"

    def takeScreenShot(self, driver, ss_name):
        screenshot_path = "/tmp/" + ss_name
        driver.save_screenshot(screenshot_path)
        s3 = boto3.client("s3",
                          aws_access_key_id=config("aws_access_key_id"),
                          aws_secret_access_key=config("aws_secret_access_key"))
        s3.put_object(Bucket=self.bucket_name, Key=ss_name, Body=open(screenshot_path, "rb"))
    
    def get_chrome_driver_options(self):

        options = Options()
        options.binary_location = '/opt/chrome-linux/chrome'
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-gpu")
        options.add_argument('--window-size=1440x626')
        options.add_argument("--disable-extensions")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument("--no-zygote")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("disable-popup-blocking")
        options.add_argument("disable-notifications")
        self.proxyToBeUsed  = random.choice(self.proxylist)
        options.add_argument('--proxy-server=%s' % self.proxyToBeUsed)

        return options

    def polling_for_driver(self, domain):
        attempts = 0
        workingDriver = None
        while True:
            driver = None
            attempts = attempts + 1
            if attempts == self.maxPollingCount:
                break
            else:
                # print("Started attempts :- " + str(attempts))
                try:
                    options  = self.get_chrome_driver_options()
                    driver = webdriver.Chrome("/opt/chromedriver",options=options)
                    driver.get(f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q={domain}")
                    try:
                        element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[text()='0 results']")))
                        print(f"Got 0 ads for domain: {domain}")
                        break
                    except:
                        try:
                            element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "_99s5")))
                            print(f"Working Proxy for {domain} is :- { self.proxyToBeUsed }!!!!")
                            workingDriver = driver
                            break
                        except Exception as ex:
                            if driver:
                                driver.quit()
                            print(f"Working Proxy for {domain} is :- { self.proxyToBeUsed }!!!!")
                            # # print(ex)
                            continue
                except Exception as ex:
                    if driver:
                        driver.quit()
                    # print(f"Not Working { self.proxyToBeUsed }!!!!")
                    # # print(ex)
                    continue
        return workingDriver            
            
    def startDataCleaner(self,fbAdlibItem):
        fbAdLibAdDataCleaner = FbAdLibAdDataCleaner()
        cleanedFbAdlibItem = fbAdLibAdDataCleaner.clean_data(fbAdlibItem)
        return cleanedFbAdlibItem

    def startDataStore(self,cleanedFbAdlibItem):
        fbAdsLibDataStore = FbAdsLibDataStore()
        storedFbAdlibItem = fbAdsLibDataStore.save_ad(cleanedFbAdlibItem)
        return storedFbAdlibItem

    def startAdScraper(self,driver, fbAdlibItem):

        fbAdLibAdSpider = FbAdLibAdSpider()
        fbAdlibItem = fbAdLibAdSpider.process_ad(driver, fbAdlibItem)

        cleanedFbAdlibItem = self.startDataCleaner(fbAdlibItem)
        storedFbAdlibItem  = self.startDataStore(cleanedFbAdlibItem)

        # print(f"Data is successfully stored for Ad : {storedFbAdlibItem['adID']}")
    def process_domain(self, domain):
        # print("Domain to be scraped :- " + domain)
        fbAdLibItemList = []
        driver = None
        try:
            driver = self.polling_for_driver(domain)
            for ads in driver.find_elements(by=By.CLASS_NAME, value="_99s5"):

                fbAdlibItem = {
                    "domain": domain,
                    "status": '',
                    "startDate":'',
                    "platforms":[],
                    "adID":'',
                    "noOfCopyAds":"1 ads"
                }

                for idx, details in enumerate(ads.find_element(by=By.CLASS_NAME, value='hv94jbsx').find_elements(by=By.CLASS_NAME, value='m8urbbhe')):
                    if idx == 0:
                        try:
                            fbAdlibItem["status"] = details.find_element(by=By.CLASS_NAME, value='nxqif72j').text
                        except Exception as e:
                            pass
                            # print("Exception at while status :")
                            ## print(e)
                    if idx == 1: 
                        try:
                            fbAdlibItem["startDate"] = details.find_element(by=By.TAG_NAME, value='span').text
                        except Exception as e:
                            pass
                            # print("Exception at while startDate :")
                            ## print(e)
                    if idx == 2:
                        platformList = []
                        try:
                            for platform in details.find_elements(by=By.CLASS_NAME, value='jwy3ehce'):
                                platform_style = platform.get_attribute("style")
                                if platform_style.__contains__('0px'):
                                    platformList.append("Facebook")
                                    # # print("Facebook")
                                if platform_style.__contains__('-19px'):
                                    platformList.append("Instagram")
                                    # # print("Instagram")
                                if platform_style.__contains__('-17px -66px'):
                                    platformList.append("Audience Network")
                                    # # print("Audience Network")
                                if platform_style.__contains__('-17px -79px'):
                                    platformList.append("Messenger")
                                    # # print("Messenger")
                            fbAdlibItem["platforms"] = platformList
                        except Exception as e:
                            fbAdlibItem["platforms"] = platformList
                            ## print(e)
                    if idx > 2:
                        text = details.find_element(by=By.TAG_NAME, value='span').text
                        if text.__contains__('ID'):
                            try:
                                fbAdlibItem["adID"] = details.find_element(by=By.TAG_NAME, value='span').text.split(':')[1].strip()
                            except Exception as e:
                                pass
                                # print("Exception at while adID :")
                                ## print(e)

                try:
                    text = ads.find_element(by=By.CLASS_NAME, value='hv94jbsx').find_element(by=By.CLASS_NAME, value='_9b9y')
                    if text:
                        fbAdlibItem["noOfCopyAds"] = text.find_element(by=By.TAG_NAME, value='strong').text
                except Exception as e:
                    pass
                    # print("Exception at noOfCopyAds :--")
                    ## print(e)

                try:
                    ads.find_element(by=By.XPATH, value="// *[contains(text(),'we cannot show you this ad')]")
                    # print("we cannot show you this ad")
                except:
                    fbAdLibItemList.append(fbAdlibItem)

            print(f"Got {len(fbAdLibItemList)} no of ads for domain {domain}")
            for item in fbAdLibItemList[:2]:
                self.startAdScraper(driver, item)

            print(f"Domain scraped successfully :- {domain}")

        except Exception as e:
            # print(f"Exception Occured While getting list of ads from domain :::: {domain}")
            # # print(e)
            if driver:
                driver.quit()
        finally:
            # print(f"Got List Of Ads for a Domain  ::::  {domain}")
            if driver:
                driver.quit()
            return fbAdLibItemList
