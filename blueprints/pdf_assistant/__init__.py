from flask import Blueprint

# Define the blueprint
pdf_assistant_bp = Blueprint('pdf_assistant', __name__, template_folder='templates')

# Import routes
from . import routes
