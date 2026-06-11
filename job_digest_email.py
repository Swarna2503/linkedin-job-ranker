import json
from email_sender import send_email

def load_jobs(path="scored_jobs.json"):
    with open(path) as f:
        return json.load(f)

def build_html(jobs):
    html = """
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2>Your Top Visa-Friendly Jobs Today</h2>
    """

    for job in jobs:
        html += f"""
        <div style="border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:8px;">
            <h3>{job['title']} — {job['company']}</h3>
            <p><strong>Score:</strong> {job['score']}</p>
            <p><strong>Visa:</strong> {job['visa_block']}</p>
            <p><strong>Reason:</strong> {job.get('reason', 'No reason provided')}</p>
            <a href="{job['linkedin_url']}"
               style="display:inline-block; padding:10px 15px; background:#0073b1; color:white; text-decoration:none; border-radius:5px;">
               Apply Now
            </a>
        </div>
        """

    html += "</body></html>"
    return html

def send_job_digest():
    jobs = load_jobs()

    # ⭐ Top 20 jobs for the email body
    top_20 = jobs[:20]
    email_html = build_html(top_20)

    # ⭐ Full job list saved as HTML attachment
    full_html = build_html(jobs)
    attachment_path = "all_jobs.html"
    with open(attachment_path, "w") as f:
        f.write(full_html)

    # ⭐ Send email with top 20 + attachment
    send_email(
        subject="Your Top Visa-Friendly Jobs Today",
        html_body=email_html,
        recipient="swarnadurga.nallam@gmail.com",
        attachments=[attachment_path]
    )
