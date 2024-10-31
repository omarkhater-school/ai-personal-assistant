# app.py
from flask import Flask, render_template
from flask_cors import CORS

# Import blueprints
from blueprints.pdf_assistant.routes import pdf_assistant_bp
from blueprints.email_assistant.routes import email_assistant_bp
from blueprints.meeting_assistant.routes import meeting_assistant_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(pdf_assistant_bp, url_prefix='/pdf_assistant')
app.register_blueprint(email_assistant_bp, url_prefix='/email_assistant')
app.register_blueprint(meeting_assistant_bp, url_prefix='/meeting_assistant')

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
