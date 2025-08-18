from playwright.sync_api import sync_playwright
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
