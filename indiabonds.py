# from playwright.sync_api import sync_playwright
# import time
# from datetime import datetime
# from google_sheets import update_google_sheet_by_name, append_footer

# # ================= CONFIG =================
# SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
# WORKSHEET_NAME = "indiabonds"

# BASE_URL = "https://www.indiabonds.com/search/?filter=%7B%7D"

# ITEMS_PER_PAGE = 9
# TOTAL_PAGES = 11
# LAST_PAGE_ITEMS = 5   # 👈 confirmed by UI

# HEADERS = [
#     "Company",
#     "Coupon",
#     "Maturity",
#     "Rating",
#     "Type of Bond",
#     "Interest Payment",
#     "Yield",
#     "Price",
#     "Security"
# ]

# rows = []

# # ================= SCRAPER =================
# with sync_playwright() as p:
#     browser = p.chromium.launch(
#         headless=True,
#         args=["--no-sandbox", "--disable-dev-shm-usage"]
#     )
#     page = browser.new_page()

#     for page_no in range(1, TOTAL_PAGES + 1):
#         offset = (page_no - 1) * ITEMS_PER_PAGE
#         url = f"{BASE_URL}&offset={offset}"

#         print(f"\n--- PAGE {page_no} ---")
#         page.goto(url, timeout=60000)

#         page.wait_for_load_state("networkidle")
#         page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
#         time.sleep(2)

#         if page_no == TOTAL_PAGES:
#             item_range = range(1, LAST_PAGE_ITEMS + 1)
#         else:
#             item_range = range(1, ITEMS_PER_PAGE + 1)

#         for i in item_range:
#             base = f"/html/body/div[1]/div[2]/div[2]/div[3]/div/div/div[{i}]"

#             try:
#                 company = page.locator(
#                     f"xpath={base}/div[2]/div/div[2]/p"
#                 ).text_content(timeout=5000).strip()

#                 raw_coupon = page.locator(f"xpath={base}/div[3]/div[1]/p[2]").text_content(timeout=5000).strip()
#                 try:
#                     coupon = float(raw_coupon.replace("%", "").strip()) / 100
#                 except:
#                     coupon = None


#                 maturity = page.locator(
#                     f"xpath={base}/div[3]/div[2]/p[2]"
#                 ).text_content(timeout=5000).strip()

#                 rating = page.locator(
#                     f"xpath={base}/div[3]/div[3]/p[2]"
#                 ).text_content(timeout=5000).strip()

#                 type_of_bond = page.locator(
#                     f"xpath={base}/div[3]/div[4]/p[2]"
#                 ).text_content(timeout=5000).strip()

#                 yield_val = page.locator(
#                     f"xpath={base}/div[3]/div[5]/p[2]"
#                 ).text_content(timeout=5000).strip()

#                 price = page.locator(
#                     f"xpath={base}/div[3]/div[6]/p[2]"
#                 ).text_content(timeout=5000).strip()

#                 interest_payment = page.locator(
#                     f"xpath=/html/body/div[1]/div[2]/div[2]/div[4]/div/table/tbody/tr[{i}]/td[5]/div"
#                 ).text_content(timeout=5000).strip()

#                 security = (
#                     "SECURED"
#                     if "secured" in type_of_bond.lower()
#                     else "UNSECURED"
#                 )

#                 rows.append([
#                     company,
#                     coupon,
#                     maturity,
#                     rating,
#                     type_of_bond,
#                     interest_payment,
#                     yield_val,
#                     price,
#                     security
#                 ])

#                 print(f"✔ {company}")

#             except Exception as e:
#                 print(f"⚠ Skipped row {i}: {e}")

#     browser.close()

# # ================= PUSH TO GOOGLE SHEET =================
# update_google_sheet_by_name(
#     sheet_id=SHEET_ID,
#     worksheet_name=WORKSHEET_NAME,
#     headers=HEADERS,
#     rows=rows
# )

# # ================= FOOTER =================
# timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
# append_footer(
#     sheet_id=SHEET_ID,
#     worksheet_name=WORKSHEET_NAME,
#     footer_row=[f"Last Updated : {timestamp}"]
# )
import requests
import gspread
import os
import json
from google.oauth2.service_account import Credentials

# =========================
# GOOGLE SHEETS
# =========================

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
SHEET_NAME = "indpe"

creds_dict = json.loads(os.environ["NEW"])

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=scopes
)

client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# =========================
# INDIA BONDS API
# =========================

url = "https://prod-api.indiabonds.com/api/v3/web/bond-list/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

all_rows = []

page = 1

while True:

    params = {
        "page_no": page,
        "page_size": 100,
        "sort_by": "yield_high_to_low",
        "tag_name": "Secured"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    bonds = data.get("bond_list", [])

    if not bonds:
        break

    for bond in bonds:
        all_rows.append([
            bond.get("issuer_name", ""),
            bond.get("isin", ""),
            bond.get("rating_combined", ""),
            bond.get("type_of_bond", ""),
            bond.get("maturity_date", ""),
            bond.get("coupon_rate", ""),
            bond.get("price", ""),
            bond.get("security_type", ""),
            bond.get("yield_value", "")
        ])

    print(f"Fetched page {page} ({len(bonds)} bonds)")
    page += 1

# =========================
# WRITE TO SHEET
# =========================

headers_row = [
    "issuer_name",
    "isin",
    "rating_combined",
    "type_of_bond",
    "maturity_date",
    "coupon_rate",
    "price",
    "security_type",
    "yield_value"
]

sheet.clear()

sheet.update(
    "A1",
    [headers_row] + all_rows
)

print(f"Uploaded {len(all_rows)} records")
