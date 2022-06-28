import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import boto3
import time
from webdriver_manager.chrome import ChromeDriverManager
# from random_user_agent.user_agent import UserAgent
# from random_user_agent.params import SoftwareName, OperatingSystem

class FbAdLibAdSpider:
    
    def __init__(self, proxyList):
        self.proxylist = proxyList
        self.maxPollingCount = 10
        self.proxyToBeUsed = ''
        self.bucket_name = "fbadslib-dev"

    def takeScreenShot(self, currentDriver, ss_name):
        screenshot_path = "/tmp/" + ss_name
        currentDriver.save_screenshot(screenshot_path)
        s3 = boto3.client("s3")
        s3.put_object(Bucket=self.bucket_name, Key=ss_name, Body=open(screenshot_path, "rb"))
    
    def get_chrome_driver_instance(self):
        options = webdriver.ChromeOptions()
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
        options.add_experimental_option("useAutomationExtension", False)  # Adding Argument to Not Use Automation Extension
        options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Excluding enable-automation Switch
        options.add_argument("disable-popup-blocking")
        options.add_argument("disable-notifications")
        self.proxyToBeUsed=random.choice(self.proxylist)
        options.add_argument('--proxy-server=%s' % self.proxyToBeUsed)

        # software_names     = [SoftwareName.CHROME.value]
        # operating_systems  = [OperatingSystem.LINUX.value]   
        # user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)
        # user_agent = user_agent_rotator.get_random_user_agent()
        # options.add_argument(f'user-agent={user_agent}')

        print(self.proxyToBeUsed)
        driver = webdriver.Chrome(executable_path="/opt/chromedriver",options=options)
        return driver
        # chrome_options = webdriver.ChromeOptions()
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        # driver = webdriver.Chrome(ChromeDriverManager().install())
        # return driver

    # def polling_for_driver(self, fbAdlibItem):
    #     for count in range(self.maxPollingCount):
    #         print(count)
    #         try:
    #             adUrl = "https://www.facebook.com/ads/library/?id=" + fbAdlibItem["adID"]
    #             # adUrl = "https://www.google.com/"
    #             print("adURL scrapped :- ", adUrl)
    #             detailedDriver  = self.get_chrome_driver_instance()
    #             detailedDriver.get(adUrl)
    #             element = WebDriverWait(detailedDriver, 60).until(EC.presence_of_element_located((By.XPATH, "//div [contains( text(), 'See ad details')]")))
    #             print("Working !!!!")
    #             # time.sleep(120)
    #             # self.takeScreenShot(detailedDriver, 'adDriverSuccess' + str(count) + '.png')
    #             print('Image Saved in S3 bucket!!!')
    #             # time.sleep(120)
    #             # self.takeScreenShot(detailedDriver, 'adDriver' + str(count) + '.png')
    #             # screenshot_filename = "adsScraper.png"
    #             # screenshot_path = "/tmp/" + screenshot_filename
    #             # detailedDriver.save_screenshot(screenshot_path)
    #             # s3 = boto3.client("s3")
    #             # s3.put_object(Bucket="fbadlibtest", Key=str(count) + '.png', Body=open(screenshot_path, "rb"))
    #             return detailedDriver
    #         except Exception as ex:
    #             print("Not Working just remove the IP from list and proceed for next")
    #             # self.takeScreenShot(detailedDriver, str(fbAdlibItem["adID"]) + "_Failure_" +  str(count) + '.png')
    #             # print('Image Saved in S3 bucket!!!')
    #             self.proxylist.remove(self.proxyToBeUsed)
    #             detailedDriver.quit()
    #             print(ex)
    #             # pass
    #         finally:
    #             # self.takeScreenShot(detailedDriver, 'adDriverFinal' + str(count) + '.png')
    #             # detailedDriver.quit()
    #             # break
    #             pass


    def process_ad(self, fbAdlibItem):
        fbAdlibItem["adMediaURL"] = ""
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
            "logo": ""
        }
        fbAdlibItem["pageInfo"] = pageInfo

        print("adURL scrapped :- ", fbAdlibItem["adID"])
        detailedDriver  = self.get_chrome_driver_instance()
        adUrl = "https://www.facebook.com/ads/library/?id=" + fbAdlibItem["adID"]
        detailedDriver.get(adUrl)

        try:
            element = WebDriverWait(detailedDriver, 60).until(EC.presence_of_element_located((By.XPATH, "//div [contains( text(), 'See ad details')]")))
            detailedDriver.find_element(by=By.XPATH, value="//div [contains( text(), 'See ad details')]").click()
            element = WebDriverWait(detailedDriver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'effa2scm > .qi2u98y8')))
            # self.takeScreenShot(detailedDriver, str(fbAdlibItem["adID"]) + "_Success" + '.png')
            print("Hello")
            print(detailedDriver.find_element(by=By.CLASS_NAME, value='effa2scm > .qi2u98y8'))
            
            for link in detailedDriver.find_element(by=By.CLASS_NAME, value='effa2scm > .qi2u98y8').find_elements(by=By.TAG_NAME, value="a"):

                try:
                    fbAdlibItem["adMediaURL"] = link.find_element(by=By.TAG_NAME, value="img").get_attribute('src')
                    fbAdlibItem["adMediaType"] = 'image'
                    break
                except Exception as e:
                    print("Exception while adMediaURL Image")
                    #print(e)

            if fbAdlibItem["adMediaURL"] == "":
                try:
                    fbAdlibItem["adMediaURL"] = detailedDriver.find_element(by=By.CLASS_NAME, value='effa2scm > .qi2u98y8').find_element(by=By.TAG_NAME, value='video').get_attribute('src')
                    fbAdlibItem["adMediaType"] = "video"
                except Exception as e:
                    print("Exception while adMediaURL Video")
                    #print(e)

            
            try:
                fbAdlibItem["adDescription"] = detailedDriver.find_element(by=By.CLASS_NAME, value="qi2u98y8.n6ukeyzl").find_element(by=By.CLASS_NAME, value='n54jr4lg ._4ik5').text
            except Exception as e:
                print("Exception while adDescription")
                #print(e)

            
            try:
                fbAdlibItem["ctaStatus"] = detailedDriver.find_element(by=By.CLASS_NAME, value="_8jg_").find_element(by=By.CLASS_NAME, value="duy2mlcu").text
            except Exception as e:
                print("Exception while ctaStatus")
                #print(e)


            try:
                for idx, info in enumerate(detailedDriver.find_element(by=By.CLASS_NAME, value="_8jg_").find_elements(by=By.CSS_SELECTOR, value="._4ik5")): 
                    if idx == 0:
                        fbAdlibItem["displayURL"] = info.text
                    if idx == 1:
                        fbAdlibItem["headline"] = info.text
                    if idx == 2:
                        fbAdlibItem["purchaseDescription"] = info.text
            except Exception as e:
                print("Exception while Ads Headline")
                #print(e)

        
            try:
                fbAdlibItem["purchaseURL"] = detailedDriver.find_element(by=By.CLASS_NAME, value='qi2u98y8.n6ukeyzl').find_elements(by=By.TAG_NAME, value='a')[2].get_attribute('href')
            except Exception as e:
                print("Exception while Ads purchaseURL")
                #print(e)

            ##### Scrape Page Info
            
            try:
                pageInfo["name"] = detailedDriver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_element(by=By.TAG_NAME, value='a').text
            except Exception as e:
                print("Exception while pageInfo name")
                #print(e)
                pageInfo["name"] = ""
            
            try:
                pageInfo["url"] = detailedDriver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_element(by=By.TAG_NAME, value='a').get_attribute('href')
            except Exception as e:
                print("Exception while pageInfo url")
                #print(e)
                pageInfo["url"] = ""
            
            try:
                pageInfo["logo"] = detailedDriver.find_element(by=By.CLASS_NAME, value="jbmj41m4").find_element(by=By.TAG_NAME, value='img').get_attribute('src')
            except Exception as e:
                print("Exception while pageInfo logo")
                #print(e)
                pageInfo["logo"] = ""

            fbAdlibItem["pageInfo"] = pageInfo
            # try:
            #     line = json.dumps(fbAdlibItem.__dict__) + ","
            #     print(line)
            #     self.file.write(line)
            # except Exception as e:
            #     print("Error while saving data to file :")
            #     #print(e)

            print("4. Ads Data Scrapped!!!")
            print(fbAdlibItem)
        except Exception as ex:
            print(ex)
        finally:
            detailedDriver.quit()
            return fbAdlibItem
            

