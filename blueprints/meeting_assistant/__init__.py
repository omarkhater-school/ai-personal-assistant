from flask import Blueprint

# Define the blueprint
meeting_assistant_bp = Blueprint('meeting_assistant', __name__, template_folder='templates')

# Import routes
from . import routes
