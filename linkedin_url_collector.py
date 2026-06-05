from playwright.sync_api import sync_playwright
import time
import os
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

AUTOMATION_PROFILE = "/Users/swarna/automation_profile"
os.makedirs(AUTOMATION_PROFILE, exist_ok=True)

# All possible job list containers LinkedIn uses
JOB_LIST_SELECTORS = [
    "div.jobs-search-results-list",
    "div.scaffold-layout__list-container",
    "ul.jobs-search__results-list",
    "div.jobs-search-two-pane__results-list"
]

def find_job_container(page):
    for selector in JOB_LIST_SELECTORS:
        if page.locator(selector).count() > 0:
            return page.locator(selector)
    return None

def scroll_everything(page, steps=10):
    for _ in range(steps):
        page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                for (const el of elements) {
                    if (el.scrollHeight > el.clientHeight) {
                        el.scrollBy(0, 2000);
                    }
                }
            }
        """)
        time.sleep(0.8)

def scroll_job_list(page):
    container = find_job_container(page)
    if container:
        for _ in range(10):
            container.evaluate("el => el.scrollBy(0, 2000)")
            time.sleep(0.5)
    else:
        scroll_everything(page)

def collect_jobs_from_page(page):
    urls = set()
    job_cards = page.locator("a[href*='/jobs/view/']").all()

    for card in job_cards:
        href = card.get_attribute("href")
        if href and "/jobs/view/" in href:
            job_id = href.split("/jobs/view/")[1].split("/")[0]
            urls.add(f"https://www.linkedin.com/jobs/view/{job_id}/")

    return urls

def add_start_param(url, start_value):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["start"] = [str(start_value)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def collect_linkedin_job_urls(base_url: str, max_pages: int = 25) -> list[str]:
    all_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=AUTOMATION_PROFILE,
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page()

        print("🌐 Opening LinkedIn...")
        page.goto("https://www.linkedin.com", timeout=0)

        print("\n🔐 Log in manually, then press ENTER.")
        input()

        page.goto(base_url, timeout=0)
        time.sleep(2)

        for page_index in range(max_pages):
            print(f"\n📄 Collecting page {page_index+1}")

            scroll_job_list(page)

            page_urls = collect_jobs_from_page(page)
            print(f"🔍 Found {len(page_urls)} jobs on this page")
            all_urls |= page_urls

            next_button = page.locator("button[aria-label='Next']").first

            if next_button.count() > 0 and not next_button.is_disabled():
                print("➡️ Clicking NEXT button...")
                next_button.click()
                time.sleep(3)
                continue

            start_value = (page_index + 1) * 25
            fallback_url = add_start_param(base_url, start_value)
            print(f"➡️ NEXT not found. Loading fallback URL: start={start_value}")
            page.goto(fallback_url, timeout=0)
            time.sleep(2)

            if len(page_urls) == 0:
                print("⛔ No more jobs. Stopping.")
                break

        print("\n🛑 Closing browser safely...")
        browser.close()

    print(f"\n✅ TOTAL JOBS COLLECTED: {len(all_urls)}")

    # ⭐ Save URLs to file
    with open("linkedin_job_urls.txt", "w") as f:
        for url in all_urls:
            f.write(url + "\n")

    print("📄 Saved all job URLs to linkedin_job_urls.txt")

    return list(all_urls)
