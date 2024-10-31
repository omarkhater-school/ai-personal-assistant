from flask import render_template
from . import meeting_assistant_bp

@meeting_assistant_bp.route("/", methods=["GET"])
def meeting_assistant_home():
    return render_template("meeting_assistant.html")
