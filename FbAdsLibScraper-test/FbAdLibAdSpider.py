import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from decouple import config
import boto3
import time
from webdriver_manager.chrome import ChromeDriverManager
import logging
logger = logging.getLogger(__name__)
# from random_user_agent.user_agent import UserAgent
# from random_user_agent.params import SoftwareName, OperatingSystem

class FbAdLibAdSpider:
    
    def __init__(self):
        # self.driver = driver
        # self.proxylist = proxylist
        # self.proxyToBeUsed = ''
        self.maxPollingCount = 25
        self.bucket_name = "fbadslib-dev"

    def takeScreenShot(self, driver, ss_name):
        screenshot_path = "/tmp/" + ss_name
        driver.save_screenshot(screenshot_path)
        s3 = boto3.client("s3",
                          aws_access_key_id=config("aws_access_key_id"),
                          aws_secret_access_key=config("aws_secret_access_key"))
        s3.put_object(Bucket=self.bucket_name, Key=ss_name, Body=open(screenshot_path, "rb"))
    
    # def get_chrome_driver_options(self):

    #     options = Options()
    #     options.binary_location = '/opt/chrome-linux/chrome'
    #     options.add_argument('--headless')
    #     options.add_argument('--no-sandbox')
    #     options.add_argument("--disable-gpu")
    #     options.add_argument('--window-size=1440x626')
    #     options.add_argument("--disable-extensions")
    #     options.add_argument("--single-process")
    #     options.add_argument("--disable-dev-shm-usage")
    #     options.add_argument("--disable-dev-tools")
    #     options.add_argument('--ignore-certificate-errors')
    #     options.add_argument('--allow-running-insecure-content')
    #     options.add_argument("--no-zygote")
    #     options.add_experimental_option("useAutomationExtension", False)
    #     options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #     options.add_argument("disable-popup-blocking")
    #     options.add_argument("disable-notifications")
    #     self.proxyToBeUsed  = random.choice(self.proxylist)
    #     options.add_argument('--proxy-server=%s' % self.proxyToBeUsed)

    #     return options

    # def polling_for_driver(self, adID):
    #     attempts = 0
    #     workingDriver = None
    #     while True:
    #         driver = None
    #         attempts = attempts + 1
    #         if attempts == self.maxPollingCount:
    #             break
    #         else:
    #             # print("Started attempts :- " + str(attempts))
    #             try:
    #                 options  = self.get_chrome_driver_options()
    #                 driver = webdriver.Chrome("/opt/chromedriver",options=options)
    #                 adUrl = f"https://www.facebook.com/ads/library/?id={adID}"
    #                 driver.get(adUrl)
    #                 element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div [contains( text(), 'See ad details')]")))
    #                 # print(f"Working { self.proxyToBeUsed }!!!!")
    #                 workingDriver = driver
    #                 break
    #             except Exception as ex:
    #                 if driver:
    #                     driver.quit()
    #                 # print(f"Not Working { self.proxyToBeUsed }!!!!")
    #                 # print(ex)
    #                 continue
    #     return workingDriver

    def process_ad(self,driver, fbAdlibItem):
        print(f"Ad Started -->  ::::  {fbAdlibItem['adID']}")
        fbAdlibItem["adMediaURL"] = ""
        fbAdlibItem["adMediaThumbnail"] = ""
        fbAdlibItem["adMediaType"] = ""
        fbAdlibItem["adDescription"] = ""
        fbAdlibItem["ctaStatus"] = ""
        fbAdlibItem["displayURL"] = ""
        fbAdlibItem["headline"]   = ""
        fbAdlibItem["purchaseDescription"] = ""
        fbAdlibItem["purchaseURL"] = ""
        pageInfo = {
            "name": "",
            "url" : "",
            "logo": "",
            "platforms":[]
        }
        fbAdlibItem["pageInfo"] = pageInfo
        try:
            adUrl = f"https://www.facebook.com/ads/library/?id={fbAdlibItem['adID']}"
            driver.get(adUrl)
            element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div [contains( text(), 'See ad details')]")))
            # driver  = self.polling_for_driver(fbAdlibItem["adID"])
            driver.find_element(by=By.XPATH, value="//div [contains( text(), 'See ad details')]").click()
            element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'effa2scm > .qi2u98y8')))
            
            for link in driver.find_element(by=By.CLASS_NAME, value='effa2scm > .qi2u98y8').find_elements(by=By.TAG_NAME, value="a"):

                try:
                    fbAdlibItem["adMediaURL"] = link.find_element(by=By.TAG_NAME, value="img").get_attribute('src')
                    fbAdlibItem["adMediaType"] = 'image'
                    break
                except Exception as e:
                    pass
                    # print("Exception while adMediaURL Image")
                    ## print(e)

            if fbAdlibItem["adMediaURL"] == "":
                try:
                    fbAdlibItem["adMediaURL"] = driver.find_element(by=By.CLASS_NAME, value='effa2scm > .qi2u98y8').find_element(by=By.TAG_NAME, value='video').get_attribute('src')
                    fbAdlibItem["adMediaThumbnail"] = driver.find_element(by=By.CLASS_NAME, value='effa2scm > .qi2u98y8').find_element(by=By.TAG_NAME, value='video').get_attribute('poster')
                    fbAdlibItem["adMediaType"] = "video"
                except Exception as e:
                    pass
                    # print("Exception while adMediaURL Video")
                    ## print(e)

            
            try:
                fbAdlibItem["adDescription"] = driver.find_element(by=By.CLASS_NAME, value="qi2u98y8.n6ukeyzl").find_element(by=By.CLASS_NAME, value='n54jr4lg ._4ik5').text
            except Exception as e:
                pass
                # print("Exception while adDescription")
                ## print(e)

            
            try:
                fbAdlibItem["ctaStatus"] = driver.find_element(by=By.CLASS_NAME, value="_8jg_").find_element(by=By.CLASS_NAME, value="duy2mlcu").text
            except Exception as e:
                pass
                # print("Exception while ctaStatus")
                ## print(e)


            try:
                for idx, info in enumerate(driver.find_element(by=By.CLASS_NAME, value="_8jg_").find_elements(by=By.CSS_SELECTOR, value="._4ik5")): 
                    if idx == 0:
                        fbAdlibItem["displayURL"] = info.text
                    if idx == 1:
                        fbAdlibItem["headline"] = info.text
                    if idx == 2:
                        fbAdlibItem["purchaseDescription"] = info.text
            except Exception as e:
                pass
                # print("Exception while Ads Headline")
                ## print(e)

        
            try:
                fbAdlibItem["purchaseURL"] = driver.find_element(by=By.CLASS_NAME, value='qi2u98y8.n6ukeyzl').find_elements(by=By.TAG_NAME, value='a')[2].get_attribute('href')
            except Exception as e:
                pass
                # print("Exception while Ads purchaseURL")
                ## print(e)

            ##### Scrape Page Info
            
            try:
                pageInfo["name"] = driver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_element(by=By.TAG_NAME, value='a').text
            except Exception as e:
                pass
                # print("Exception while pageInfo name")
                ## print(e)
            
            try:
                pageInfo["url"] = driver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_element(by=By.TAG_NAME, value='a').get_attribute('href')
            except Exception as e:
                pass
                # print("Exception while pageInfo url")
                ## print(e)
            
            try:
                pageInfo["logo"] = driver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_element(by=By.TAG_NAME, value='img').get_attribute('src')
            except Exception as e:
                pass
                # print("Exception while pageInfo logo")
                ## print(e)

            try:
                for platforms in driver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_elements(by=By.CLASS_NAME, value="hck7fp40"):
                    platform = {
                        "name":"",
                        "likes":0,
                        "followers":0,
                        "other":"",
                        "type":""
                    }
                    if platforms.text.__contains__('likes'):
                        platform["name"] = "Facebook"
                        for info in platforms.find_elements(by=By.CLASS_NAME, value="i0ppjblf"):
                            if info.text.__contains__('likes'):
                                platform["likes"] = int(info.text.split(' ')[0].replace(',', ''))
                                if info.text.__contains__('•'):
                                    platform["type"] = info.text.split('•')[1].strip()
                            else:
                                platform["other"] = info.text

                    elif platforms.text.__contains__('followers'):
                        platform["name"] = "Instagram"
                        for info in platforms.find_elements(by=By.CLASS_NAME, value="i0ppjblf"):
                            if info.text.__contains__('followers'):
                                platform["followers"] = int(info.text.split(' ')[0].replace(',', ''))
                            else:
                                platform["other"] = info.text

                    pageInfo["platforms"].append(platform)
                        
                fbAdlibItem["pageInfo"] = pageInfo
            except Exception as ex:
                pass
                # print(f"Exception while getting Platforms for ad :- {fbAdlibItem['adID']}")
            # try:
            #     line = json.dumps(fbAdlibItem.__dict__) + ","
            #     # print(line)
            #     self.file.write(line)
            # except Exception as e:
            #     # print("Error while saving data to file :")
            #     ## print(e)
        except Exception as e:
            # print(f"Exception Occured While getting Ad Details :::: {fbAdlibItem['adID']}")
            pass
            # # print(e)
            # if driver:
            #     driver.quit()
            # self.process_ad(driver,fbAdlibItem)
        finally:
            print(f"Ad Scrapped Successfully -->  ::::  {fbAdlibItem['adID']}")
            # if driver:
            #     driver.quit()
            return fbAdlibItem
            

