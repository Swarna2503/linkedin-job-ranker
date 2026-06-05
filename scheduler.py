# scheduler.py

import schedule
import time
import subprocess

def send_digest():
    print("⏰ Running daily job digest...")
    subprocess.run(["python", "job_digest_email.py"])

# Run every day at 10 AM CST
schedule.every().day.at("19:40").do(send_digest)

print("📌 Daily job digest scheduler started (7:00 PM CST).")

while True:
    schedule.run_pending()
    time.sleep(30)
