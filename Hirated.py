from playwright.sync_api import sync_playwright
import time
from datetime import datetime
from google_sheets import update_google_sheet_by_name, append_footer

# ---------------- CONFIG ---------------- #

URL = "https://www.wintwealth.com/bonds/listing/?filterBy=HIGH_RATED"

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "HIGH_RATED"

HEADERS = [
    "Company",
    "Rating",
    "Sold %",
    "YTM",
    "Tenure",
    "Interest",
    "Principal"
]

# ---------------- HELPERS ---------------- #

def safe_text(page, xpath):
    try:
        return page.locator(f"xpath={xpath}").inner_text(timeout=2000).strip()
    except:
        return "NA"

# ---------------- MAIN ---------------- #

def main():
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        # wait for first bond card
        page.wait_for_selector("xpath=//ul/div/li[1]//a", timeout=20000)

        # scroll to load all cards
        prev = 0
        for _ in range(25):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            count = page.locator("xpath=//ul/div/li").count()
            if count == prev:
                break
            prev = count

        total = page.locator("xpath=//ul/div/li").count()
        print(f"\nTotal bonds found: {total}\n")

        for i in range(1, total + 1):
            base = f"/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li[{i}]/div/a"

            company = safe_text(page, f"{base}/div[1]/div/div[1]/div/p")
            rating  = safe_text(page, f"{base}/div[1]/div/div[1]/div/div/div[1]/span")
            sold    = safe_text(page, f"{base}/div[1]/div/div[2]/span/span")
            sold    = sold.replace("Sold", "").strip()

            ytm = safe_text(page, f"{base}/div[2]/div/div/div[1]/div/div[2]/div[1]/h3")
            tenure = safe_text(page, f"{base}/div[2]/div/div/div[2]/div/div[2]/div[1]/h3")
            interest = safe_text(page, f"{base}/div[2]/div/div/div[3]/div/div[2]/div[1]/h3")
            principal = safe_text(page, f"{base}/div[2]/div/div/div[4]/div/div[2]/div[1]/h3")

            print(f"{i}. {company} | {sold} | {ytm}")

            rows.append([
                company,
                rating,
                sold,
                ytm,
                tenure,
                interest,
                principal
            ])

        browser.close()

    # push data to sheet
    update_google_sheet_by_name(
        SHEET_ID,
        WORKSHEET_NAME,
        HEADERS,
        rows
    )

    # append timestamp footer
    timestamp = datetime.now().strftime("Updated on %d-%m-%Y %H:%M:%S")
    append_footer(
        SHEET_ID,
        WORKSHEET_NAME,
        [timestamp]
    )

    print("✅ Sheet updated with timestamp")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
