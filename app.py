#Made my @undead_meme on github :) 
#7-24-25
import os
from dotenv import load_dotenv
import requests
import random

#
import logging
logging.basicConfig(filename="scraper.log", level=logging.INFO, force=True)
#
import threading
load_dotenv("keys.env")
from playwright.sync_api import sync_playwright, Page
#schedulers
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone




#turns out all this shit just wasted my time cause I thought I could go through the webapi but that only returns some fucking bullshit items and not the most recent items 
from fastapi import HTTPException, FastAPI
import time
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import json
cache_fp = "cache.json"     

def load_cache():
    global cache 
    if os.path.exists(cache_fp):
        if os.path.getsize(cache_fp) == 0:
            cache = {}
            print("Cache file is empty")
        else:
            with open(cache_fp, "r") as f:
                cache = json.load(f)
    else:
        cache = {}
        print("No filepath found")
    return cache
def save_cache():
    global cache
    print("Saving Cache")
    with open(cache_fp, "w") as f:
        json.dump(cache, f)

# Create an instance of the FastAPI class.
app = FastAPI()
# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

filter_keywords =  {"#notreal", "hangtags", "hang tags", "comes in bag", "comes in original bag", "tagged for visibility", "original tags", "ifykyk"}
#if price is less than this dont even consider
basic_price_check = 15

def return_website(search : str):
    #clean up search term 
           
    new = search.replace(" ", "+")

    return f"https://www.depop.com/search/?q={new}&_suggestion-type=recent&sort=newlyListed"
#gets the next 24 i thought it would get the first 24 but im an idiot 
def get_old_listings(search_Term):
    url = return_website(search_Term)
    with sync_playwright() as p:
            browser = p.chromium.launch(
            headless=True,
            #executable_path="\Program Files\Google\Chrome\Application\chrome.exe"  # Adjust this path
        )
            page = browser.new_page()
        #begin waitig for url that contains the API path
            with page.expect_response(lambda resp: "https://webapi.depop.com/api/v3/search/products" in resp.url , timeout=100000) as resp:
                
                print("going to url")
                page.goto(url)
                time.sleep(2)
                #if webapi is not called force it by scrolling
                
                #close cookie screen
                try:
                    #class button has the text accep 
                    locator = page.locator('button:has-text("Accept")')
                    print("Matches" , locator.count())
                    if locator.count() == 1:
                        locator.click()
                    else:
                        pass
                finally:
                    print("fuck")
                #scroll
                for _ in range(4):
                    page.mouse.wheel(0, 500)
                    time.sleep(.3)
        
            response = resp.value
            #print(resp , "\n", response)
            data = response.json()
            for product in data.get('products'):
                print(product)

def close_cookies(page : Page):
    clicked = False
    ct = 1
    while clicked == False:
        if ct > 5:
            print("ERROR CLICKING COOKKIE SCREEN")
            break
        if page.locator('button:has-text("Accept")').count() > 0:
            page.locator('button:has-text("Accept")').click()
            clicked = True
        else:
            ct += 1
            time.sleep(random.uniform(.5, 1))
        
    

def crawl_depop(search_term):
    global cache
    url = return_website(search_term)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            executable_path="\Program Files\Google\Chrome\Application\chrome.exe"  # Adjust this path
        )
        page = browser.new_page()
        page.goto(url=url)
        html = page.content()
        try:
            locator = page.locator('button:has-text("Accept")')
            print("Matches" , locator.count())
            if locator.count() == 1:
                locator.click()
            else:
                pass
        except:
            pass
        soup = BeautifulSoup(html, "html.parser")
        listings = soup.find_all('div', "styles_productCardRoot__DaYPT")
        parsed = []
        for listing in listings:
            attributes = listing.find('div', "styles_productAttributesContainer__h02Bs")
            if not attributes:
                pass
            listingDetails = {}

            brand_name= listing.find('p', "_text_bevez_41 _shared_bevez_6 _normal_bevez_51").text.strip()
            listingDetails['brand'] = brand_name

            price = listing.find('p' , "_text_bevez_41 _shared_bevez_6 _bold_bevez_47 styles_price__H8qdh").text.strip()
            listingDetails['price'] = price

            listing_link = listing.find("a", "styles_unstyledLink__DsttP")["href"]
            listingDetails['link'] = ("depop.com" + listing_link)

            listing_image = listing.find("img", "_blurImage_e5j9l_17")['src']
            listingDetails['image'] = listing_image

            parsed.append(listingDetails)
        #basic filter

        remove_indexes = []
        for i, val in reversed(list(enumerate(parsed))):
            print(cache.get(val['link']))
            if cache.get(val['link']) is not None:
                remove_indexes.append(i)
                continue
            if "omarcolon86" in val['link']: #fuck this guy
                remove_indexes.append(i)
                continue
            #print(val['brand'])
            if val['brand'] != "Chrome Hearts":
                #print("removing")
                remove_indexes.append(i)
                continue

            price_str = val['price'].replace("$", "").replace(".", "").replace("€", "").strip()
            try:
                price = int(price_str) / 100
            except ValueError:
                remove_indexes.append(i)
                continue

            if price < basic_price_check:
                remove_indexes.append(i)

        for i in remove_indexes:
            parsed.pop(i)

        #Go to individual listings now :) 
        Item_Info = []
        for item in parsed:
            cache[item['link']] = True
            item_page = browser.new_page()
            #easy to thread
              
            
            
            with item_page.expect_response(lambda resp: "https://webapi.depop.com/api/v1/product/by-slug/" in resp.url , timeout=100000000) as resp:
                item_page.goto("https://" + item['link'])
                close_cookies(item_page)

            apiInfo = resp.value.json()

            content = item_page.content()
            soup = BeautifulSoup(content, "html.parser")
            try:
                sizeCond = soup.find_all("p", "_text_bevez_41 _shared_bevez_6 _normal_bevez_51 styles_attribute__QC7gC") # if this is jewelry it will return the condition only 
            except:
                continue
            print( sizeCond)
            itemInfo = {}
            itemInfo['Price'] = item['price']
            itemInfo['brand'] = item['brand']     #Right now I'm only looking for Chrome Hearts
            itemInfo['link'] = item['link']
            for size in sizeCond:
                if "Size" in size.get_text(strip=True):
                    itemInfo['Size'] = size.get_text(strip=True)
                else:
                    itemInfo['Condition']  = size.get_text(strip=True)
            try:
                description = soup.find("p", "_text_bevez_41 _shared_bevez_6 _normal_bevez_51 styles_textWrapper__v3kxJ styles_textWrapper--collapsed__YnecK").get_text(strip=True)
            except:
                continue
            #Simple Filter 
            itemInfo['descPass'] = True
            for keyword in filter_keywords:
                if keyword in description:
                    itemInfo['descPass'] = False
            itemInfo['description'] = description
   
     
          

            #starCount = starCount / 4
            itemInfo['stars'] =apiInfo["seller_reviews"]["reviews_rating"]
            print("User has this many stars:" , itemInfo['stars'])
            itemInfo["totalReviews"] = apiInfo["seller_reviews"]["reviews_total"]
            itemInfo['productType'] = apiInfo['attributes']['product_type']
            itemInfo['items_sold'] = apiInfo['seller_activity']['items_sold']
         

            
                
                
            Item_Info.append(itemInfo)
            #make sure depop dont get me 

            
            item_page.close()
            print(itemInfo)
            time.sleep(random.randrange(1, 5))

        #Final Review of all Listings
        def confidenceRating(item):
            rating = 0.7
            item['Price'] = int(item['Price'].replace(".", "").replace("$", "").strip()) / 100
            print(item['Price'])
            #Instant Pass/Fail Criteria
            '''if item['items_sold'] > 100:
                return True
            '''
            
            if item['descPass'] == False:
                return False
            if item['Price'] < 15:
                return False
            #grade scale
            if item['stars'] < 4.4:
                rating -= .1
            if item['totalReviews'] == 0:
                rating -= .1
            #brand new stuff is more likely to be a replica
            if item['Condition'] == "Brand New":
                rating -= .2
            else:
            
                rating += .1
            
            #my estimated sweet spot
            if item['Price'] > 20 and item['Price'] < 250:
                rating += .15
            else:
                rating += .1
            if item['items_sold'] < 100 and item['items_sold'] > 50:
                rating += .2
            if rating >= 1:
                return True
            else:
                return False
            
        for item in Item_Info:
            cache[item['link']] = True
            if confidenceRating(item) == True:
                logging.info("GOOD ITEM FOUND!!!")
                alert(item=item)
        save_cache()
#idgaf its hardcoded no one else is gonna se this
webhookurl = os.getenv("webhook_url")
print("Webhook Url: ", webhookurl)
def alert(item):
    # Build a plain string (not a set!)
    content = (
        f"GOOD ITEM FOUND!\n"
        f"Price: {item.get('Price')}\n"
        f"Link: https://{item.get('link')}\n"
        f"Description: {item.get('description')}\n"
        f"Product type: {item.get('productType')}\n"
        f"@everyone"
    )

    payload = {
        "content": content,
        # Optional: ensure @everyone actually pings
        "allowed_mentions": {"parse": ["everyone"]}
    }

    try:
        r = requests.post(webhookurl, json=payload, timeout=10)
        if r.status_code >= 400:
            logging.error("Discord webhook failed: %s %s", r.status_code, r.text)
        else:
            logging.info("Alert sent: %s", item.get('link'))
    except Exception as e:
        logging.exception("Error sending alert")  # logs stacktrace



scheduler = BackgroundScheduler()
checkTime = 15 * 60 #15 Minutes
cache_file = "cache.json" 


def job():
    global cache
    try:
        logging.info(f"[{datetime.now(timezone.utc)}] Running Scrape job")
        cache = load_cache()
        crawl_depop("chrome hearts")
        save_cache()
    except Exception as e:
        print(' Error', e)
from datetime import timedelta
def startup():
    global cache
    logging.info(f"Starting up:  {datetime.now(timezone.utc)}")
    cache = load_cache()
    scheduler.add_job(job, trigger="interval", next_run_time=datetime.now(timezone.utc) + timedelta(seconds= 1), minutes= 10)
    scheduler.start()
def shutdown():
    logging.info(f"Shutting Down: {datetime.now(timezone.utc)}")
    save_cache()
    scheduler.shutdown()
    
        
import atexit
atexit.register(shutdown)



if __name__ == "__main__":
    global cache
    cache = {}
    load_cache()
    startup()
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
        #shutdown()
    #get_old_listings("Chrome Hearts")