from playwright.sync_api import sync_playwright
from datetime import datetime
import time

import google_sheets   # DO NOT CHANGE

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

def scrape_tax_benefit():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        page.wait_for_selector("ul div li", timeout=60000)
        time.sleep(2)

        bonds = page.query_selector_all("ul div li")

        print(f"\n🔎 TAX BENEFIT bonds found: {len(bonds)}\n")
        print("=" * 95)

        for i, bond in enumerate(bonds, start=1):
            try:
                company = bond.query_selector("p").inner_text().strip()

                rating = bond.query_selector(
                    "span[class*='gNQmnK'], span[class*='rating']"
                )
                rating = rating.inner_text().strip() if rating else "NA"

                spans = bond.query_selector_all("div span")

                price = spans[0].inner_text().strip() if len(spans) > 0 else "NA"
                ytm = spans[1].inner_text().strip() if len(spans) > 1 else "NA"
                tenure = spans[2].inner_text().strip() if len(spans) > 2 else "NA"

                interest = bond.query_selector(
                    "div:nth-child(2) span"
                ).inner_text().strip()

                principal = bond.query_selector("h3").inner_text().strip()

                # TERMINAL OUTPUT (as requested)
                print(f"Bond #{i}")
                print(f"Company    : {company}")
                print(f"Rating     : {rating}")
                print(f"Min Price  : {price}")
                print(f"YTM        : {ytm}")
                print(f"Tenure     : {tenure}")
                print(f"Interest   : {interest}")
                print(f"Principal  : {principal}")
                print("-" * 95)

                rows.append([
                    company,
                    rating,
                    price,
                    ytm,
                    tenure,
                    interest,
                    principal
                ])

            except Exception as e:
                print(f"❌ Error in bond #{i}: {e}")

        browser.close()

    return rows

if __name__ == "__main__":
    data = scrape_tax_benefit()

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
            footer_row=[f"Last updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"]
        )
