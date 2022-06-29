from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import boto3
import time
from webdriver_manager.chrome import ChromeDriverManager
from decouple import config
import logging
logger = logging.getLogger(__name__)
# from random_user_agent.user_agent import UserAgent
# from random_user_agent.params import SoftwareName, OperatingSystem
# import requests
# import io

class FbAdLibPageSpider:

    def __init__(self, proxylist):
        self.proxylist = proxylist
        self.proxyToBeUsed = ''
        self.maxPollingCount = 10
        self.bucket_name = "fbadslib-dev"

    def takeScreenShot(self, currentDriver, ss_name):
        session = boto3.Session(
        aws_access_key_id=config("aws_access_key_id"),
        aws_secret_access_key=config("aws_secret_access_key"),
        region_name="us-east-1"
        )
        screenshot_path = "/tmp/" + ss_name
        currentDriver.save_screenshot(screenshot_path)
        s3 = boto3.client("s3",
                          aws_access_key_id=config("aws_access_key_id"),
                          aws_secret_access_key=config("aws_secret_access_key"))
        s3.put_object(Bucket=self.bucket_name, Key=ss_name, Body=open(screenshot_path, "rb"))
    
    def get_chrome_driver_instance(self):

        # options = webdriver.ChromeOptions()
        # options.binary_location = '/opt/chrome-linux/chrome'
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument("--disable-gpu")
        # options.add_argument('--window-size=1440x626')
        # options.add_argument("--disable-extensions")
        # options.add_argument("--single-process")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--disable-dev-tools")
        # options.add_argument('--ignore-certificate-errors')
        # options.add_argument('--allow-running-insecure-content')
        # options.add_argument("--no-zygote")
        # options.add_experimental_option("useAutomationExtension", False)
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_argument("disable-popup-blocking")
        # options.add_argument("disable-notifications")

        # self.proxyToBeUsed=random.choice(self.proxylist)
        # options.add_argument('--proxy-server=%s' % self.proxyToBeUsed)

        # logger.info(f'Proxy To be Used : {self.proxyToBeUsed}')

        # # software_names = [SoftwareName.CHROME.value]
        # # operating_systems = [OperatingSystem.LINUX.value]   
        # # user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)
        # # user_agent = user_agent_rotator.get_random_user_agent()
        # # options.add_argument(f'user-agent={user_agent}')

        # driver = webdriver.Chrome(executable_path="/opt/chromedriver",options=options)
        # return driver

        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(ChromeDriverManager().install())
        return driver

    # def polling_for_driver(self, pageUrl):
    #     for count in range(self.maxPollingCount):
    #         print("No. of attempts :- " + str(count))
    #         print("pageURL scrapped :- ", pageUrl)
    #         try:
    #             currentDriver  = self.get_chrome_driver_instance()
    #             currentDriver.get(pageUrl)
    #             print("Driver Initialize successfully !!!")
    #             element = WebDriverWait(currentDriver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "_99s5")))
    #             self.takeScreenShot(currentDriver, 'pageDriver' + str(count) + '.png')
    #             print('Image Saved in S3 bucket!!!')
    #             print("Working !!!!")
    #             return currentDriver
    #         except Exception as ex:
    #             print("Not Working just remove the IP from list and proceed for next")
    #             self.proxylist.remove(self.proxyToBeUsed)
    #             self.takeScreenShot(currentDriver, 'pageDriver' + str(count) + '.png')
    #             print('Image Saved in S3 bucket!!!')
    #             print(ex)
    #             currentDriver.quit()
    #         finally:
    #             pass

    def process_page(self, pageUrl):
        print("Page URL to be scraped :- " + pageUrl)
        fbAdLibItemList = []
        try:
            currentDriver = self.get_chrome_driver_instance()
            self.takeScreenShot(currentDriver, 'pageDriverTestingNet.png')
        except Exception as ex:
            logger.info(ex)
            raise Exception(ex)
        currentDriver.get(pageUrl)
        logger.info("Get URL SuccessFull")
        try:
            # currentDriver  = self.polling_for_driver(pageUrl)
            # Wait for List of Ads
            try:
                element = WebDriverWait(currentDriver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "_99s5")))
                print(len(currentDriver.find_elements(by=By.CLASS_NAME, value="_99s5")))
                # Get List Of Ads.
                for ads in currentDriver.find_elements(by=By.CLASS_NAME, value="_99s5"):
                    fbAdlibItem = {}
                    for idx, details in enumerate(ads.find_element(by=By.CLASS_NAME, value='hv94jbsx').find_elements(by=By.CLASS_NAME, value='m8urbbhe')):
                        if idx == 0:
                            try:
                                fbAdlibItem["status"] = details.find_element(by=By.CLASS_NAME, value='nxqif72j').text
                            except Exception as e:
                                print("Exception at while status :")
                                #print(e)
                        if idx == 1: 
                            try:
                                fbAdlibItem["startDate"] = details.find_element(by=By.TAG_NAME, value='span').text
                            except Exception as e:
                                print("Exception at while startDate :")
                                #print(e)
                        if idx == 2:
                            platformList = []
                            try:
                                for platform in details.find_elements(by=By.CLASS_NAME, value='jwy3ehce'):
                                    platform_style = platform.get_attribute("style")
                                    if platform_style.__contains__('0px'):
                                        platformList.append("Facebook")
                                        # print("Facebook")
                                    if platform_style.__contains__('-19px'):
                                        platformList.append("Instagram")
                                        # print("Instagram")
                                    if platform_style.__contains__('-17px -66px'):
                                        platformList.append("Audience Network")
                                        # print("Audience Network")
                                    if platform_style.__contains__('-17px -79px'):
                                        platformList.append("Messenger")
                                        # print("Messenger")
                                fbAdlibItem["platforms"] = platformList
                            except Exception as e:
                                fbAdlibItem["platforms"] = platformList
                                #print(e)
                        if idx == 3:
                            text = details.find_element(by=By.TAG_NAME, value='span').text
                            if text.__contains__('ID'):
                                try:
                                    fbAdlibItem["adID"] = details.find_element(by=By.TAG_NAME, value='span').text.split(':')[1].strip()
                                except Exception as e:
                                    print("Exception at while adID :")
                                    #print(e)
                            # print(details.find_elements(by=By.TAG_NAME, value='span').text)
                        if idx == 4:
                            text = details.find_element(by=By.TAG_NAME, value='span').text
                            try:
                                if text.__contains__('ID'):
                                    fbAdlibItem["adID"] = text.split(':')[1].strip()
                            except Exception as e:
                                print("Exception at while adID :")
                                #print(e)
                    try:
                        text = ads.find_element(by=By.CLASS_NAME, value='hv94jbsx').find_element(by=By.CLASS_NAME, value='_9b9y')
                        if text:
                            fbAdlibItem["noOfCopyAds"] = text.find_element(by=By.TAG_NAME, value='strong').text
                            # print(text.find_elements(by=By.TAG_NAME, value='strong').text)
                    except Exception as e:
                        fbAdlibItem["noOfCopyAds"] = '0'
                        print("Exception at while noOfCopyAds :")
                        #print(e)
                    fbAdLibItemList.append(fbAdlibItem)
            except Exception as e:
                print("Exception Occured While Scrapping list of ads from page :" + pageUrl)
                print(e)
            finally:
                currentDriver.quit()
        
        except Exception as e:
            print("Exception Occured While Scrapping page :" + pageUrl)
            print(str(e))
        finally:
            print("fbAdLibItemList :::: ----")
            print(fbAdLibItemList)
            return fbAdLibItemList
