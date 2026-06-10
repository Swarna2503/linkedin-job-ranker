# 🤖 LinkedIn Job Ranker

An intelligent job search automation tool that scrapes LinkedIn job listings, evaluates them using AI, and sends personalized job digest emails with visa sponsorship insights.

## 📋 Overview

**LinkedIn Job Ranker** is a comprehensive Python pipeline that automates job hunting by:

1. **Collecting** LinkedIn job URLs using browser automation (Playwright)
2. **Scraping** detailed job information via LinkedIn's private API
3. **Filtering** out staffing/recruiting agencies and unwanted companies
4. **Evaluating** jobs using Google's Gemini LLM for semantic similarity matching
5. **Ranking** jobs by fit and visa sponsorship status
6. **Emailing** personalized job digest reports with top recommendations

## ✨ Key Features

- ✅ **Automated Job Collection** – Playwright-based browser automation to collect job URLs across multiple pages
- ✅ **LinkedIn API Scraping** – Direct API integration for detailed job descriptions and metadata
- ✅ **Smart Filtering** – Automatically blocks staffing companies, recruiters, and low-quality job postings
- ✅ **LLM-Powered Evaluation** – Uses Google Gemini to semantically match jobs to your profile
- ✅ **Visa Status Tracking** – Categorizes jobs by visa sponsorship availability
- ✅ **Email Digests** – Beautiful HTML emails with top job recommendations + full report attachments
- ✅ **Intelligent Caching** – Avoids re-processing and re-embedding jobs
- ✅ **Smart Mode** – Run only missing pipeline steps (no redundant work)
- ✅ **Customizable Prompts** – Easy to adjust candidate profile and evaluation criteria

## 🏗️ Architecture

```
main.py (Controller)
    ├── linkedin_url_collector.py → Collect LinkedIn job URLs
    ├── linkedin_api_scraper.py → Fetch job details via API
    ├── linkedin_minimizer.py → Clean & filter jobs
    ├── llm_job_evaluator.py → Score & rank jobs with LLM
    ├── job_digest_email.py → Build HTML digest
    └── email_sender.py → Send via Gmail SMTP
```


## 📦 Installation

### Prerequisites
- Python 3.10+
- Chrome browser (for Playwright automation)
- LinkedIn account with valid cookies
- Google Gemini API key
- Gmail account with app-specific password

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Swarna2503/linkedin-job-ranker.git
   cd linkedin-job-ranker
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install playwright python-dotenv google-genai requests tqdm numpy
   playwright install chromium
   ```

4. **Set up environment variables:**
   ```bash
   cp .env_example .env
   ```

5. **Configure `.env` file:**
   ```env
   # Google Gemini API
   GEMINI_API_KEY=your_gemini_api_key_here

   # LinkedIn Authentication (see Getting Cookies section)
   LI_AT=your_linkedin_li_at_cookie
   JSESSIONID=your_linkedin_jsessionid_cookie

   # Gmail Configuration
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_app_specific_password
   ```

---

## 🔐 Getting LinkedIn Cookies

1. **Log in to LinkedIn** in your browser
2. **Open DevTools** (F12 or Right-click → Inspect)
3. **Go to Application tab → Cookies**
4. **Find and copy:**
   - `li_at` – Your LinkedIn session token
   - `JSESSIONID` – Your session ID
5. **Paste into `.env` file** (keep the quotes if present)

## 🚀 Usage

### Run the Controller Menu

```bash
python main.py
```

You'll see an interactive menu:

```
==============================
   🤖 Job Agent Controller
==============================
1. Run FULL pipeline
2. Evaluate jobs only
3. Send email digest only
4. Collect URLs
5. Scrape job descriptions (skip if already scraped)
6. Minimize job fields
7. Smart Mode (run only missing steps)
0. Exit
==============================
```

### Quick Start (Full Pipeline)

```bash
python main.py
# Select option 1
```

This will:
1. Collect LinkedIn job URLs
2. Scrape job descriptions via LinkedIn API
3. Filter out unwanted companies
4. Evaluate jobs with Gemini LLM
5. Send email digest


## ⚙️ Configuration

### Customize Candidate Profile

Edit the `CANDIDATE_PROFILE` in `llm_job_evaluator.py`:

```python
CANDIDATE_PROFILE = """
MS Data Science (Rice), 2+ yrs experience.
Experience: [Your background]
Skills: [Your skills]
Target roles: [Desired positions]
"""
```

### Adjust Similarity Threshold

In `llm_job_evaluator.py`, modify `evaluate_all()`:

```python
evaluate_all(
    input_file="linkedin_minimized_jobs.json",
    output_file="scored_jobs.json",
    similarity_threshold=0.70,  # Increase to be stricter
    max_llm_jobs=50  # Limit LLM evaluations to top N jobs
)
```

### Block Companies

Edit blocked companies in `linkedin_minimizer.py`:

```python
BLOCKED_PHRASES = [
    
]

BLOCKED_TOKENS = [
    
]

BLOCKED_DOMAINS = [
    "your_domain.com",
]
```

### Customize Email Recipients

In `job_digest_email.py`, change:

```python
send_email(
    subject="Your Top Visa-Friendly Jobs Today",
    html_body=email_html,
    recipient="your_email@gmail.com",  # ← Change here
    attachments=[attachment_path]
)
```
## 📊 Output Files

| File | Purpose |
|------|---------|
| `linkedin_job_urls.txt` | Raw job URLs collected from LinkedIn |
| `seen_linkedin_urls.txt` | Persistent cache of all URLs ever seen (prevents duplicates) |
| `linkedin_api_jobs.json` | Raw job data from LinkedIn API (includes full raw JSON) |
| `linkedin_minimized_jobs.json` | Cleaned job data (blocked companies removed) |
| `scored_jobs.json` | Evaluated jobs with LLM scores and visa info |
| `embedding_cache.json` | Cached embeddings for performance |
| `all_jobs.html` | Full HTML report (email attachment) |

## ⚠️ Troubleshooting

### "Authentication Error" (LinkedIn)
- **Issue:** LI_AT or JSESSIONID missing/expired
- **Fix:** Refresh cookies (LinkedIn sessions expire periodically)
  ```bash
  # Manually update .env with fresh cookies
  ```

### "Throttled (HTTP 429)"
- **Issue:** LinkedIn rate-limiting
- **Fix:** Automatic retry with exponential backoff (built-in)
- **Manual:** Wait 5-10 minutes and re-run

### "HTTP 401/403 - Cookies expired"
- **Issue:** Session timeout
- **Fix:** Clear browser cookies and get fresh `li_at` and `JSESSIONID`

### "No jobs found on this page"
- **Issue:** LinkedIn page structure changed or pagination ended
- **Fix:** Manual inspection or adjust selectors in `linkedin_url_collector.py`

### "Missing .env file"
- **Issue:** No configuration
- **Fix:**
  ```bash
  cp .env_example .env
  # Edit .env with your credentials
  ```

### Gmail auth fails
- **Issue:** Using regular password instead of app password
- **Fix:** Generate app-specific password:
  1. Go to [Google Account Security](https://myaccount.google.com/security)
  2. Enable 2-step verification
  3. Generate app-specific password for Gmail
  4. Use that password in `.env`

## 🔒 Security

⚠️ **IMPORTANT:**
- Never commit `.env` to version control
- `.gitignore` protects sensitive files
- Cookies are session-specific and auto-expire
- Use app-specific Gmail passwords, not your main password

## 📈 Performance Tips

1. **Use Smart Mode** – Avoids redundant work
   ```bash
   python main.py  # Option 7
   ```

2. **Cache Embeddings** – Reuses computed vectors
   - Stored in `embedding_cache.json`
   - Automatically managed

3. **Batch Processing** – LLM calls are optimized
   - Default: Up to 50 jobs evaluated per run
   - Adjustable in `llm_job_evaluator.py`

4. **Persistent URL Tracking** – Avoids duplicate scraping
   - Stored in `seen_linkedin_urls.txt`


## 🤝 Contributing

Pull requests welcome! Areas for improvement:
- Support for other job boards (Indeed, Glassdoor, etc.)
- Database integration for historical job tracking
- Advanced filtering (salary range, remote preference)
- Scheduling automation (cron jobs)
- Dashboard/web UI


## ⚡ Limitations & Disclaimers

- **LinkedIn ToS:** This tool uses LinkedIn's private API. Use responsibly and respect their Terms of Service.
- **Rate Limiting:** LinkedIn throttles requests. Built-in backoff handles this, but delays may occur.
- **Cookie Expiry:** Sessions expire; you'll need to refresh cookies periodically.
- **API Costs:** Uses paid Google Gemini API for LLM evaluation (embeddings + generation).
- **Email Limits:** Gmail has daily sending limits (~500 emails/day).

## 📜 License

MIT License – Feel free to use and modify!

## 👤 Author

Created by **Swarna Durga Nallam**

## 🚨 Common Errors & Fixes

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError: linkedin_api_jobs.json` | Scraping skipped | Run Step 2 first |
| `Playwright not installed` | Missing dependency | `pip install playwright && playwright install chromium` |
| `Empty response from LLM` | API rate limit exceeded | Wait 30 minutes, try again |
| `JSON parse failed` | Malformed response | Retry; may be transient |
| `SMTP authentication failed` | Wrong Gmail app password | Generate new app password from Google Account |

## 📞 Support

For issues, questions, or feature requests:
1. Check this README's troubleshooting section
2. Review code comments in each module
3. Open an issue on GitHub

Happy job hunting! 🎉
