import os
import json
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from flask_mail import Mail, Message as MailMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)
CORS(app)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Helper for env bools
def _as_bool(v, default=True):
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "t", "on", "yes", "y")

# Mail setup
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = _as_bool(os.environ.get('MAIL_USE_TLS', 'true'), True)
app.config['MAIL_USE_SSL'] = _as_bool(os.environ.get('MAIL_USE_SSL', 'false'), False)
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

mail = Mail(app)

# Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    project_url = db.Column(db.String(255))
    github_url = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'project_url': self.project_url,
            'github_url': self.github_url,
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Routes
@app.route('/')
def index():
    return "<h1>API Server is Running</h1><p>Try accessing the <a href='/api/projects'>/api/projects</a> endpoint.</p>"

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json() or {}
    if not all(k in data and str(data[k]).strip() for k in ('name', 'email', 'message')):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    name = data.get('name').strip()
    email = data.get('email').strip()
    message_text = data.get('message').strip()

    # Save to DB
    try:
        new_message = Message(name=name, email=email, message=message_text)
        db.session.add(new_message)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error on contact form submission: {e}")
        return jsonify({"success": False, "message": "Could not save message due to a database error."}), 500

    app.logger.info(f"New message from {name} ({email}) stored in database.")

    # Email
    subject = f"New Contact Form Message from {name}"
    body = f"""You have received a new message from your portfolio contact form.

Name: {name}
Email: {email}

Message:
{message_text}
"""

    try:
        msg = MailMessage(
            subject=subject,
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['iamtjayearl@gmail.com'],
            reply_to=email
        )
        msg.body = body
        mail.send(msg)
        app.logger.info("Email sent successfully via Gmail.")
        return jsonify({"success": True, "message": "Message received and emailed!"}), 200

    except Exception as err:
        app.logger.error(f"Failed to send email: {err}")
        return jsonify({
            "success": True,
            "message": "Message saved, but failed to send email notification."
            "error": str(err)
        }), 200

# Seeder
@app.cli.command('seed-projects')
def seed_projects():
    """Seeds the database with projects from data/projects.json."""
    data_file = Path(__file__).parent / "data" / "projects.json"
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return
    with open(data_file) as f:
        projects_data = json.load(f)
    for p_data in projects_data:
        if not Project.query.filter_by(title=p_data['title']).first():
            project = Project(**p_data)
            db.session.add(project)
    db.session.commit()
    print("Project database has been seeded.")

if __name__ == '__main__':
    print("Starting Flask server for local development...")
    app.run(host='0.0.0.0', port=8080, debug=True)
