import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

def build_search_url(query, location):
    return (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={quote_plus(query)}"
        f"&location={quote_plus(location)}"
        "&f_TPR=r86400"     # last 24 hours
        "&f_E=2"            # entry level
        "&sortBy=DD"        # most recent
    )

def collect_job_urls(query="software engineer",
                     location="United States",
                     max_pages=25,
                     output_file="linkedin_job_urls.txt"):

    print("\n🚀 Collecting LinkedIn job URLs (HTML scraper)...")

    search_url = build_search_url(query, location)
    all_urls = set()

    for page in range(max_pages):
        start = page * 25
        url = f"{search_url}&start={start}"

        print(f"🔎 Fetching page {page+1} → start={start}")
        resp = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")

        job_cards = soup.select("a.base-card__full-link")

        if not job_cards:
            print("⚠️ No job cards found — stopping early.")
            break

        for card in job_cards:
            job_url = card.get("href")
            if job_url:
                clean_url = job_url.split("?")[0]
                all_urls.add(clean_url)

        time.sleep(1)

    all_urls = sorted(all_urls)

    with open(output_file, "w") as f:
        f.write("\n".join(all_urls))

    print(f"\n💾 Saved {len(all_urls)} job URLs → {output_file}")
    return all_urls


if __name__ == "__main__":
    collect_job_urls()
