import hashlib
import json

USERS_FILE = "server/users.json"

def hash_password(password: str) -> str:
    """Return SHA-1 hash of password"""
    return hashlib.sha1(password.encode()).hexdigest()

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def authenticate(username: str, password: str) -> bool:
    users = load_users()
    hashed_pw = hash_password(password)
    return username in users and users[username] == hashed_pw
