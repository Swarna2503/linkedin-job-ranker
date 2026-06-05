import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
    raise RuntimeError("Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in .env")

def send_email(subject: str, html_body: str, recipient: str, attachments=None):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    # Attach files
    if attachments:
        for file_path in attachments:
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file_path)}"
                )
                msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    print("Email sent successfully!")
