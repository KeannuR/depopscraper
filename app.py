#Made my @undead_meme on github :) 
#7-24-25
import os
from dotenv import load_dotenv
import requests
load_dotenv("keys.env")
from playwright.sync_api import sync_playwright, Page
#turns out all this shit just wasted my time cause I thought I could go through the webapi but that only returns some fucking bullshit items and not the most recent items 
from fastapi import HTTPException, FastAPI
import time
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import json
cache_fp = "cache.json"                 

cache = {}

def load_cache():
    global cache 
    if os.path.exists(cache_fp):
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

filter_keywords =  {"rep", "hangtags", "hangtags", "comes in bag", "comes in original bag", "tagged for visibility"}

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
        
        
        


if __name__ == "__main__":
    crawl_depop("chrome hearts")
    #get_old_listings("Chrome Hearts")
