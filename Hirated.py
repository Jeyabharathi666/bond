from playwright.sync_api import sync_playwright
import time
from google_sheets import update_google_sheet_by_name

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

def safe_text(page, xpath):
    try:
        return page.locator(f"xpath={xpath}").inner_text(timeout=2000).strip()
    except:
        return "NA"

def main():
    data_rows = []

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
            sold    = safe_text(page, f"{base}/div[1]/div/div[2]/span/span").replace("Sold", "").strip()

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

    # push to Google Sheet using your existing helper
    update_google_sheet_by_name(
        SHEET_ID,
        WORKSHEET_NAME,
        HEADERS,
        data_rows
    )

if __name__ == "__main__":
    main()


'''
from playwright.sync_api import sync_playwright
import time, re
from datetime import datetime
from google_sheets import update_google_sheet_by_name, append_footer

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "HIGH_RATED"

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
        return page.locator(f"xpath={xpath}").inner_text(timeout=3000).strip()
    except:
        return ""

def extract_live_count(text):
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else 0

def parse_price(text):
    if not text:
        return "NA"

    t = text.lower().replace("₹", "").replace(",", "")
    t = t.replace("minimum", "").replace("min.", "").replace("min", "").strip()

    m = re.search(r"(\d+(\.\d+)?)", t)
    if not m:
        return "NA"

    num = float(m.group(1))

    if "lk" in t or re.search(r"\bl\b", t):
        return int(num * 100000)
    if "k" in t:
        return int(num * 1000)

    return int(num)

# ---------------- MAIN ---------------- #

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("\n🔵 STARTING HIGH_RATED SCRAPE")

        page.goto(
            "https://www.wintwealth.com/bonds/listing/?filterBy=HIGH_RATED",
            timeout=60000
        )
        page.wait_for_selector("xpath=//ul/div/li[1]//a", timeout=30000)

        live_text = safe_text(
            page,
            "/html/body/div[2]/div/div[2]/div/div[1]/div/div[1]/div/div[1]/div[1]/h2"
        )
        live_count = extract_live_count(live_text)

        print(f"🟢 HIGH_RATED live bonds: {live_count}")

        # -------- SCROLL ONLY UNTIL LIVE COUNT -------- #
        for _ in range(30):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            if page.locator("xpath=//ul/div/li").count() >= live_count:
                break

        rows = []

        for i in range(1, live_count + 1):
            base = (
                "/html/body/div[2]/div/div[2]/div/div[1]/div/"
                f"div[2]/ul/div/li[{i}]/div/a"
            )

            company = safe_text(page, f"{base}/div[1]/div/div[1]/div/p")
            rating = safe_text(page, f"{base}/div[1]/div/div[1]/div/div/div[1]/span")
            price = parse_price(
                safe_text(page, f"{base}/div[1]/div/div[1]/div/div/span")
            )
            sold = safe_text(page, f"{base}/div[1]/div/div[2]/span/span")
            sold = sold.replace("Sold", "").strip()

            ytm = safe_text(page, f"{base}/div[2]/div/div/div[1]/div/div[2]/div[1]/h3")
            tenure = safe_text(page, f"{base}/div[2]/div/div/div[2]/div/div[2]/div[1]/h3")
            interest = safe_text(page, f"{base}/div[2]/div/div/div[3]/div/div[2]/div[1]/h3")
            principal = safe_text(page, f"{base}/div[2]/div/div/div[4]/div/div[2]/div[1]/h3")

            print(f"{i}. {company} | YTM={ytm}")

            rows.append([
                company, rating, price, sold, ytm, tenure, interest, principal
            ])

        update_google_sheet_by_name(SHEET_ID, WORKSHEET_NAME, HEADERS, rows)
        append_footer(
            SHEET_ID,
            WORKSHEET_NAME,
            [datetime.now().strftime("Updated on %d-%m-%Y %H:%M:%S")]
        )

        print("✅ HIGH_RATED sheet updated successfully")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
'''
