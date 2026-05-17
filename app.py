from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB Connection (Render ke Environment Variables se uthayega)
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['mdmkiller_pro']
users_collection = db['users']

@app.route('/')
def home():
    return "MDM Killer Pro Multi-Tier API is Live!"

# --- LOGIN (Common for All) ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = users_collection.find_one({"email": email, "password": password})
    
    if user:
        return jsonify({
            "status": "success",
            "role": user.get('role', 'user'),
            "credits": user.get('credits', 0),
            "activated": user.get('activated', False)
        }), 200
    return jsonify({"status": "error", "message": "Invalid Credentials"}), 401

# --- REGISTER (Only for Users) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    
    if users_collection.find_one({"email": email}):
        return jsonify({"message": "User Already Exists"}), 400

    new_user = {
        "email": email,
        "password": data.get('password'),
        "role": "user",
        "credits": 0,
        "activated": False
    }
    users_collection.insert_one(new_user)
    return jsonify({"message": "Registration Successful"}), 201

# --- ACTIVATE USER (Deducts 100 Credits) ---
@app.route('/activate-user', methods=['POST'])
def activate():
    data = request.get_json()
    reseller_email = data.get('reseller_email')
    target_email = data.get('target_email')

    reseller = users_collection.find_one({"email": reseller_email})
    if not reseller or reseller.get('credits', 0) < 100:
        return jsonify({"message": "Insufficient Credits (100 required)"}), 400

    # User activate karo aur reseller ke credits kato
    users_collection.update_one({"email": reseller_email}, {"$inc": {"credits": -100}})
    users_collection.update_one({"email": target_email}, {"$set": {"activated": True}})
    return jsonify({"message": "Account Activated Successfully!"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

