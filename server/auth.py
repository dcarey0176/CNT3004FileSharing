import hashlib
import json
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def authenticate(username: str, password: str) -> bool:
    users = load_users()
    hashed_pw = hash_password(password)
    print(f" Username entered: {username}")
    print(f" Password entered (hashed): {hashed_pw}")
    print(f" Users loaded: {users}")
    return username in users and users[username] == hashed_pw
