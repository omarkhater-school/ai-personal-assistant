# config_loader.py

import yaml

def load_config(file_path="config.yml"):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config

def get_endpoint(service_name):
    config = load_config()
    return config.get("endpoints", {}).get(service_name)
