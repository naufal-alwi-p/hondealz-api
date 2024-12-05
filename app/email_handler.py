import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = os.environ["SENDER_EMAIL"] # Wajib buat env variabel sendiri
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"] # Wajib buat env variabel sendiri

def send_reset_password_email(receiver_email: str, body: str):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email
    message["Subject"] = "Reset Password HonDealz App"

    message.attach(MIMEText(body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(message)
