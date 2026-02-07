#no use
from flask import Flask, request, render_template, jsonify, session
from flask_cors import CORS
import pickle
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.debug = True
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5502"}})

app.secret_key = 'your_secret_key'  # Change this to a secure random key in production

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# Load pickle files
try:
    with open('classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('fertilizer.pkl', 'rb') as f:
        ferti = pickle.load(f)
    print("Models loaded successfully")
except Exception as e:
    print(f"Error loading pickle files: {e}")
    model, ferti = None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user[3], password):
        session['user_id'] = user[0]
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"})

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    hashed_password = generate_password_hash(password)
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hashed_password))
        conn.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username or email already exists"})
    finally:
        conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"success": True})

@app.route('/predict', methods=['POST'])
def predict_fertilizer():
    try:
        data = request.get_json()
        print(f"Incoming data: {data}")

        required_fields = ['temperature', 'humidity', 'soilType', 'cropType', 'nitrogen', 'potassium', 'phosphorous']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}")
            return jsonify(success=False, message=f"Missing fields: {', '.join(missing_fields)}"), 400

        try:
            temp = float(data['temperature'])
            humi = float(data['humidity'])
            soil = data['soilType']
            crop = data['cropType']
            nitro = float(data['nitrogen'])
            pota = float(data['potassium'])
            phosp = float(data['phosphorous'])
        except ValueError as e:
            print(f"Value conversion error: {e}")
            return jsonify(success=False, message="Invalid input types"), 400

        soil_types = ['black', 'clayey', 'loamy', 'red', 'sandy']
        crop_types = ['barley', 'cotton', 'groundNuts', 'maize', 'millets', 'oilSeeds', 'paddy', 'pulses', 'sugarcane', 'tobacco', 'wheat']

        if soil not in soil_types:
            print(f"Invalid soil type: {soil}")
            return jsonify(success=False, message=f"Invalid soil type: {soil}"), 400
        if crop not in crop_types:
            print(f"Invalid crop type: {crop}")
            return jsonify(success=False, message=f"Invalid crop type: {crop}"), 400

        soil_index = soil_types.index(soil)
        crop_index = crop_types.index(crop)

        input_data = [int(temp), int(humi), soil_index, crop_index, int(nitro), int(pota), int(phosp)]
        print(f"Prepared input for prediction: {input_data}")

        try:
            predicted_fertilizer = ferti.classes_[model.predict([input_data])[0]]
            print(f"Predicted fertilizer: {predicted_fertilizer}")
            return jsonify(success=True, fertilizer=str(predicted_fertilizer))
        except Exception as model_error:
            print(f"Model prediction error: {model_error}")
            return jsonify(success=False, message=f"Model prediction error: {model_error}"), 500

    except Exception as e:
        print(f"Unexpected server error: {e}")
        return jsonify(success=False, message=f"Unexpected server error: {e}"), 500

if __name__ == '__main__':
    app.run(debug=True)
