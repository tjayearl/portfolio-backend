from flask import Flask, jsonify, request
import json
from pathlib import Path
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "<h1>API Server is Running</h1><p>Try accessing the <a href='/api/projects'>/api/projects</a> endpoint.</p>"

@app.route('/api/projects', methods=['GET'])
def get_projects():
    data_file = Path(__file__).parent / "data" / "projects.json"
    with open(data_file) as f:
        projects = json.load(f)
    return jsonify(projects)

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    print(f"New message from {name} ({email}): {message}")
    return jsonify({"success": True, "message": "Message received!"})

if __name__ == '__main__':
    print("✅ Starting Flask server...")
    app.run(host='0.0.0.0', port=8080, debug=True)
