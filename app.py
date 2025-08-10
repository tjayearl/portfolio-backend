import os
from flask import Flask, jsonify, request
import json
from pathlib import Path
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)

# Database Configuration
# It will use the DATABASE_URL from the environment if it exists,
# otherwise it will fall back to a local sqlite database.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Database Models ---
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

# --- API Routes ---
@app.route('/')
def index():
    return "<h1>API Server is Running</h1><p>Try accessing the <a href='/api/projects'>/api/projects</a> endpoint.</p>"

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'email', 'message')):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    new_message = Message(name=name, email=email, message=message)
    db.session.add(new_message)
    db.session.commit()

    print(f"New message from {name} ({email}) stored in database.")
    return jsonify({"success": True, "message": "Message received and stored!"})

# --- CLI Commands ---
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
    print("✅ Project database has been seeded.")

if __name__ == '__main__':
    print("✅ Starting Flask server for local development...")
    app.run(host='0.0.0.0', port=8080, debug=True)
