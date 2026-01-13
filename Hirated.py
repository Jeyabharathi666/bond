'''
from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime
from google_sheets import update_google_sheet_by_name, append_footer

# ---------------- CONFIG ---------------- #

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"

FILTERS = ["HIGH_RATED", "TAX_BENEFIT"]

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
        update_google_sheet_by_name(
            SHEET_ID, filter_name, HEADERS, []
        )
        return

    # -------- SCROLL TO LOAD -------- #

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

    # -------- EXTRACT ONLY LIVE -------- #

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

    print(f"✅ {filter_name} updated correctly (LIVE ONLY)")

# ---------------- MAIN (CRITICAL FIX HERE) ---------------- #

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 🔑 NEW PAGE FOR EACH FILTER (FIXES DATA MIXING)
        for f in FILTERS:
            page = browser.new_page()
            scrape_filter(page, f)
            page.close()

        browser.close()

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

FILTERS = ["HIGH_RATED", "TAX_BENEFIT"]

HEADERS = [
    "Company",
    "Rating",
    "Price",
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

def parse_price(text):
    """
    Converts:
    1k  -> 1000
    1L / 1lk -> 100000
    ₹5,000 -> 5000
    """
    if not text:
        return "NA"

    t = text.lower().replace("₹", "").replace(",", "").strip()

    if t.endswith("k"):
        return int(float(t[:-1]) * 1000)
    if t.endswith("lk") or t.endswith("l"):
        return int(float(t.replace("lk", "").replace("l", "")) * 100000)

    if t.isdigit():
        return int(t)

    return "NA"

# ---------------- SCRAPER ---------------- #

def scrape_filter(page, filter_name):
    url = f"https://www.wintwealth.com/bonds/listing/?filterBy={filter_name}"
    print(f"\n🔍 Scraping {filter_name} (LIVE ONLY)")

    page.goto(url, timeout=60000)
    page.wait_for_selector("xpath=//ul/div/li[1]//a", timeout=20000)

    # -------- LIVE COUNT -------- #

    live_text = safe_text(
        page,
        "/html/body/div[2]/div/div[2]/div/div[1]/div/div[1]/div/div[1]/div[1]/h2"
    )

    live_count = extract_live_count(live_text)
    print(f"🟢 Live bonds count: {live_count}")

    if live_count == 0:
        update_google_sheet_by_name(
            SHEET_ID, filter_name, HEADERS, []
        )
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

    # -------- EXTRACT -------- #

    for i in range(1, limit + 1):
        base = f"/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/ul/div/li[{i}]/div/a"

        company = safe_text(page, f"{base}/div[1]/div/div[1]/div/p")
        rating  = safe_text(page, f"{base}/div[1]/div/div[1]/div/div/div[1]/span")

        price_raw = safe_text(
            page,
            f"{base}/div[1]/div/div[1]/div/div/span"
        )
        price = parse_price(price_raw)

        sold = safe_text(page, f"{base}/div[1]/div/div[2]/span/span")
        sold = sold.replace("Sold", "").strip()

        ytm = safe_text(page, f"{base}/div[2]/div/div/div[1]/div/div[2]/div[1]/h3")
        tenure = safe_text(page, f"{base}/div[2]/div/div/div[2]/div/div[2]/div[1]/h3")
        interest = safe_text(page, f"{base}/div[2]/div/div/div[3]/div/div[2]/div[1]/h3")
        principal = safe_text(page, f"{base}/div[2]/div/div/div[4]/div/div[2]/div[1]/h3")

        print(f"{i}. {company} | Price={price} | Sold={sold}")

        rows.append([
            company,
            rating,
            price,
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

    print(f"✅ {filter_name} updated with PRICE")

# ---------------- MAIN ---------------- #

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for f in FILTERS:
            page = browser.new_page()
            scrape_filter(page, f)
            page.close()

        browser.close()

if __name__ == "__main__":
    main()
