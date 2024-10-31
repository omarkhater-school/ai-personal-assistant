from flask import render_template
from . import email_assistant_bp

@email_assistant_bp.route("/", methods=["GET"])
def email_assistant_home():
    return render_template("email_assistant.html")
