from playwright.sync_api import sync_playwright
import time
from datetime import datetime
from google_sheets import update_google_sheet_by_name, append_footer

# ================= CONFIG =================
SHEET_ID = "1VtgTb36SB65HtQQpjcagh4cxr7pDGcLzGpR9ScE4vdA"
WORKSHEET_NAME = "indiabonds"

BASE_URL = (
    "https://www.indiabonds.com/search/"
    "?filter=%7B%22curated_pack_filter%22%3A%5B%22New+Arrivals%22%5D%7D"
    "&ordering=-vendor_security_offer_price__yield_value"
)

ITEMS_PER_PAGE = 9
TOTAL_PAGES = 4          # Known last page
LAST_PAGE_SINGLE = 4     # Page 4 has only one valid item

HEADERS = [
    "Company",
    "Coupon",
    "Maturity",
    "Rating",
    "Type of Bond",
    "Interest Payment",
    "Yield",
    "Price",
    "Security"
]

rows = []

# ================= SCRAPER =================
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    page = browser.new_page()

    for page_no in range(1, TOTAL_PAGES + 1):
        offset = (page_no - 1) * ITEMS_PER_PAGE
        url = f"{BASE_URL}&offset={offset}"

        print(f"\n--- PAGE {page_no} ---")
        page.goto(url, timeout=60000)

        # Trigger JS render
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)

        # Page 4 → only 1 record
        item_range = [1] if page_no == LAST_PAGE_SINGLE else range(1, ITEMS_PER_PAGE + 1)

        for i in item_range:
            base = f"/html/body/div[1]/div[2]/div[2]/div[3]/div/div/div[{i}]"

            try:
                company = page.locator(
                    f"xpath={base}/div[2]/div/div[2]/p"
                ).text_content(timeout=5000).strip()

                coupon = page.locator(
                    f"xpath={base}/div[3]/div[1]/p[2]"
                ).text_content(timeout=5000).strip()

                maturity = page.locator(
                    f"xpath={base}/div[3]/div[2]/p[2]"
                ).text_content(timeout=5000).strip()

                rating = page.locator(
                    f"xpath={base}/div[3]/div[3]/p[2]"
                ).text_content(timeout=5000).strip()

                type_of_bond = page.locator(
                    f"xpath={base}/div[3]/div[4]/p[2]"
                ).text_content(timeout=5000).strip()

                yield_val = page.locator(
                    f"xpath={base}/div[3]/div[5]/p[2]"
                ).text_content(timeout=5000).strip()

                price = page.locator(
                    f"xpath={base}/div[3]/div[6]/p[2]"
                ).text_content(timeout=5000).strip()

                # Interest Payment from table
                interest_payment = page.locator(
                    f"xpath=/html/body/div[1]/div[2]/div[2]/div[4]/div/table/tbody/tr[{i}]/td[5]/div"
                ).text_content(timeout=5000).strip()

                security = (
                    "SECURED"
                    if "secured" in type_of_bond.lower()
                    else "UNSECURED"
                )

                rows.append([
                    company,
                    coupon,
                    maturity,
                    rating,
                    type_of_bond,
                    interest_payment,
                    yield_val,
                    price,
                    security
                ])

                print(f"✔ Collected: {company} | {interest_payment}")

            except Exception as e:
                print("⚠ Skipped row:", e)

    browser.close()

# ================= PUSH TO GOOGLE SHEET =================
update_google_sheet_by_name(
    sheet_id=SHEET_ID,
    worksheet_name=WORKSHEET_NAME,
    headers=HEADERS,
    rows=rows
)

# ================= TIMESTAMP FOOTER =================
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
print("\n🕒 Last Updated:", timestamp)

append_footer(
    sheet_id=SHEET_ID,
    worksheet_name=WORKSHEET_NAME,
    footer_row=[f"Last Updated : {timestamp}"]
)
