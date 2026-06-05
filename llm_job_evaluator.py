import os
import json
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

client = genai.Client(api_key=API_KEY)

GEN_MODEL = "gemini-2.5-flash"
EMB_MODEL = "gemini-embedding-001"   

BLOCKED_COMPANIES = [
    "beaconfire", "dice", "jobs via dice", "sysmind", "sysmind llc",
    "kforce", "insight global", "revature", "hcl", "global consulting",
    "staffing", "recruiter"
]

def is_blocked(job: dict) -> bool:
    text = (
        (job.get("company") or "") + " " +
        (job.get("title") or "") + " " +
        (job.get("description") or "")
    ).lower()
    return any(bad in text for bad in BLOCKED_COMPANIES)

CANDIDATE_PROFILE = """
MS Data Science (Rice), 2+ yrs experience.
Experience: Built AI agents, OCR systems, and automation platforms. Developed LLM/RAG applications and natural-language-to-SQL agents. Full-stack development experience at Barclays. Teaching Assistant for graduate NLP and Deep Learning courses.
Skills: Python, SQL, Java, PyTorch, TensorFlow, LLMs, RAG, NLP, Google ADK, Gemini, AWS, GCP, Spark, BigQuery, MongoDB, React.
Target roles: Software Engineer, FullStack Engineer, AI Engineer, ML Engineer, LLM Engineer, NLP Engineer, Data Scientist.
"""

EMBED_CACHE_FILE = "embedding_cache.json"

if os.path.exists(EMBED_CACHE_FILE):
    with open(EMBED_CACHE_FILE, "r") as f:
        EMBED_CACHE = json.load(f)
else:
    EMBED_CACHE = {}

def save_cache():
    with open(EMBED_CACHE_FILE, "w") as f:
        json.dump(EMBED_CACHE, f)

def embed(text: str, cache_key: str) -> np.ndarray:
    if cache_key in EMBED_CACHE:
        return np.array(EMBED_CACHE[cache_key], dtype=float)

    if not text:
        text = " "

    result = client.models.embed_content(
        model=EMB_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
    )

    vec = result.embeddings[0].values
    EMBED_CACHE[cache_key] = vec
    save_cache()

    return np.array(vec, dtype=float)

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

print("🔹 Computing candidate embedding once...")
CANDIDATE_VEC = embed(CANDIDATE_PROFILE, "candidate_profile")

def evaluate_job(job: dict) -> dict:
    desc = job.get("description") or ""

    job_id = job.get("job_id") or f"hash_{abs(hash(desc))}"
    cache_key = f"job_{job_id}"

    job_vec = embed(desc, cache_key)
    similarity = cosine(CANDIDATE_VEC, job_vec)

    if similarity < 0.50:
        return {
            "company": job.get("company"),
            "title": job.get("title"),
            "location": job.get("location"),
            "linkedin_url": job.get("linkedin_url"),
            "job_id": job.get("job_id"),
            "score": int(similarity * 100),
            "should_apply": False,
            "visa_block": "Unknown",
            "reason": "Low similarity (<50). Skipped LLM to save cost."
        }

    prompt = f"""
You are a precise job-match evaluator. Extract missing fields and evaluate the job.

Job Title: {job.get('title')}
Company (may be null): {job.get('company')}
Location: {job.get('location')}
LinkedIn URL: {job.get('linkedin_url')}
Job ID: {job.get('job_id')}

Job Description:
{desc}

Candidate Profile:
{CANDIDATE_PROFILE}

Skill similarity score (0–1): {similarity}

Your tasks:
1. Infer the company name from the job description if missing.
2. Determine visa sponsorship status:
   - "Provides sponsorship"
   - "Does not sponsor visas"
   - "Unknown"
3. Decide if the candidate should apply.
4. Provide a short explanation in a field called "reason".
5. Produce a final JSON object in this exact order:

{{
  "company": "<company name>",
  "title": "<job title>",
  "location": "<location>",
  "linkedin_url": "<linkedin url>",
  "job_id": "<job id>",
  "score": <0-100>,
  "should_apply": <true/false>,
  "visa_block": "<Provides sponsorship | Does not sponsor visas | Unknown>",
  "reason": "<1–2 sentence explanation>"
}}

Return ONLY valid JSON.
"""

    resp = client.models.generate_content(
        model=GEN_MODEL,
        contents=prompt,
        config={"temperature": 0.1}
    )

    try:
        raw = "".join(
            part.text for part in resp.candidates[0].content.parts
            if hasattr(part, "text")
        )
    except:
        raw = ""

    if not raw.strip():
        return {
            "company": job.get("company"),
            "title": job.get("title"),
            "location": job.get("location"),
            "linkedin_url": job.get("linkedin_url"),
            "job_id": job.get("job_id"),
            "score": int(similarity * 100),
            "should_apply": False,
            "visa_block": "Unknown",
            "reason": "LLM returned empty response."
        }

    import re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {
            "company": job.get("company"),
            "title": job.get("title"),
            "location": job.get("location"),
            "linkedin_url": job.get("linkedin_url"),
            "job_id": job.get("job_id"),
            "score": int(similarity * 100),
            "should_apply": False,
            "visa_block": "Unknown",
            "reason": "LLM returned invalid JSON."
        }

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except:
        return {
            "company": job.get("company"),
            "title": job.get("title"),
            "location": job.get("location"),
            "linkedin_url": job.get("linkedin_url"),
            "job_id": job.get("job_id"),
            "score": int(similarity * 100),
            "should_apply": False,
            "visa_block": "Unknown",
            "reason": "LLM failed to parse JSON."
        }

def visa_priority(value: str) -> int:
    if value == "Provides sponsorship":
        return 0
    if value == "Unknown":
        return 1
    return 2

def evaluate_all(
    input_file="linkedin_minimized_jobs.json",
    output_file="scored_jobs.json"
):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Missing {input_file}")

    with open(input_file) as f:
        jobs = json.load(f)

    results = []

    for idx, job in enumerate(jobs, start=1):
        print(f"\n[{idx}/{len(jobs)}] Evaluating: {job.get('title')} at {job.get('company')}")

        if is_blocked(job):
            print(f"⛔ Skipping blocked company: {job.get('company')}")
            results.append({
                "company": job.get("company"),
                "title": job.get("title"),
                "location": job.get("location"),
                "linkedin_url": job.get("linkedin_url"),
                "job_id": job.get("job_id"),
                "score": 0,
                "should_apply": False,
                "visa_block": "Unknown",
                "reason": "Blocked company (staffing/recruiter spam)"
            })
            continue

        eval_result = evaluate_job(job)

        if eval_result["visa_block"] == "Does not sponsor visas":
            continue

        results.append(eval_result)

    results = sorted(
        results,
        key=lambda x: (visa_priority(x["visa_block"]), -x["score"])
    )

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Saved {len(results)} visa‑friendly, sorted jobs to {output_file}")
