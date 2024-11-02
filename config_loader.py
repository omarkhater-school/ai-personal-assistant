# config_loader.py

import yaml
import json

def load_config(file_path="config.yml"):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config

def get_endpoint(service_name):
    config = load_config()
    return config.get("endpoints", {}).get(service_name)

def get_email_config():
    config = load_config()
    return config.get("email", {})

def load_contacts(file_path="contacts.json"):
    with open(file_path, "r") as file:
        contacts = json.load(file)
    return contacts