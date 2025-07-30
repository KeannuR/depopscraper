from playwright.sync_api import sync_playwright
from uuid import uuid4

SEARCH_PATH = "/api/v3/search/products/"

def main():
    with sync_playwright() as p:
        # 1) Launch a real browser and visit Depop
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context()
        page    = ctx.new_page()
        page.goto("https://www.depop.com/", wait_until="networkidle")

        # 2) Capture the storage state (cookies + localStorage)
        storage = ctx.storage_state()

        # 3) Extract whatever tokens Depop set in localStorage
        device_id  = page.evaluate("() => localStorage.getItem('depop-device-id')")
        session_id = page.evaluate("() => localStorage.getItem('depop-session-id')")
        # generate a fresh search id each run
        search_id  = str(uuid4())
        # mirror the real browser’s UA
        ua         = page.evaluate("() => navigator.userAgent")

        # now we can close the browser if you like
        browser.close()

        # 4) Create an APIRequestContext reusing that storage + headers
        api_ctx = p.request.new_context(
            base_url="https://webapi.depop.com",
            extra_http_headers={
                "Accept":           "*/*",
                "Accept-Encoding":  "gzip, deflate",   # requests Playwright will auto‑decompress
                "Content-Type":     "application/json",
                "Origin":           "https://www.depop.com",
                "Referer":          "https://www.depop.com/",
                "User-Agent":       ua,
                "Depop-Device-Id":  device_id,
                "Depop-Session-Id": session_id,
                "Depop-Search-Id":  search_id,
            },
            storage_state=storage
        )

        # 5) Issue the API call
        params = {
            "what":                   "chrome hearts",
            "cursor":                 "MnwxOXwxNzUzODI2NTIx.Mnw1fDE3NTM4MjY1MjE.1",
            "items_per_page":         "24",
            "country":                "us",
            "user_id":                "41962803",
            "sort":                   "newlyListed",
            "currency":               "USD",
            "force_fee_calculation":  "false",
            "from":                   "in_country_search",
            "boosted_spacing":        "4",
            "boosted_group_size":     "1",
        }

        response = api_ctx.get(SEARCH_PATH, params=params)

        # 6) Check for errors and parse JSON
        if not response.ok:
        
            print(response.text())
        else:
            data = response.json()
            products = data.get("products") or data.get("product_listings") or []
            print(f"✅ Found {len(products)} items")
            for item in products:
                print(" •", item.get("product_link"), item.get("price"))
            # or: print(data) for full payload

        api_ctx.dispose()

if __name__ == "__main__":
    main()
