from playwright.sync_api import sync_playwright
from datetime import datetime
import time
import google_sheets   # DO NOT MODIFY

URL = "https://www.wintwealth.com/bonds/listing/?filterBy=TAX_BENEFIT"

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "TAX_BENEFIT"

HEADERS = [
    "Company",
    "Rating",
    "Min Price",
    "YTM",
    "Tenure / Maturity",
    "Interest",
    "Principal"
]

def safe_text(el):
    return el.inner_text().strip() if el else "NA"

def scrape_tax_benefit():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        assert "filterBy=TAX_BENEFIT" in page.url, "❌ WRONG URL"

        page.wait_for_selector(
            'xpath=/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li'
        )

        cards = page.query_selector_all(
            'xpath=/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li'
        )

        print(f"\nFOUND {len(cards)} TAX BENEFIT BONDS\n" + "=" * 90)

        for i, card in enumerate(cards, 1):
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

                # ✅ FIXED (RELATIVE XPATH)
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
                print(f"❌ Error bond #{i}: {e}")

        browser.close()
    return rows

if __name__ == "__main__":
    data = scrape_tax_benefit()

    if data:
        google_sheets.update_google_sheet_by_name(
            SHEET_ID,
            WORKSHEET_NAME,
            HEADERS,
            data
        )

        google_sheets.append_footer(
            SHEET_ID,
            WORKSHEET_NAME,
            [f"Last updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"]
        )
