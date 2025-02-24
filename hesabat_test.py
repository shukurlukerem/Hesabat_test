
import datetime
import os 
import jwt
import string
from flask_cors import CORS
from flask import Flask, request, jsonify
import sqlite3
import requests
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

MainDB = '/Users/firdovsirzaev/Desktop/hesabat_back_test/ZeferMlmDb.db'
SECRET_KEY = 'YOUR_SECRET_KEY'

def init_db():
    conn = sqlite3.connect(MainDB)
    cursor = conn.cursor()
    
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Bolme_Novu (
            bolme_novunun_kodu INTEGER,
            bolme_novunun_adi TEXT
        )
    ''')

    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS Bolme_Novu_Fakulte (
            bolme_novunun_kodu INTEGER,
            fakulte_kodu INTEGER,
            ad TEXT,
            qisa_ad TEXT
        )
    ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Bolme_Novu_Kafedra (
            bolme_novunun_kodu INTEGER,
            fakulte_kodu INTEGER,
            kafedra_kodu INTEGER,
            kafedra_adi TEXT
        )
    ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS LoginHesabat (
            username TEXT,
            password TEXT
        )
    ''')
   

    cursor.execute (''' 
        CREATE TABLE IF NOT EXISTS user_details (
          istifadeci_adi   TEXT,
          ad  TEXT,
          soyad  TEXT,
          ati_adi  TEXT,
          vezife_kodu  INTEGER,
          vezife_adi  TEXT,
          kafetda_kodu  INTEGER,
          kafedra_adi  TEXT,
          fakulte_kodu  INTEGER,
          fakulte_adi  TEXT
            )
    ''')
    conn.commit()  
    conn.close()
init_db()

def get_db_connection():
    conn = sqlite3.connect(MainDB)  
    conn.row_factory = sqlite3.Row       
    return conn

def generate_jwt(username):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=10)
    payload = {
        'username': username,
        'exp': expiration_time
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            token = token.split(" ")[1]  # Extract token part from "Bearer <token>"
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = payload['username']
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return jsonify({'message': 'Token is invalid!'}), 403

        # Add user info to the request context
        request.current_user = current_user
        return f(*args, **kwargs)

    return decorated_function

# @app.route('/login', methods = ['GET'])
# def login():
#     data = request.json
#     if not data:
#         return jsonify({'error': 'Invalid request, missing JSON data'}), 400
    
#     username = data.get('username')
#     password = data.get('password')

#     if not username or not password:
#         return jsonify({'error': 'Username and password are required'}), 400

#     conn = get_db_connection()
#     try:
#         query = "SELECT password FROM users WHERE username = ?"
#         cursor = conn.cursor()
#         cursor.execute(query, (username,))
#         user = cursor.fetchone()

#         if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
#             return jsonify({'message': 'Login successful'}), 200
#         else:
#             return jsonify({'error': 'Invalid username or password'}), 401
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         conn.close()
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request, missing JSON data'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch password and vezife_kodu (role)
        query = "SELECT password, vezife_kodu FROM LoginHesabat WHERE username = ?"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        print(username)
        if user and user['password'] == password and username:
            token = generate_jwt(username)
            role = user['vezife_kodu']  # Get the role from the database
            return jsonify({'message': 'Login successful', "token": token, "role": role, "username": username}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    except sqlite3.Error as db_error:
        return jsonify({'error': f'Database error: {str(db_error)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()
            conn.close()
    
@app.route('/fetch_user_details/<username>', methods = ['GET'])
@token_required
def fetch_user_details(username):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM user_details WHERE istifadeci_adi = ?"
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        rows = cursor.fetchall()
        
        results = [dict(row) for row in rows]  
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/kafedra_as_fac/<fakulte_kodu>', methods=['GET'])
def get_fakulte(fakulte_kodu):
    conn = get_db_connection()
    try:
        sql = """SELECT kafedra_adi FROM Bolme_Novu_Kafedra WHERE fakulte_kodu =?"""  
        cursor = conn.cursor()
        cursor.execute(sql, fakulte_kodu)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]  
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)