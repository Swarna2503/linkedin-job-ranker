import os
from linkedin_url_collector import collect_linkedin_job_urls
from linkedin_api_scraper import scrape_all
from linkedin_minimizer import minimize_all
from llm_job_evaluator import evaluate_all
from job_digest_email import send_job_digest

SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/?currentJobId=4423543221&distance=25.0&f_E=2&f_TPR=r86400&geoId=103644278&keywords=software%20engineer&origin=JOBS_HOME_KEYWORD_HISTORY"
)

def file_exists(path: str) -> bool:
    return os.path.exists(path) and os.path.getsize(path) > 0

def run_full_pipeline():
    print("\n🚀 Running FULL Job Agent Pipeline...\n")

    print("📌 Step 1: Collecting LinkedIn job URLs...")
    collect_linkedin_job_urls(SEARCH_URL, max_pages=25)

    print("📌 Step 2: Scraping job descriptions...")
    scrape_all()

    print("📌 Step 3: Minimizing job fields...")
    minimize_all()

    print("📌 Step 4: Evaluating jobs...")
    evaluate_all(
        input_file="linkedin_minimized_jobs.json",
        output_file="scored_jobs.json"
    )

    print("📌 Step 5: Sending job digest email...")
    send_job_digest()

    print("\n🎉 FULL PIPELINE COMPLETE!\n")

def menu():
    print("\n==============================")
    print("   🤖 Job Agent Controller")
    print("==============================")
    print("1. Run FULL pipeline")
    print("2. Evaluate jobs only")
    print("3. Send email digest only")
    print("4. Collect URLs")
    print("5. Scrape job descriptions (skip if already scraped)")
    print("6. Minimize job fields")
    print("7. Smart Mode (run only missing steps)")
    print("0. Exit")
    print("==============================")

    return input("Select an option: ").strip()

def smart_mode():
    print("\n🧠 Smart Mode Activated — Running only missing steps...\n")

    if not file_exists("linkedin_job_urls.txt"):
        print("📌 Step 1: Collecting URLs...")
        collect_linkedin_job_urls(SEARCH_URL, max_pages=25)
    else:
        print("⚠️ Step 1 skipped — URLs already collected.")

    if not file_exists("linkedin_api_jobs.json"):
        print("📌 Step 2: Scraping job descriptions...")
        scrape_all()
    else:
        print("⚠️ Step 2 skipped — Scraped data already exists.")

    if not file_exists("linkedin_minimized_jobs.json"):
        print("📌 Step 3: Minimizing job fields...")
        minimize_all()
    else:
        print("⚠️ Step 3 skipped — Minimized data already exists.")

    if not file_exists("scored_jobs.json"):
        print("📌 Step 4: Evaluating jobs...")
        evaluate_all(
            input_file="linkedin_minimized_jobs.json",
            output_file="scored_jobs.json"
        )
    else:
        print("⚠️ Step 4 skipped — Evaluation already exists.")

    print("📌 Step 5: Sending job digest email...")
    send_job_digest()

    print("\n🎉 Smart Mode Complete!\n")

def main():
    while True:
        choice = menu()

        if choice == "1":
            run_full_pipeline()

        elif choice == "2":
            print("\n📌 Running Step 4: Evaluating jobs...")
            evaluate_all(
                input_file="linkedin_minimized_jobs.json",
                output_file="scored_jobs.json"
            )
            print("✅ Evaluation complete\n")

        elif choice == "3":
            print("\n📌 Running Step 5: Sending job digest email...")
            send_job_digest()
            print("📨 Email sent!\n")

        elif choice == "4":
            print("\n📌 Running Step 1: Collecting URLs...")
            collect_linkedin_job_urls(SEARCH_URL, max_pages=25)
            print("✅ URLs collected\n")

        elif choice == "5":
            print("\n📌 Running Step 2: Scraping job descriptions...")

            if file_exists("linkedin_api_jobs.json"):
                print("⚠️ Scraped data already exists — skipping Step 2.")
            else:
                scrape_all()
                print("✅ Scraping complete\n")

        elif choice == "6":
            print("\n📌 Running Step 3: Minimizing job fields...")
            minimize_all()
            print("✅ Minimization complete\n")

        elif choice == "7":
            smart_mode()

        elif choice == "0":
            print("\n👋 Exiting Job Agent. Goodbye!\n")
            break

        else:
            print("\n❌ Invalid choice. Try again.\n")


if __name__ == "__main__":
    main()
