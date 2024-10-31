# logger.py
import logging
import os

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup a logger with a specific name and log file."""
    # Ensure the log directory exists
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler for logging to file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    # Console handler for logging to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Log format with filename and line number
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Setup loggers for different components
app_logger = setup_logger("AppLogger", "logs/app.log")
local_server_logger = setup_logger("LocalServerLogger", "logs/local_server.log")
openai_logger = setup_logger("OpenAILogger", "logs/openai.log")
