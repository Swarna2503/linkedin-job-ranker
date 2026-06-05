# linkedin_minimizer.py

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "linkedin_api_jobs.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "linkedin_minimized_jobs.json")

KEEP_FIELDS = {
    "linkedin_url",
    "job_id",
    "title",
    "company",
    "location",
    "description",
    "ats_url",
}

def minimize_job(job: dict) -> dict:
    """Return only the fields needed for the evaluator."""
    return {k: job.get(k) for k in KEEP_FIELDS}

def minimize_all():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing {INPUT_FILE}")

    with open(INPUT_FILE) as f:
        jobs = json.load(f)

    minimized = [minimize_job(job) for job in jobs]

    with open(OUTPUT_FILE, "w") as f:
        json.dump(minimized, f, indent=2)

    print(f"✅ Minimized {len(minimized)} jobs → {OUTPUT_FILE}")