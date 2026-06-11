import json
import re

INPUT_FILE = "linkedin_scraped_jobs.json"
OUTPUT_FILE = "linkedin_minimized_jobs.json"

BLOCKED_COMPANIES = {
    "BeaconFire", "BeaconFire Inc", "BeaconFire Inc.",
    "Dice", "SysMind", "KPG99", "Tech Consulting",
    "Jack & Jill", "Jack Jill", "JackJill",
    "Talent Acquisition", "Consultancy Services"
}

def is_blocked(company):
    if not company:
        return False
    company_lower = company.lower()
    return any(b.lower() in company_lower for b in BLOCKED_COMPANIES)

def clean_text(value):
    if not value:
        return None
    return value.strip()

def minimize_all():
    with open(INPUT_FILE, "r") as f:
        jobs = json.load(f)

    cleaned = []
    skipped = 0
    counter = 1

    for job in jobs:
        company = clean_text(job.get("company"))
        title = clean_text(job.get("title"))
        description = clean_text(job.get("description"))
        url = clean_text(job.get("url"))

        # Skip blocked companies
        if is_blocked(company):
            skipped += 1
            continue

        # Skip invalid or empty descriptions
        if not description:
            skipped += 1
            continue

        cleaned.append({
            "job_id": f"job_{counter:04d}",
            "company": company,
            "title": title,
            "description": description,
            "url": url
        })

        counter += 1

    with open(OUTPUT_FILE, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"🎉 Minimization complete!")
    print(f"   → Saved {len(cleaned)} cleaned jobs → {OUTPUT_FILE}")
    print(f"   → Skipped {skipped} blocked or invalid jobs")

if __name__ == "__main__":
    minimize_all()
