import requests
import gspread
import os
import json
import re
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# CODE GENERATOR
# =========================

def generate_code(company, coupon_rate, maturity_date):
    try:
        coupon = str(coupon_rate).replace("%", "").replace(".", "")

        initials = "".join(
            word[0].upper()
            for word in company.split()
            if word and word[0].isalnum()
        )

        year_match = re.search(r"(\d{4})", str(maturity_date))
        year = year_match.group(1)[-2:] if year_match else ""

        return f"{coupon}{initials}{year}"

    except Exception:
        return ""

# =========================
# GOOGLE SHEETS
# =========================

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
SHEET_NAME = "indiabond"

creds_dict = json.loads(os.environ["NEW"])

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# =========================
# INDIA BONDS API
# =========================

URL = "https://prod-api.indiabonds.com/api/v3/web/bond-list/?page_no=1&page_size=100&sort_by=yield_high_to_low&tag_name=Secured"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

print("Status Code:", response.status_code)

if response.status_code != 200:
    raise Exception(
        f"Request failed: {response.status_code}\n{response.text[:500]}"
    )

data = response.json()

# API structure may vary
bonds = (
    data.get("bond_list")
    or data.get("data")
    or []
)

rows = []

for bond in bonds:

    code = generate_code(
        bond.get("issuer_name", ""),
        bond.get("coupon_rate", ""),
        bond.get("maturity_date", "")
    )

    rows.append([
        bond.get("issuer_name", ""),
        bond.get("isin", ""),
        bond.get("rating_combined", ""),
        bond.get("type_of_bond", ""),
        bond.get("maturity_date", ""),
        bond.get("coupon_rate", ""),
        bond.get("price", ""),
        bond.get("security_type", ""),
        bond.get("yield_value", ""),
        code
    ])

print(f"Fetched {len(rows)} bonds")

# =========================
# UPLOAD TO SHEET
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
    "yield_value",
    "code"
]

sheet.clear()

ist_time = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%d-%m-%Y %I:%M:%S %p")

sheet.update(
    values=[headers_row] + rows,
    range_name="A1"
)
sheet.append_row([ist_time])

print(f"Uploaded {len(rows)} records")
