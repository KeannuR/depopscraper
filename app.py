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
            if cache.get(val['link']) is None:
                continue
            if val['brand'] != "Chrome Hearts":
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
        for item in parsed:
            
            item_page = browser.new_page()
            item_page.goto("https://" + item['link'], wait_until='load')
            


            #make sure depop dont get me 
            try:
                page.locator('button:has-text("Accept")').click()
            except:
                pass
            content = item_page.content()
            sizeCond = soup.find("p", "_text_bevez_41 _shared_bevez_6 _normal_bevez_51 styles_attribute__QC7gC").text().strip()
            print(sizeCond)
            
            time.sleep(random.randrange(1, 5))

    


        
        


if __name__ == "__main__":
    global cache
    cache = {}
    load_cache()
    crawl_depop("chrome hearts")
    #get_old_listings("Chrome Hearts")
