import requests
from bs4 import BeautifulSoup
import json
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

def scrape_job_description(url):
    """Scrape a single LinkedIn job posting page."""
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    title = (
        soup.select_one("h1.top-card-layout__title") or
        soup.select_one("h1.top-card__title") or
        soup.select_one("h1[class*='job-title']") or
        soup.select_one("h1")
    )

    company = (
        soup.select_one("a.topcard__org-name-link") or
        soup.select_one("a.topcard__flavor") or
        soup.select_one("span.topcard__flavor") or
        soup.select_one("a[class*='company']") or
        soup.select_one("span[class*='company']")
    )

    description = (
        soup.select_one("div.show-more-less-html") or
        soup.select_one("section.description") or
        soup.select_one("div.description__text") or
        soup.select_one("div[class*='description']") or
        soup.select_one("div[class*='jobs-description']") or
        soup.select_one("div.jobs-box__html-content")
    )

    def clean(el):
        return el.get_text("\n", strip=True) if el else None

    return {
        "url": url,
        "title": clean(title),
        "company": clean(company),
        "description": clean(description),
    }


def scrape_all_jobs(
    input_file="linkedin_job_urls.txt",
    output_file="linkedin_scraped_jobs.json"
):
    """Scrape all job URLs from the input file and save results."""
    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []
    total = len(urls)

    print(f"\n🚀 Scraping {total} LinkedIn job pages...\n")

    for i, url in enumerate(urls, start=1):
        print(f"🔎 [{i}/{total}] Scraping: {url}")

        try:
            data = scrape_job_description(url)

            if not data["description"]:
                print("⚠️ Missing description — retrying...")
                time.sleep(1)
                data = scrape_job_description(url)

            results.append(data)

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            results.append({
                "url": url,
                "title": None,
                "company": None,
                "description": None,
                "error": str(e)
            })

        time.sleep(0.5)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n🎉 Saved {len(results)} scraped jobs → {output_file}")


if __name__ == "__main__":
    scrape_all_jobs()
