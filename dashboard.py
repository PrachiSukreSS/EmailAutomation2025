import tkinter as tk
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
import sqlite3

# Load environment variables from .env file
load_dotenv()

# Create or connect to SQLite database
conn = sqlite3.connect('email_responses.db')
c = conn.cursor()

# Create a table for storing email responses
c.execute('''CREATE TABLE IF NOT EXISTS responses 
             (id INTEGER PRIMARY KEY, sender TEXT, subject TEXT, seen INTEGER)''')
conn.commit()

# Function to create a simple dashboard UI
def create_dashboard():
    root = tk.Tk()
    root.title("Email Response Dashboard")
    
    # Adjusted window size for better visibility
    root.geometry("600x600")
    
    # Label for the dashboard
    tk.Label(root, text="Email Responses", font=("Helvetica", 16, "bold")).pack(pady=10)

    # Frame to hold responses with checkboxes, adding a scrollbar for better usability
    response_frame = tk.Frame(root)
    response_frame.pack(fill="both", expand=True, pady=10)

    # Add a scrollbar to the response frame
    response_canvas = tk.Canvas(response_frame)
    scrollbar = tk.Scrollbar(response_frame, orient="vertical", command=response_canvas.yview)
    response_list = tk.Frame(response_canvas)

    response_list.bind(
        "<Configure>",
        lambda e: response_canvas.configure(scrollregion=response_canvas.bbox("all"))
    )

    response_canvas.create_window((0, 0), window=response_list, anchor="nw")
    response_canvas.configure(yscrollcommand=scrollbar.set)

    response_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Button to check for new email responses
    tk.Button(root, text="Check for Responses", command=lambda: update_responses(response_list)).pack(pady=10)

    # Close button
    tk.Button(root, text="Close", command=root.quit).pack(pady=20)

    # Load previous responses from the database
    load_responses(response_list)

    root.mainloop()

# Function to load responses from the database
def load_responses(response_list):
    for widget in response_list.winfo_children():
        widget.destroy()

    # Fetch all responses from the database
    c.execute("SELECT id, sender, subject, seen FROM responses")
    rows = c.fetchall()

    for row in rows:
        response_id, sender, subject, seen = row
        var = tk.IntVar(value=seen)

        # Create a frame for each response with a checkbox
        response_item = tk.Frame(response_list, borderwidth=1, relief="solid", padx=5, pady=5)
        response_item.pack(anchor="w", fill="x", padx=10, pady=5)

        # Checkbox to mark the response as seen
        checkbox = tk.Checkbutton(response_item, text=f"From: {sender}\nSubject: {subject}", variable=var, wraplength=400,
                                  command=lambda id=response_id, var=var: mark_as_seen(id, var))
        checkbox.pack(anchor="w")

        # Set the checkbox state based on 'seen' value
        if seen:
            checkbox.select()

# Function to mark a response as seen in the database
def mark_as_seen(response_id, var):
    seen_status = var.get()
    c.execute("UPDATE responses SET seen = ? WHERE id = ?", (seen_status, response_id))
    conn.commit()

# Function to check for email responses
def check_email_responses():
    # Load credentials from .env file
    username = os.getenv('SENDER_EMAIL')
    password = os.getenv('APP_PASSWORD')

    if not username or not password:
        raise ValueError("Email or app password is missing in .env file.")

    # Connect to Gmail's IMAP server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)

    # Select inbox and search for unread messages
    mail.select("inbox")
    status, messages = mail.search(None, '(UNSEEN)')

    email_ids = messages[0].split()
    responses = []

    for e_id in email_ids:
        status, msg_data = mail.fetch(e_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                from_ = msg.get("From")

                # Store response in database if it doesn't already exist
                c.execute("SELECT * FROM responses WHERE sender = ? AND subject = ?", (from_, subject))
                if c.fetchone() is None:
                    c.execute("INSERT INTO responses (sender, subject, seen) VALUES (?, ?, 0)", (from_, subject))
                    conn.commit()

                responses.append(f"New response from {from_} with subject: {subject}")

    # Logout from the server
    mail.logout()
    return responses

# Function to update responses in the list
def update_responses(response_list):
    new_responses = check_email_responses()
    load_responses(response_list)

if __name__ == "__main__":
    create_dashboard()
