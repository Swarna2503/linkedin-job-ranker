import os
import json
import re

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
}

BLOCKED_PHRASES = [
    "jobs via dice",
    "insight global",
    "global consulting",
]

BLOCKED_TOKENS = [
    "beaconfire",
    "sysmind",
    "kforce",
    "revature",
    "hcl",
    "staffing",
    "recruiter",
    "knowfinity",
]

BLOCKED_DOMAINS = [
    "jobright.ai",
]

def extract_all_text(obj):
    """Recursively extract all text from raw JSON."""
    texts = []

    if isinstance(obj, dict):
        for v in obj.values():
            texts.extend(extract_all_text(v))

    elif isinstance(obj, list):
        for item in obj:
            texts.extend(extract_all_text(item))

    elif isinstance(obj, str):
        texts.append(obj.lower())

    return texts


def detect_blocked_company(job: dict) -> bool:
    """
    Detect staffing / blocked companies using phrases, tokens, and domains.
    Includes guard: if raw is missing, assume already minimized → skip blocking.
    """
    if "raw" not in job:
        return False

    raw = job["raw"]
    all_text = " ".join(extract_all_text(raw))

    for dom in BLOCKED_DOMAINS:
        if dom in all_text:
            return True

    for phrase in BLOCKED_PHRASES:
        if phrase in all_text:
            return True

    for tok in BLOCKED_TOKENS:
        if re.search(rf"\b{re.escape(tok)}\b", all_text):
            return True

    return False


def minimize_job(job: dict) -> dict:
    """Return minimized job fields only."""
    return {k: job.get(k) for k in KEEP_FIELDS}


def minimize_all():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing {INPUT_FILE}")

    with open(INPUT_FILE) as f:
        jobs = json.load(f)

    minimized = []

    for job in jobs:
        if detect_blocked_company(job):
            continue  

        minimized.append(minimize_job(job))

    with open(OUTPUT_FILE, "w") as f:
        json.dump(minimized, f, indent=2)

    print(f"Saved {len(minimized)} clean jobs → {OUTPUT_FILE}")
    
if __name__ == "__main__":
    minimize_all()
