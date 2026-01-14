from playwright.sync_api import sync_playwright
from datetime import datetime
import time

# import your existing helper (UNCHANGED)
import google_sheets

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "HIGH_RATED"

URL = "https://www.wintwealth.com/bonds/listing/?filterBy=HIGH_RATED"

HEADERS = [
    "Company",
    "Rating",
    "Min Price",
    "YTM",
    "Tenure",
    "Interest",
    "Principal"
]

def scrape_high_rated():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        page.wait_for_selector("ul div li", timeout=60000)
        time.sleep(2)

        bonds = page.query_selector_all("ul div li")

        print(f"\n🔎 Total bonds found: {len(bonds)}\n")
        print("=" * 90)

        for i, bond in enumerate(bonds, start=1):
            try:
                company = bond.query_selector("p").inner_text().strip()

                rating = bond.query_selector(
                    "span[class*='gNQmnK']"
                ).inner_text().strip()

                spans = bond.query_selector_all("div span")

                price = spans[0].inner_text().strip() if len(spans) > 0 else "NA"
                ytm = spans[1].inner_text().strip() if len(spans) > 1 else "NA"
                tenure = spansnspans = spans[2].inner_text().strip() if len(spans) > 2 else "NA"

                interest = bond.query_selector(
                    "div:nth-child(2) span"
                ).inner_text().strip()

                principal = bond.query_selector("h3").inner_text().strip()

                # Print to terminal (as requested)
                print(f"Bond #{i}")
                print(f"Company   : {company}")
                print(f"Rating    : {rating}")
                print(f"Min Price : {price}")
                print(f"YTM       : {ytm}")
                print(f"Tenure    : {tenure}")
                print(f"Interest  : {interest}")
                print(f"Principal : {principal}")
                print("-" * 90)

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
                print(f"❌ Error parsing bond #{i}: {e}")

        browser.close()

    return rows

if __name__ == "__main__":
    data_rows = scrape_high_rated()

    if data_rows:
        google_sheets.update_google_sheet_by_name(
            sheet_id=SHEET_ID,
            worksheet_name=WORKSHEET_NAME,
            headers=HEADERS,
            rows=data_rows
        )

        google_sheets.append_footer(
            sheet_id=SHEET_ID,
            worksheet_name=WORKSHEET_NAME,
            footer_row=[f"Last updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"]
        )
