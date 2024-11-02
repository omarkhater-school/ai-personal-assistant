# email_module.py

import os
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config_loader import get_email_config
from logger import setup_logger
from prompts import email_drafting_prompt

class EmailModule:
    def __init__(self, assistant_query_llm):
        self.query_llm = assistant_query_llm  # Reference to AIAssistant's query method
        self.logger = setup_logger("EmailModuleLogger", "logs/email_module.log")
        self.email_config = get_email_config()
        self.contacts = self.load_contacts()
        self.contains_sensitive_data = False

    def load_contacts(self):
        """
        Loads contacts from contacts.json file.
        """
        contacts_file = 'contacts.json'
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
                self.logger.info("Contacts loaded successfully.")
                return contacts
        else:
            self.logger.warning("Contacts file not found. Creating a default contacts list.")
            contacts = {}
            return contacts

    def find_email(self, name):
        """
        Finds the email address of a contact by name or directly uses it if it's an email format.
        """
        # Check if 'name' is already in email format
        if re.match(r"[^@]+@[^@]+\.[^@]+", name):
            self.logger.info(f"Using direct email address: {name}")
            return name

        # Otherwise, look up in contacts
        email = self.contacts.get(name)
        if email:
            self.logger.info(f"Email found for {name}: {email}")
        else:
            self.logger.warning(f"No email found for {name}")
        return email

    def scan_for_sensitive_data(self, text):
        """
        Scans the text for patterns that might indicate sensitive data.
        """
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
        password_pattern = r'password\s*[:=]\s*\S+'

        patterns = {"SSN": ssn_pattern, "Credit Card Number": cc_pattern, "Password": password_pattern}
        for name, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                self.logger.info(f"Sensitive data detected: {name}")
                return True
        return False

    def draft_email(self, to_addr, subject, user_message):
        """
        Drafts an email using the assistant's LLM, capturing the tone from the user's message.
        """
        if not to_addr:
            return "Invalid email address."

        # Use the assistant to draft the email body
        prompt = email_drafting_prompt(to_addr, subject, user_message)
        email_body = self.query_llm(prompt, is_private=True)

        # Scan the email body for sensitive data
        self.contains_sensitive_data = self.scan_for_sensitive_data(email_body)

        # Log the draft without sending or asking for confirmation
        email_preview = f"""
To: {to_addr}
Subject: {subject}
Body:
{email_body}
"""
        self.logger.info(f"Drafted email for confirmation: {email_preview}")
        return email_body

    def send_email(self, to_addr, subject, body):
        """
        Sends an email using SMTP server configuration from config.yml.
        """
        smtp_server = self.email_config.get('smtp_server')
        smtp_port = self.email_config.get('smtp_port')
        username = self.email_config.get('username')
        password = self.email_config.get('password')
        from_addr = self.email_config.get('default_from_address')
        cc_addr = self.email_config.get('cc_address')

        self.logger.info(f"Sending an email from: {username} to {to_addr}")
        self.logger.info("Using password: [SECURE: Password not displayed for security purposes]")
        self.logger.info(f"The subject is: {subject}")
        self.logger.info(f"The body is: {body}")
        message = MIMEMultipart()
        message["From"] = from_addr
        message["To"] = to_addr
        message["Subject"] = subject
        if cc_addr:
            message["Cc"] = cc_addr  # Add CC field to the message
        message.attach(MIMEText(body, "plain"))

        recipients = [to_addr] + ([cc_addr] if cc_addr else [])

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(from_addr, recipients, message.as_string())
            self.logger.info("Email sent successfully.")
            return "Email sent successfully."
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {e}"
            self.logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            self.logger.error(error_msg)
            return error_msg

    def get_available_contacts(self):
        """
        Returns a list of available contacts.
        """
        return list(self.contacts.keys()) if self.contacts else ["No contacts available."]
