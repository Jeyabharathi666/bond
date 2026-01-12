'''from playwright.sync_api import sync_playwright
import time
import os
from google_sheets import update_google_sheet_by_name
import json
import tempfile

# === Write secret JSON to temp file for gspread ===
SERVICE_ACCOUNT_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(os.environ["NEW"])

URL = "https://www.wintwealth.com/bonds/aaa-rated-bonds/"

def click_load_more_until_done(page, max_clicks=200):
    rows_locator = page.locator("tr.table-row-common")
    last_count = rows_locator.count()
    stalled_tries = 0

    def try_click(selector_str: str) -> bool:
        btn = page.locator(selector_str)
        if btn.count() == 0:
            return False
        try:
            btn.first.scroll_into_view_if_needed()
            btn.first.click(timeout=4000)
            return True
        except Exception:
            try:
                btn.first.scroll_into_view_if_needed()
                btn.first.click(force=True, timeout=4000)
                return True
            except Exception:
                try:
                    page.evaluate(
                        """(sel) => {
                            const el = document.querySelector(sel);
                            if (el) { el.scrollIntoView({block:'center'}); el.click(); return true; }
                            return false;
                        }""",
                        selector_str
                    )
                    return True
                except Exception:
                    return False

    for i in range(max_clicks):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)

        clicked = (
            try_click("#DIRECTORY_FILTER_PAGE_CTA-LOAD_MORE") or
            try_click("button:has-text('Load more')") or
            try_click("xpath=//button[normalize-space()='Load more']")
        )

        if not clicked:
            if page.locator("button:has-text('Load more')").count() == 0 and \
               page.locator("#DIRECTORY_FILTER_PAGE_CTA-LOAD_MORE").count() == 0:
                break
            else:
                stalled_tries += 1
                if stalled_tries >= 3:
                    break
                continue

        for _ in range(10):
            page.wait_for_timeout(500)
            new_count = rows_locator.count()
            if new_count > last_count:
                last_count = new_count
                stalled_tries = 0
                if last_count >= 500:
                    break
                break
        else:
            stalled_tries += 1
            if stalled_tries >= 2:
                break

def main():
    data_rows = []
    headers = ["Issuer", "Rating", "ISIN", "Amount", "Maturity", "Coupon"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=150)
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        page.wait_for_selector("tr.table-row-common", timeout=20000)
        click_load_more_until_done(page)

        rows = page.locator("tr.table-row-common")
        total = rows.count()
        print(f"\nTotal bonds found: {total}\n")

        for i in range(total):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() < 4:
                continue

            first_col = tds.nth(0).inner_text().strip()
            lines = [ln.strip() for ln in first_col.splitlines() if ln.strip()]
            issuer = lines[0] if len(lines) > 0 else ""
            rating = lines[1] if len(lines) > 1 else ""
            isin   = lines[2] if len(lines) > 2 else ""

            amount   = tds.nth(1).inner_text().strip()
            maturity = tds.nth(2).inner_text().strip()
            coupon   = tds.nth(3).inner_text().strip()

            data_rows.append([issuer, rating, isin, amount, maturity, coupon])

        browser.close()

    # Push to Google Sheet
    SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
    WORKSHEET_NAME = "AAA"
    update_google_sheet_by_name(SHEET_ID, WORKSHEET_NAME, headers, data_rows)

if __name__ == "__main__":
    main()
'''
'''
from playwright.sync_api import sync_playwright
import time
import os
from google_sheets import update_google_sheet_by_name
import tempfile

# === Write secret JSON to temp file for gspread ===
SERVICE_ACCOUNT_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(os.environ["NEW"])

URL = "https://www.wintwealth.com/bonds/aaa-rated-bonds/"

def click_load_more_until_done(page, max_clicks=200):
    rows_locator = page.locator("tr.table-row-common")
    last_count = rows_locator.count()
    stalled_tries = 0

    def try_click(selector_str: str) -> bool:
        btn = page.locator(selector_str)
        if btn.count() == 0:
            return False
        try:
            btn.first.scroll_into_view_if_needed()
            btn.first.click(timeout=4000)
            return True
        except Exception:
            try:
                btn.first.click(force=True, timeout=4000)
                return True
            except Exception:
                return False

    for _ in range(max_clicks):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)

        clicked = (
            try_click("#DIRECTORY_FILTER_PAGE_CTA-LOAD_MORE") or
            try_click("button:has-text('Load more')")
        )

        if not clicked:
            break

        page.wait_for_timeout(1000)
        new_count = rows_locator.count()
        if new_count == last_count:
            stalled_tries += 1
            if stalled_tries >= 2:
                break
        else:
            last_count = new_count
            stalled_tries = 0

def get_security_status(page, issuer, isin):
    """
    Open bond detail page and fetch Secured / Unsecured
    """
    slug = issuer.lower().replace("&", "").replace(".", "").replace(" ", "-")
    detail_url = f"https://www.wintwealth.com/bonds/{slug}/{isin.lower()}"

    try:
        page.goto(detail_url, timeout=60000)
        page.wait_for_selector(
            "xpath=/html/body/div[2]/main/main/article/div[2]/div/div/section[1]/div[2]/div[1]/div[1]",
            timeout=15000
        )
        text = page.locator(
            "xpath=/html/body/div[2]/main/main/article/div[2]/div/div/section[1]/div[2]/div[1]/div[1]"
        ).inner_text().strip()

        if "secured" in text.lower():
            return "SECURED"
        if "unsecured" in text.lower():
            return "UNSECURED"

        return "UNKNOWN"

    except Exception:
        return "UNKNOWN"

def main():
    data_rows = []
    headers = [
        "Issuer",
        "Rating",
        "ISIN",
        "Amount",
        "Maturity",
        "Coupon",
        "Security"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        page.wait_for_selector("tr.table-row-common", timeout=20000)
        click_load_more_until_done(page)

        rows = page.locator("tr.table-row-common")
        total = rows.count()
        print(f"\nTotal bonds found: {total}\n")

        for i in range(total):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() < 4:
                continue

            first_col = tds.nth(0).inner_text().strip()
            lines = [ln.strip() for ln in first_col.splitlines() if ln.strip()]

            issuer = lines[0] if len(lines) > 0 else ""
            rating = lines[1] if len(lines) > 1 else ""
            isin   = lines[2] if len(lines) > 2 else ""

            amount   = tds.nth(1).inner_text().strip()
            maturity = tds.nth(2).inner_text().strip()
            coupon   = tds.nth(3).inner_text().strip()

            # 🔹 Fetch Secured / Unsecured
            security = get_security_status(page, issuer, isin)

            print(f"{issuer} | {isin} | {security}")

            data_rows.append([
                issuer,
                rating,
                isin,
                amount,
                maturity,
                coupon,
                security
            ])

        browser.close()

    # Push to Google Sheet
    SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
    WORKSHEET_NAME = "AAA"
    update_google_sheet_by_name(SHEET_ID, WORKSHEET_NAME, headers, data_rows)

if __name__ == "__main__":
    main()
'''
'''
from playwright.sync_api import sync_playwright
import time
import os
from google_sheets import update_google_sheet_by_name
import tempfile

# === Write secret JSON to temp file for gspread ===
SERVICE_ACCOUNT_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(os.environ["NEW"])

URL = "https://www.wintwealth.com/bonds/aaa-rated-bonds/"

# ---------- LOAD MORE ----------
def click_load_more_until_done(page, max_clicks=200):
    rows_locator = page.locator("tr.table-row-common")
    last_count = rows_locator.count()
    stalled_tries = 0

    for _ in range(max_clicks):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)

        btn = page.locator("button:has-text('Load more')")
        if btn.count() == 0:
            break

        btn.first.click(force=True)
        page.wait_for_timeout(1200)

        new_count = rows_locator.count()
        if new_count == last_count:
            stalled_tries += 1
            if stalled_tries >= 2:
                break
        else:
            last_count = new_count
            stalled_tries = 0

# ---------- SECURITY FETCH ----------
def get_security_status(detail_page, issuer, isin):
    slug = issuer.lower().strip().replace("&", "").replace(".", "").replace(" ", "-")
    url = f"https://www.wintwealth.com/bonds/{slug}/{isin.lower()}"

    try:
        detail_page.goto(url, timeout=60000)
        detail_page.wait_for_selector(
            "xpath=/html/body/div[2]/main/main/article/div[2]/div/div/section[1]/div[2]/div[1]/div[1]",
            timeout=15000
        )

        text = detail_page.locator(
            "xpath=/html/body/div[2]/main/main/article/div[2]/div/div/section[1]/div[2]/div[1]/div[1]"
        ).inner_text().strip().lower()

        # ✅ IMPORTANT: check UNSECURED first
        if text.startswith("unsecured"):
            return "UNSECURED"
        if text.startswith("secured"):
            return "SECURED"

        return "UNKNOWN"

    except Exception:
        return "UNKNOWN"


# ---------- MAIN ----------
def main():
    data_rows = []
    headers = ["Issuer", "Rating", "ISIN", "Amount", "Maturity", "Coupon", "Security"]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        list_page = browser.new_page()
        detail_page = browser.new_page()

        list_page.goto(URL, timeout=60000)
        list_page.wait_for_selector("tr.table-row-common", timeout=20000)
        click_load_more_until_done(list_page)

        rows = list_page.locator("tr.table-row-common")
        total = rows.count()
        print(f"\nTotal bonds found: {total}\n")

        for i in range(total):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() < 4:
                continue

            first_col = tds.nth(0).inner_text().strip()
            lines = [ln.strip() for ln in first_col.splitlines() if ln.strip()]

            issuer = lines[0] if len(lines) > 0 else ""
            rating = lines[1] if len(lines) > 1 else ""
            isin   = lines[2] if len(lines) > 2 else ""

            amount   = tds.nth(1).inner_text().strip()
            maturity = tds.nth(2).inner_text().strip()
            coupon   = tds.nth(3).inner_text().strip()

            # 🔹 Fetch security
            security = get_security_status(detail_page, issuer, isin)

            print(f"{i+1}. {issuer} | {isin} | {security}")

            data_rows.append([
                issuer,
                rating,
                isin,
                amount,
                maturity,
                coupon,
                security
            ])

        browser.close()

    # ---------- PUSH TO GOOGLE SHEET ----------
    SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
    WORKSHEET_NAME = "wint"
    update_google_sheet_by_name(SHEET_ID, WORKSHEET_NAME, headers, data_rows)

if __name__ == "__main__":
    main()'''
from playwright.sync_api import sync_playwright
import time
import os
from google_sheets import update_google_sheet_by_name
import tempfile

# =========================================================
# Google Sheets credentials (uses existing NEW secret)
# =========================================================
SERVICE_ACCOUNT_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(os.environ["NEW"])

# =========================================================
# CONFIG
# =========================================================
URL = "https://www.wintwealth.com/bonds/aaa-rated-bonds/"
LOAD_MORE_XPATH = "/html/body/div[2]/main/div[4]/div[1]/div[2]/div[3]/button"

SHEET_ID = "1QN5GMlxBKMudeHeWF-Kzt9XsqTt01am7vze1wBjvIdE"
WORKSHEET_NAME = "AAA"

HEADERS = [
    "Issuer",
    "Rating",
    "ISIN",
    "Amount",
    "Maturity",
    "Coupon",
    "Security"
]

# =========================================================
# LOAD MORE (ROBUST, XPATH-BASED)
# =========================================================
def click_load_more_until_done(page, max_clicks=200):
    rows_locator = page.locator("tr.table-row-common")

    for click_no in range(max_clicks):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)

        load_more = page.locator(f"xpath={LOAD_MORE_XPATH}")

        # Stop ONLY when button disappears
        if load_more.count() == 0:
            print("✅ Load more button disappeared. All bonds loaded.")
            break

        before = rows_locator.count()

        try:
            load_more.first.scroll_into_view_if_needed()
            load_more.first.click(force=True, timeout=5000)
            print(f"🔁 Clicked Load more ({click_no + 1})")
        except Exception as e:
            print("⚠ Click failed, retrying:", e)
            page.wait_for_timeout(1500)
            continue

        # Wait until rows increase
        for _ in range(12):
            page.wait_for_timeout(800)
            after = rows_locator.count()
            if after > before:
                print(f"📈 Rows increased: {before} → {after}")
                break

# =========================================================
# SECURITY (SECURED / UNSECURED) – FIXED LOGIC
# =========================================================
def get_security_status(detail_page, issuer, isin):
    slug = (
        issuer.lower()
        .strip()
        .replace("&", "")
        .replace(".", "")
        .replace(" ", "-")
    )
    url = f"https://www.wintwealth.com/bonds/{slug}/{isin.lower()}"

    try:
        detail_page.goto(url, timeout=60000)
        detail_page.wait_for_selector(
            "xpath=/html/body/div[2]/main/main/article/div[2]/div/div/section[1]/div[2]/div[1]/div[1]",
            timeout=15000
        )

        text = detail_page.locator(
            "xpath=/html/body/div[2]/main/main/article/div[2]/div/div/section[1]/div[2]/div[1]/div[1]"
        ).inner_text().strip().lower()

        # IMPORTANT: unsecured must be checked first
        if text.startswith("unsecured"):
            return "UNSECURED"
        if text.startswith("secured"):
            return "SECURED"

        return "UNKNOWN"

    except Exception:
        return "UNKNOWN"

# =========================================================
# MAIN
# =========================================================
def main():
    data_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        # Two pages: list + detail
        list_page = browser.new_page()
        detail_page = browser.new_page()

        # Open list page
        list_page.goto(URL, timeout=60000)
        list_page.wait_for_selector("tr.table-row-common", timeout=20000)

        # Load all rows
        click_load_more_until_done(list_page)

        rows = list_page.locator("tr.table-row-common")
        total = rows.count()
        print(f"\nTotal bonds found: {total}\n")

        for i in range(total):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() < 4:
                continue

            first_col = tds.nth(0).inner_text().strip()
            lines = [ln.strip() for ln in first_col.splitlines() if ln.strip()]

            issuer = lines[0] if len(lines) > 0 else ""
            rating = lines[1] if len(lines) > 1 else ""
            isin   = lines[2] if len(lines) > 2 else ""

            amount   = tds.nth(1).inner_text().strip()
            maturity = tds.nth(2).inner_text().strip()
            coupon   = tds.nth(3).inner_text().strip()

            security = get_security_status(detail_page, issuer, isin)

            print(f"{i+1}. {issuer} | {isin} | {security}")

            data_rows.append([
                issuer,
                rating,
                isin,
                amount,
                maturity,
                coupon,
                security
            ])

        browser.close()

    # Push to Google Sheet
    update_google_sheet_by_name(
        SHEET_ID,
        WORKSHEET_NAME,
        HEADERS,
        data_rows
    )

# =========================================================
if __name__ == "__main__":
    main()

