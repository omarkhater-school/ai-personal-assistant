import os
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config_loader import get_email_config
from logger import setup_logger

class EmailModule:
    def __init__(self, assistant_query_llm):
        self.query_llm = assistant_query_llm  # Reference to AIAssistant's query method
        self.logger = setup_logger("EmailModuleLogger", "logs/email_module.log")
        self.email_config = get_email_config()
        self.contacts = self.load_contacts()
        self.contains_sensitive_data = False

    def load_contacts(self):
        contacts_file = 'contacts.json'
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
                self.logger.info("Contacts loaded successfully.")
                return contacts
        else:
            self.logger.warning("Contacts file not found.")
            return {}

    def send_email(self, recipient_name, subject, body):
        to_addr = self.find_email(recipient_name)
        if not to_addr:
            return "Recipient email not found."

        smtp_server = self.email_config.get('smtp_server')
        smtp_port = self.email_config.get('smtp_port')
        username = self.email_config.get('username')
        password = self.email_config.get('password')
        from_addr = self.email_config.get('default_from_address')
        
        # Prepare the message
        message = MIMEMultipart()
        message["From"] = from_addr
        message["To"] = to_addr
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(from_addr, to_addr, message.as_string())
            self.logger.info("Email sent successfully.")
            return "Email sent successfully."
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {e}"
            self.logger.error(error_msg)
            return error_msg

    def find_email(self, name):
        if re.match(r"[^@]+@[^@]+\.[^@]+", name):
            return name  # Return if name is already an email
        return self.contacts.get(name, None)
