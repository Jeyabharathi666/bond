'''from playwright.sync_api import sync_playwright
import time
from datetime import datetime
from google_sheets import update_google_sheet_by_name, append_footer

# ---------------- CONFIG ---------------- #

URL = "https://www.wintwealth.com/bonds/listing/?filterBy=HIGH_RATED"

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "winthrat"

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
'''
from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime
from google_sheets import update_google_sheet_by_name, append_footer

# ---------------- CONFIG ---------------- #

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"

FILTERS = ["winthrat", "wintaxbt"]

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
        return ""

def extract_live_count(text):
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else 0

# ---------------- SCRAPER ---------------- #

def scrape_filter(page, filter_name):
    url = f"https://www.wintwealth.com/bonds/listing/?filterBy={filter_name}"
    print(f"\n🔍 Scraping {filter_name} (LIVE ONLY)")

    page.goto(url, timeout=60000)
    page.wait_for_selector("xpath=//ul/div/li[1]//a", timeout=20000)

    # -------- LIVE BOND COUNT -------- #

    live_text = safe_text(
        page,
        "/html/body/div[2]/div/div[2]/div/div[1]/div/div[1]/div/div[1]/div[1]/h2"
    )

    live_count = extract_live_count(live_text)
    print(f"🟢 Live bonds count: {live_count}")

    if live_count == 0:
        print("⚠ No live bonds found")
        return

    # -------- SCROLL -------- #

    prev = 0
    for _ in range(25):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        count = page.locator("xpath=//ul/div/li").count()
        if count == prev:
            break
        prev = count

    total_cards = page.locator("xpath=//ul/div/li").count()
    limit = min(live_count, total_cards)

    rows = []

    # -------- EXTRACT LIVE ONLY -------- #

    for i in range(1, limit + 1):
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

    # -------- PUSH TO SHEET -------- #

    update_google_sheet_by_name(
        SHEET_ID,
        filter_name,
        HEADERS,
        rows
    )

    timestamp = datetime.now().strftime("Updated on %d-%m-%Y %H:%M:%S")
    append_footer(
        SHEET_ID,
        filter_name,
        [timestamp]
    )

    print(f"✅ {filter_name} updated (LIVE ONLY)")

# ---------------- MAIN ---------------- #

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for f in FILTERS:
            scrape_filter(page, f)

        browser.close()

if __name__ == "__main__":
    main()
