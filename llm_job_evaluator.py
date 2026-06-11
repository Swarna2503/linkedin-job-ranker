import os
import json
import re
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tqdm import tqdm

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Authentication credentials missing or empty.")

client = genai.Client(api_key=API_KEY)

GEN_MODEL = "gemini-2.5-flash-lite"
EMB_MODEL = "gemini-embedding-001"
EMBED_CACHE_FILE = "embedding_cache.json"

# -----------------------------
# Embedding Cache
# -----------------------------
if os.path.exists(EMBED_CACHE_FILE):
    with open(EMBED_CACHE_FILE, "r") as f:
        EMBED_CACHE = json.load(f)
else:
    EMBED_CACHE = {}

EMBED_CACHE_LOCK = Lock()


def save_cache():
    with EMBED_CACHE_LOCK:
        with open(EMBED_CACHE_FILE, "w") as f:
            json.dump(EMBED_CACHE, f)


def embed_chunk(chunk, keys):
    """Embed a chunk of texts and write vectors into the shared cache."""
    result = client.models.embed_content(
        model=EMB_MODEL,
        contents=chunk,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
    )
    vectors = [e.values for e in result.embeddings]

    with EMBED_CACHE_LOCK:
        for key, vec in zip(keys, vectors):
            EMBED_CACHE[key] = vec

    return vectors


def cached_batch_embed(text_list, cache_keys, batch_size=100, workers=4):
    """Embed only missing items, chunked + parallel + cached."""
    to_embed, embed_keys = [], []
    final_vectors = [None] * len(text_list)

    for i, key in enumerate(cache_keys):
        if key in EMBED_CACHE:
            final_vectors[i] = np.array(EMBED_CACHE[key], dtype=float)
        else:
            to_embed.append(text_list[i])
            embed_keys.append(key)

    if not to_embed:
        return final_vectors

    chunks = [
        (to_embed[i:i + batch_size], embed_keys[i:i + batch_size])
        for i in range(0, len(to_embed), batch_size)
    ]

    print(f"\n🔹 Embedding {len(to_embed)} new items in {len(chunks)} batches...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(embed_chunk, chunk, keys) for chunk, keys in chunks]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Embedding"):
            try:
                future.result()
            except Exception as e:
                print(f"[WARN] Embedding batch failed: {e!r}")

    save_cache()

    for i, key in enumerate(cache_keys):
        final_vectors[i] = np.array(EMBED_CACHE[key], dtype=float)

    return final_vectors


# -----------------------------
# Candidate Profile
# -----------------------------
CANDIDATE_PROFILE = """
MS Computer Science (Rice), 2+ yrs experience.
Experience: Built AI agents, OCR systems, and automation platforms. Developed LLM/RAG applications and natural-language-to-SQL agents. Full-stack development experience at Barclays. Teaching Assistant for graduate NLP and Deep Learning courses.
Skills: Python, SQL, Java, PyTorch, TensorFlow, LLMs, RAG, NLP, Google ADK, Gemini, AWS, GCP, Spark, BigQuery, MongoDB, React.
Target roles: Software Engineer, FullStack Engineer, AI Engineer, ML Engineer, LLM Engineer, NLP Engineer, Data Scientist.
"""


def cosine(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def visa_priority(value: str) -> int:
    if value == "Provides sponsorship":
        return 0
    if value == "Unknown":
        return 1
    return 2


# -----------------------------
# Main Evaluator
# -----------------------------
def evaluate_all(
    input_file="linkedin_minimized_jobs.json",
    output_file="scored_jobs.json",
    similarity_threshold=0.70,
    max_llm_jobs=50,
):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Missing {input_file}")

    with open(input_file) as f:
        jobs = json.load(f)

    # Normalize descriptions
    descriptions = [(job.get("description") or "").strip() for job in jobs]

    # Embed candidate profile
    candidate_vec = cached_batch_embed(
        [CANDIDATE_PROFILE],
        ["candidate_profile"],
    )[0]

    # Embed job descriptions
    job_cache_keys = [f"job_{job['job_id']}" for job in jobs]
    job_vecs = cached_batch_embed(descriptions, job_cache_keys)

    # Similarity filtering
    scored = []
    for job, vec in zip(jobs, job_vecs):
        sim = cosine(candidate_vec, vec)
        if sim >= similarity_threshold:
            scored.append((sim, job))

    scored.sort(reverse=True, key=lambda x: x[0])
    selected = scored[:max_llm_jobs]

    # Load existing results
    completed = {}
    results = []

    if os.path.exists(output_file):
        with open(output_file) as f:
            results = json.load(f)
        for item in results:
            jid = item.get("job_id")
            if jid:
                completed[jid] = item

    print(f"\n🔍 Running LLM evaluation on {len(selected)} jobs...\n")

    # LLM evaluation
    for sim, job in tqdm(selected, desc="LLM Evaluating"):
        job_id = job["job_id"]

        if job_id in completed:
            continue

        prompt = f"""
You are a senior hiring manager and precise job evaluator.
Return ONLY valid JSON.

Job Title: {job.get('title')}
Company: {job.get('company')}
LinkedIn URL: {job.get('url')}
Job ID: {job_id}
Similarity Score: {sim}

<job_description>
{job.get('description')}
</job_description>

Candidate Profile:
{CANDIDATE_PROFILE}

Return ONLY this JSON:

{{
  "company": "",
  "title": "",
  "linkedin_url": "",
  "job_id": "",
  "score": 0,
  "visa_block": "",
  "reason": ""
}}
"""

        try:
            resp = client.models.generate_content(
                model=GEN_MODEL,
                contents=prompt,
                config={"temperature": 0.1},
            )
        except Exception as e:
            print(f"[WARN] LLM call failed for job {job_id}: {e!r}")
            continue

        # Extract text
        parts = []
        for c in resp.candidates[0].content.parts:
            if hasattr(c, "text"):
                parts.append(c.text)

        raw = "".join(parts).strip()

        # Extract JSON
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            print(f"[WARN] No JSON found for job {job_id}")
            continue

        try:
            parsed = json.loads(match.group(0))
        except Exception as e:
            print(f"[WARN] JSON parse failed for job {job_id}: {e!r}")
            continue

        results.append(parsed)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

    # Final sorting
    results = sorted(
        results,
        key=lambda x: (
            visa_priority(x.get("visa_block", "Unknown")),
            -x.get("score", 0)
        ),
    )

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n Saved {len(results)} optimized, visa-friendly jobs → {output_file}")
