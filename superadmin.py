import datetime
import jwt
import sqlite3
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#MainDB = '/Users/firdovsirzaev/Desktop/hesabat_back_test/ZeferMlmDb.db'
MainDB = 'ZeferMlmDb.db'
SECRET_KEY = 'Tm5x2,+QXD9Mo%<3V[]GZlWO`+yPEf1j'

def get_db_connection():
    conn = sqlite3.connect(MainDB)
    conn.row_factory = sqlite3.Row
    return conn

def generate_jwt(username: str):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=10)
    payload = {"username": username, "exp": expiration_time}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Token is missing!")
    try:
        token = authorization.split(" ")[1]  
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['username']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=403, detail="Token is invalid!")

@app.post("/login")
async def login(data: dict):
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT password, vezife_kodu FROM LoginHesabat WHERE username = ?"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['password'] == password:
        token = generate_jwt(username)
        return {"message": "Login successful", "token": token, "role": user['vezife_kodu'], "username": username}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")


@app.get("/add_new_fac")
