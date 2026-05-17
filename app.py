from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB Connection
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['mdmkiller_pro']
users_collection = db['users']

@app.route('/')
def home():
    # Ye line index.html file ko browser par show karegi
    return send_from_directory('.', 'index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_collection.find_one({"email": data.get('email'), "password": data.get('password')})
    if user:
        return jsonify({
            "status": "success",
            "role": user.get('role', 'user'),
            "credits": user.get('credits', 0),
            "activated": user.get('activated', False)
        }), 200
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if users_collection.find_one({"email": data.get('email')}):
        return jsonify({"message": "Exists"}), 400
    new_user = {
        "email": data.get('email'),
        "password": data.get('password'),
        "role": "user",
        "credits": 0,
        "activated": False
    }
    users_collection.insert_one(new_user)
    return jsonify({"message": "Success"}), 201

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
