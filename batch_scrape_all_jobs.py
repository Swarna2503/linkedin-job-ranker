import json
import time
from linkedin_html_scraper import scrape_job_description

INPUT_FILE = "linkedin_job_urls.txt"
OUTPUT_FILE = "linkedin_scraped_jobs.json"

def load_urls():
    with open(INPUT_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def batch_scrape():
    urls = load_urls()
    results = []
    total = len(urls)

    print(f"🚀 Starting batch scrape for {total} job URLs...\n")

    for i, url in enumerate(urls, start=1):
        print(f"🔎 [{i}/{total}] Scraping: {url}")

        try:
            data = scrape_job_description(url)

            if not data["description"]:
                print("⚠️ Description missing — retrying once...")
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

        time.sleep(0.5)  # polite delay

    print("\n💾 Saving results...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"🎉 Done! Scraped {len(results)} jobs → {OUTPUT_FILE}")

if __name__ == "__main__":
    batch_scrape()
