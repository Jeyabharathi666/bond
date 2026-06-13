
import requests
import gspread
import os
import json
from google.oauth2.service_account import Credentials

# =========================
# GOOGLE SHEETS
# =========================

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
SHEET_NAME = "indiabond"

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
