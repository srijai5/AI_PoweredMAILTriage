import os
import email
import imaplib
import smtplib
from email.header import decode_header
from email.message import EmailMessage
from email.header import decode_header
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

genai.configure(api_key='AIXXXXXXXXXXXXXXXXXXXxxjNwU')

URGENT_KEYWORDS = {
    "urgent", "asap", "immediately", "important", "action required",
    "attention", "critical", "high priority", "response needed",
    "reply asap", "deadline", "emergency", "immediate action", "top priority",
}

def is_urgent(subject):
    subject = (subject or "").lower()
    return any(word in subject for word in URGENT_KEYWORDS)

def extract_name(addr):
    local = addr.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ")
    return local.title()

def generate_reply(subject, sender_email):
    model = genai.GenerativeModel("gemini-2.0-flash")
    name = extract_name(sender_email)
    prompt = (
        f"Write a concise, professional reply to an email with subject: '{subject}'. "
        f"Greet the sender by the name '{name}', and end with a short sign-off with the name srija."
    )
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        return f"[Gemini error: {e}]"
def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = f"Re: {subject}"
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
            smtp.send_message(msg)
        print(f" Email sent to {to_email}")
    except Exception as e:
        print(f" Failed to send email to {to_email}: {e}")

def fetch_unread_emails():
    urgent, normal = [], []

    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
        mail.login(SMTP_EMAIL, SMTP_PASSWORD)
        mail.select("inbox")

        status, ids = mail.search(None, "(UNSEEN)")
        id_list = ids[0].split()

        for eid in id_list:
            status, data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])
            raw_subj = msg.get("Subject", "")
            dh = decode_header(raw_subj)
            subject = "".join(
                part.decode(charset or "utf-8") if isinstance(part, bytes) else part
                for part, charset in dh
            )
            from_email = email.utils.parseaddr(msg.get("From", ""))[1]
            item = {"from": from_email, "subject": subject}

            if is_urgent(subject):
                ai_reply = generate_reply(subject, from_email)
                item["reply"] = ai_reply
                send_email(from_email, subject, ai_reply)  
                urgent.append(item)
            else:
                normal.append(item)

            mail.store(eid, "+FLAGS", "\\Seen")

    return urgent, normal
