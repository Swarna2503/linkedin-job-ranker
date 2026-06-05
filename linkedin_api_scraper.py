import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()

LI_AT = os.getenv("LI_AT")
JSESSIONID = os.getenv("JSESSIONID")

if not LI_AT or not JSESSIONID:
    raise RuntimeError("Missing LI_AT or JSESSIONID in .env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "linkedin_job_urls.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "linkedin_api_jobs.json")

HEADERS = {
    "authority": "www.linkedin.com",
    "accept": "application/vnd.linkedin.normalized+json+2.1",
    "csrf-token": JSESSIONID.replace('"', ""),
    "cookie": f"li_at={LI_AT}; JSESSIONID={JSESSIONID};",
    "user-agent": "Mozilla/5.0",
}

def extract_job_id(url: str):
    """Extract numeric job ID from a LinkedIn job URL."""
    match = re.search(r"/jobs/view/(\d+)", url)
    return match.group(1) if match else None

def fetch_job_json(job_id: str):
    """Call LinkedIn internal job API."""
    api_url = f"https://www.linkedin.com/voyager/api/jobs/jobPostings/{job_id}"
    resp = requests.get(api_url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"⚠️ Failed to fetch job {job_id}: HTTP {resp.status_code}")
        return None

    try:
        return resp.json()
    except:
        print(f"⚠️ Invalid JSON for job {job_id}")
        return None

def normalize_job_record(url: str, raw: dict):
    """Extract clean fields from LinkedIn job JSON."""
    data = raw.get("data", {})

    description = None
    desc_obj = data.get("description")
    if isinstance(desc_obj, dict):
        description = desc_obj.get("text")

    apply_method = data.get("applyMethod") or {}
    ats_url = apply_method.get("companyApplyUrl") or apply_method.get("easyApplyUrl")

    return {
        "linkedin_url": url,
        "job_id": data.get("entityUrn", "").split(":")[-1],
        "title": data.get("title"),
        "company": data.get("companyName"),
        "location": data.get("formattedLocation"),
        "description": description,
        "ats_url": ats_url,
        "raw": data,
    }

def scrape_linkedin_job(url: str):
    """Scrape a single LinkedIn job via internal API."""
    job_id = extract_job_id(url)
    if not job_id:
        print(f"❌ Invalid LinkedIn job URL: {url}")
        return None

    print(f"🌐 Fetching job {job_id} via LinkedIn API…")
    raw = fetch_job_json(job_id)
    if not raw:
        return None

    return normalize_job_record(url, raw)

def scrape_all():
    """Scrape all LinkedIn job URLs from linkedin_job_urls.txt."""
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing {INPUT_FILE}")

    urls = [u.strip() for u in open(INPUT_FILE).readlines() if u.strip()]
    results = []

    print(f"📄 Loaded {len(urls)} LinkedIn job URLs")

    for idx, url in enumerate(urls, 1):
        print(f"\n🔎 [{idx}/{len(urls)}] {url}")
        job = scrape_linkedin_job(url)
        if job:
            results.append(job)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Saved {len(results)} LinkedIn jobs to {OUTPUT_FILE}")