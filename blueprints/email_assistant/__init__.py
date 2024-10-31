from flask import Blueprint

# Define the blueprint
email_assistant_bp = Blueprint('email_assistant', __name__, template_folder='templates')

# Import routes
from . import routes
