import smtplib
import random
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================================
# 🔧 CONFIGURATION
# ================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "subramanian160104@gmail.com"   # sender Gmail
SMTP_PASSWORD = "eblk crdk yfsj gvcb"       # App password (not normal Gmail password)

RECEIVER_EMAIL = "subramanian160104@gmail.com"  # You can send to same account for IMAP testing

# ================================
# 🧾 SAMPLE COMPLAINT TEMPLATES
# ================================
complaint_templates = [
    {
        "subject": "Billing Error in Last Invoice",
        "body": "Dear Team, I was charged twice for my last order. Please check and refund the excess amount."
    },
    {
        "subject": "Product Defective After Two Days",
        "body": "Hello, my washing machine stopped working after just two days of use. Kindly replace or repair it."
    },
    {
        "subject": "Late Delivery Issue",
        "body": "My parcel was supposed to arrive on Monday but came 4 days late. This caused me inconvenience."
    },
    {
        "subject": "App Not Loading Properly",
        "body": "I am unable to open the company app; it keeps crashing. Please fix this issue at the earliest."
    },
    {
        "subject": "Request for Refund - Order #23984",
        "body": "The product I received was not as described. I would like to request a full refund for this order."
    },
    {
        "subject": "Customer Service Experience",
        "body": "Your representative was very polite and helped me resolve my issue quickly. Thank you for the support!"
    },
    {
        "subject": "Subscription Renewal Problem",
        "body": "My subscription renewal failed even though I had sufficient balance. Please check this issue."
    }
]

general_emails = [
    {
        "subject": "Monthly Newsletter",
        "body": "Here's your monthly update with new offers and discounts!"
    },
    {
        "subject": "Thank You for Being a Loyal Customer",
        "body": "We appreciate your continued trust in our service."
    },
    {
        "subject": "Upcoming Maintenance Notification",
        "body": "Please note our systems will be under maintenance on Sunday from 2 AM to 4 AM."
    }
]

# ================================
# ✉️ FUNCTION TO SEND EMAIL
# ================================
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent: {subject}")

    except Exception as e:
        print(f"❌ Failed to send email: {subject} | Error: {e}")

# ================================
# 🚀 MAIN EXECUTION
# ================================
if __name__ == "__main__":
    total_emails = 10  # number of test emails to send
    for i in range(total_emails):
        # randomly decide whether to send complaint or general mail
        if random.random() < 0.8:  # 80% chance it's a complaint
            email = random.choice(complaint_templates)
        else:
            email = random.choice(general_emails)
        
        send_email(email["subject"], email["body"])
        
        # delay between sends to simulate real users
        time.sleep(random.randint(3, 10))
