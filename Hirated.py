from playwright.sync_api import sync_playwright
from datetime import datetime
import time

import google_sheets   # DO NOT MODIFY

URL = "https://www.wintwealth.com/bonds/listing/?filterBy=HIGH_RATED"

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "HIGH_RATED"

HEADERS = [
    "Company",
    "Rating",
    "Min Price",
    "YTM",
    "Tenure",
    "Interest",
    "Principal"
]

def safe_text(el):
    return el.inner_text().strip() if el else "NA"

def scrape_high_rated():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=60000)

        # ensure correct filter
        assert "filterBy=HIGH_RATED" in page.url, "❌ WRONG URL LOADED"

        page.wait_for_selector(
            'xpath=/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li',
            timeout=60000
        )

        time.sleep(2)

        cards = page.query_selector_all(
            'xpath=/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li'
        )

        print(f"\n✅ FOUND {len(cards)} HIGH RATED BONDS\n" + "=" * 90)

        for i, card in enumerate(cards, start=1):
            try:
                company = safe_text(card.query_selector(
                    'xpath=.//div/a/div[1]/div/div[1]/div/p'
                ))

                rating = safe_text(card.query_selector(
                    'xpath=.//span[@class="sc-a845de38-2 gNQmnK"]'
                ))

                min_price = safe_text(card.query_selector(
                    'xpath=.//div/a/div[1]/div/div[1]/div/div/span[1]'
                ))

               
                ytm = safe_text(card.query_selector(
                    'xpath=.//div/a/div[2]/div/div/div[1]/div/div[2]/div[1]/h3'
                ))
                tenure = safe_text(card.query_selector(
                    'xpath=.//div/a/div[2]/div/div/div[2]/div/div[2]/div[1]/h3'
                ))


                interest = safe_text(card.query_selector(
                    'xpath=.//div/a/div[2]/div/div/div[3]/div/div[1]/span'
                ))

                principal = safe_text(card.query_selector(
                    'xpath=.//div/a/div[2]/div/div/div[4]/div/div[2]/div[1]/h3'
                ))

                # PRINT TO TERMINAL FOR DEBUG
                print(f"Bond #{i}")
                print(f"Company   : {company}")
                print(f"Rating    : {rating}")
                print(f"Min Price : {min_price}")
                print(f"YTM       : {ytm}")
                print(f"Tenure    : {tenure}")
                print(f"Interest  : {interest}")
                print(f"Principal : {principal}")
                print("-" * 90)

                rows.append([
                    company, rating, min_price,
                    ytm, tenure, interest, principal
                ])

            except Exception as e:
                print(f"❌ ERROR in bond #{i}: {e}")

        browser.close()

    return rows

if __name__ == "__main__":
    data = scrape_high_rated()

    if data:
        google_sheets.update_google_sheet_by_name(
            sheet_id=SHEET_ID,
            worksheet_name=WORKSHEET_NAME,
            headers=HEADERS,
            rows=data
        )

        google_sheets.append_footer(
            sheet_id=SHEET_ID,
            worksheet_name=WORKSHEET_NAME,
            footer_row=[
                f"Last updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            ]
        )
