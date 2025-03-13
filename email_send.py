import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import csv

# Load environment variables from .env file
load_dotenv()

def send_email(to_email, subject, body):
    sender_email = os.getenv('SENDER_EMAIL')  # Email from .env file
    password = os.getenv('APP_PASSWORD')  # App password from .env file

    # Set up the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    # Attach the email body
    message.attach(MIMEText(body, "plain"))

    # Establish connection with Gmail's SMTP server
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {str(e)}")

def send_emails_from_csv(csv_file):
    with open(csv_file, newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            student_email = row['Email']
            student_name = row['Name']
            
            # Customize the email content
            subject = "Important Announcement"
            body = f"Hello {student_name},\n\nThis is an important message regarding the upcoming event."

            send_email(student_email, subject, body)

if __name__ == "__main__":
    csv_file = 'recipients.csv'  # Path to your CSV file
    send_emails_from_csv(csv_file)
