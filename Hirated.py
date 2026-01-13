from playwright.sync_api import sync_playwright
import time
import os
import tempfile
from google_sheets import update_google_sheet_by_name

# ---------------- GOOGLE AUTH ---------------- #

SERVICE_ACCOUNT_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(os.environ["NEW"])

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
    data_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        # Wait for first bond card
        page.wait_for_selector("xpath=//ul//li[1]//a", timeout=20000)

        # Scroll to load all cards
        prev = 0
        for _ in range(25):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            count = page.locator("xpath=//ul//li").count()
            if count == prev:
                break
            prev = count

        total = page.locator("xpath=//ul//li").count()
        print(f"\nTotal bonds found: {total}\n")

        for i in range(1, total + 1):
            base = f"/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li[{i}]/div/a"

            company = safe_text(page, f"{base}/div[1]/div/div[1]/div/p")
            rating  = safe_text(page, f"{base}/div[1]/div/div[1]/div/div/div[1]/span")
            sold    = safe_text(page, f"{base}/div[1]/div/div[2]/span/span")

            ytm = safe_text(page, f"{base}/div[2]/div/div/div[1]/div/div[2]/div[1]/h3")
            tenure = safe_text(page, f"{base}/div[2]/div/div/div[2]/div/div[2]/div[1]/h3")
            interest = safe_text(page, f"{base}/div[2]/div/div/div[3]/div/div[2]/div[1]/h3")
            principal = safe_text(page, f"{base}/div[2]/div/div/div[4]/div/div[2]/div[1]/h3")

            print(f"{i}. {company} | {sold} | {ytm}")

            data_rows.append([
                company,
                rating,
                sold,
                ytm,
                tenure,
                interest,
                principal
            ])

        browser.close()

    # ---------------- PUSH TO SHEET ---------------- #

    update_google_sheet_by_name(
        SHEET_ID,
        WORKSHEET_NAME,
        HEADERS,
        data_rows
    )

    print(f"\n✅ Data pushed successfully to worksheet: {WORKSHEET_NAME}")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
