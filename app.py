#Made my @undead_meme on github :) 
#7-24-25
import os
from dotenv import load_dotenv
import requests
import random
load_dotenv("keys.env")
from playwright.sync_api import sync_playwright, Page
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

filter_keywords =  {"#notreal", "hangtags", "hang tags", "comes in bag", "comes in original bag", "tagged for visibility", "original tags "}
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
            headless=False,
            executable_path="\Program Files\Google\Chrome\Application\chrome.exe"  # Adjust this path
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
                except:
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
            if cache.get(val['link']) is not None:
                continue
            print(val['brand'])
            if val['brand'] != "Chrome Hearts":
                print("removing")
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
            item_page.goto("https://" + item['link'], wait_until='load')
            

            close_cookies(item_page)

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
            #Star Info:
            try:
                stars = soup.find_all("svg", "styles_stars__Ca377")
            except:
                continue
            starCount = 0

            for star in stars: 
                if star.find('title').text == "Full Star":
                    starCount += 1 
                if star.find('title').text == "Half Star":
                    starCount =+ 0.5
            starCount = starCount / 4
            itemInfo['Stars'] = starCount


            item_page.mouse.wheel(0, 400)
            time.sleep(random.randrange(1,2) / 2 ) 

            try: 
                reviewCount = soup.find("p", "_text_bevez_41 _shared_bevez_6 _normal_bevez_51")
            except:
                continue
            print(reviewCount.get_text())
                
            Item_Info.append(itemInfo)
            #make sure depop dont get me 

            #item_page.close()
            time.sleep(random.randrange(1, 5))
        #Final Review of all Listings
        def confidenceRating(item):
            pass
        for item in Item_Info:
            if itemInfo['Condition'] == "Brand New":
                continue
                


    


        
        


if __name__ == "__main__":
    global cache
    cache = {}
    load_cache()
    crawl_depop("chrome hearts")
    #get_old_listings("Chrome Hearts")
