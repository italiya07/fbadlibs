import time
import datetime
from FbAdsLibScraper import FbAdsLibScraper
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from decouple import config
from datetime import timedelta

def get_today():
    # today = datetime.date.today()
    today = (datetime.date.today() + datetime.timedelta(days=0))
    return today

def update_all_ads():
    region = 'us-east-1'
    host = 'search-fbadslib-dev-vtocnlf6uhf7y24wy53x6cz2u4.us-east-1.es.amazonaws.com'
    service = 'es'
    index_name = 'fbadslib-dev'
    awsauth = AWS4Auth(config("aws_access_key_id"), config("aws_secret_access_key"), region, service)
    client = OpenSearch(
                        hosts = [{'host': host, 'port': 443}],
                        http_auth = awsauth,
                        use_ssl = True,
                        verify_certs = True,
                        connection_class = RequestsHttpConnection
                        )
    today = get_today()
    
    query1 = {
            "query": {
            "bool": {
                "must_not": [
                {
                    "match": {
                        "lastUpdatedDate.keyword": today.strftime("%d/%m/%Y")
                    }
                }
                ]
            }
            }, 
            "script": {
            "lang":"painless",
            "inline": "ctx._source.history.add(params)",
            "params":{
                        "date":today.strftime("%d/%m"),
                        "noOfCopyAds": None
                        }}
        }
    
    try:
        query_res=client.update_by_query(index=index_name,body=query1, refresh = True)
        # print(query_res)
        # print("Record updated successfully !!!!!")
    except Exception as e:
        pass
        # print("Exception Occured while updating an Ad to Elastic Search :")
        # print(e)
    finally:
        return

try:
    t1 = time.perf_counter()
    print(f"***********************************Scraper Start : { datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S') } ***********************")
    proxyUrls=[
        '198.204.249.42:19002', 
        '69.30.217.114:19001', 
        '107.150.42.146:19017', 
        '198.204.249.42:19020'
    ]
    fbadslibdomains=[
            # "conoreal.com",
            # "mysticridges.com",
            # "fitmywellness.shop",
            # "pingpongfun.com",
            # "buytoughtrimmer.com",
            # "glassywhite.com",
            # "ykcengine.com",
            # "ottowhale.com",
            # "evenueshop.com",
            # "newgadgetst.com",
            # "unicetoo.com",
            # "miwantshop.com",
            # "adoracy.com",
            # "practycal.co",
            # "accidentbuy.com", 
            # "reshline.com",  
            # "youngdaynow.com",
            # "buywighere.com",
            # "timelessnova.com",
            # "usimaginever.com",
            # "classfetm.com",
            # "glocable.com",
            # "helloaza.com",
            # "verveelite.com",
            # "ustorepia.com",
            # "molnyonon.com", 
            # "topmobacc.com",
            # "mfelectrics.com", 
            # "bestshoppingus.com",
            # "balabella.com", 
            # "hazelwagon.com",
            # "amgomall.com", 
            # "pastaoppa.com",
            # "superbuyershow.com",
            # "traegoods.com",
            # "hotmobacc.com",
            # "lightsaberchopsticks.com",
            # "earthlycosy.com",
            # "culticate.com",
            # "goldenbeee.com",
            # "giftpockets.com",
            # "choochoochoco.com",
            # "topsmartproducts4u.com",
            # "homezy.com.au",
            # "LampBoom.com",
            # "mmpeepz.com",
            # "neefty.co",
            # "blacktend.com",
            # "smoothspine.com",
            # "shopvespani.co",
            # "homeychoicest.com",
            # "getyourbelongs.com",
            # "pumalover.com",
            # "newamazingtrends.com",
            # "shopnatic.com",
            # "selven.co.uk",
            # "beyood.com",
            # "newcici.com",
            # "swankinshops.com",
            # "lestylishpet.com",
            # "brandcentric.shop",
            # "pineapplea.com",
            # "fonfony.com",
            # "aubreyandclaudia.com",
            # "pabenco.com",
            # "favorfound.com",
            # "usawishingoal.com",
            # "sesameoilwa.com",
            # "babegogo.com",
            # "shazulee.com",
            # "mivimall.com",
            # "arlodesire.com",
            # "petmodstore.com",
            # "shoppingdeer.com",
            # "olygaywawa.com",
            # "thelioncomes.com",
            # "materiol.com",
            # "powertoneco.com",
            # "dailyflex.co",
            # "gymfiti.com",
            # "topmorry.com",
            # "oasiszephyr.com",
            # "beyondmats.com",
            # "glassylilac.com",
            # "dorribo.com",
            # "lilydealstore.com",
            # "solegg.com",
            # "njordoutdoors.com",
            # "amazingbun.com",
            # "leveauxdesign.com",
            # "bluseahorse.com",
            # "callistercanoe.com",
            # "fancyberrie.com",
            # "Cuplie.com",
            # "ofertas.innovachollos.com",
            # "bikedescent.store",
            # "dermay.com",
            # "garishpigs.com",
            # "nickboli.com",
            # "inspiretrendz.com",
            # "mshopo.com",
            # "ferristale.co.uk",
            # "conoreal.com",
            # "createmusic.fm",
            # "bestsolarlighting"
            # "ottowhale.com",
            "reshline.com",
          ]
    fbAdsLibScraper = FbAdsLibScraper(proxyUrls, fbadslibdomains)
    fbAdsLibScraper.startScraper()
    t2 = time.perf_counter()
    update_all_ads()
    print(f"***********************************Scraper End : { datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S') } ***********************")
    print(f'Scraper Took:{t2 - t1} seconds')
except Exception as ex:
    pass
    # print("Exception Occured While Scrapping :-")
    # print(ex)


# try:
#     t1 = time.perf_counter()
#     # print(f"***********************************Scraper Start : { datetime.now().strftime('%d/%m/%Y %H:%M:%S') } ***********************")
#     cleanedFbAdlibItem = {'status': 'Active', 'startDate': '2022-06-08', 'platforms': ['Facebook', 'Facebook', 'Audience Network', 'Messenger'], 'adID': '3219422001610117', 'noOfCopyAds': '2', 'adMediaURL': 'https://video-lax3-1.xx.fbcdn.net/v/t42.1790-2/10000000_425870779340674_1677875396473456968_n.?_nc_cat=110&ccb=1-7&_nc_sid=cf96c8&_nc_ohc=WVQMTa6ZNa4AX-kVeZK&_nc_ht=video-lax3-1.xx&oh=00_AT-MOoZNcH6Ee3DBXJhH1UGjVp2kiEblC935HzCDA5NAmg&oe=62BD780C', 'adMediaType': 'video', 'adDescription': '??Tired of Your Trimmer Being too Weak to Cut Tough Weeds???Transform Your Weeder to A Beast That Slices Through Anything!Get it here????https://www.culticate.com/6Trimmer', 'ctaStatus': 'Shop now','displayURL': 'WWW.CULTICATE.COM', 'headline': '??50% Off Limited Time Only UNIVERSAL 6-Steel Razors Trimmer Head', 'purchaseDescription': '', 'purchaseURL': 'https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.              culticate.com%2Fproducts%2F6-steel-blades-trimmer-head&h=AT082mYqvDlkddTe_OOa2ScrH65eGkTEKGKtKkJki_5_4DN0UEiOF8worQhubYDmh49meO4cwcrmvXBvi-pzzbjk4t4Q2uynNDLeYm4                                     DmomPWd3c9ZcLozMgI4gB9gYsBLzkq0VusYvt3Q', 'pageInfo': {'name': 'Culticate', 'url': 'https://www.facebook.com/Culticate/', 'logo': 'https://scontent-lax3-2.xx.fbcdn.net/v/t39.354266/286938011_965862330775799_450487203209140268_n.jpg?stp=dst-jpg_s60x60&_nc_cat=111&ccb=1-7&_nc_sid=cf96c8&_nc_ohc=pOglLCUd3BUAX_H4Uyw&_nc_ht=scontent-lax3-2.xx&oh=00_AT9NtMZklgqWPMdbUK1sGrEsI3J4K-jVm7X8XLaSmzq81g&oe=62C252D0'}}
#     fbAdsLibDataStore = FbAdsLibDataStore()
#     storedFbAdlibItem = fbAdsLibDataStore.save_ad(cleanedFbAdlibItem)
#     t2 = time.perf_counter()
#     # print(f"***********************************Scraper End : { datetime.now().strftime('%d/%m/%Y %H:%M:%S') } ***********************")
#     # print(f'MultiThreaded Code Took:{t2 - t1} seconds')
# except Exception as ex:
#     # print("Exception While Scrapping :-")
#     # print(ex)




