from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB Connection (Render Environment Variables se MONGO_URI uthayega)
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['mdmkiller_pro']
users_collection = db['users']

# --- HOMEPAGE ROUTE (index.html dikhane ke liye) ---
@app.route('/')
def home():
    # Ye line aapke domain par index.html file dikhayegi
    return send_from_directory('.', 'index.html')

# --- LOGIN (Admin, Distributor, Reseller, User sab ke liye) ---
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

# --- REGISTER (Naye users ke liye) ---
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
    
    # Check if Reseller has enough credits
    if not reseller or reseller.get('credits', 0) < 100:
        return jsonify({"message": "Insufficient Credits (100 required)"}), 400

    # User activate karo aur reseller ke credits kato
    users_collection.update_one({"email": reseller_email}, {"$inc": {"credits": -100}})
    users_collection.update_one({"email": target_email}, {"$set": {"activated": True}})
    
    return jsonify({"message": "Account Activated Successfully!"}), 200

# --- ADD CREDITS (Only Admin can call this) ---
@app.route('/add-credits', methods=['POST'])
def add_credits():
    data = request.get_json()
    # Yahan security ke liye admin check bhi laga sakte hain
    target_email = data.get('target_email')
    amount = int(data.get('amount'))

    users_collection.update_one({"email": target_email}, {"$inc": {"credits": amount}})
    return jsonify({"message": f"{amount} Credits added to {target_email}"}), 200

if __name__ == "__main__":
    # Render hamesha port 10000 ya environment port use karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
