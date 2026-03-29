# """
# auth.py — Streamlit-side authentication helpers

# Wraps UserStore + SessionStore so streamlit_chat.py
# just calls simple functions without touching MongoDB directly.
# """

# from typing import Optional, Dict, Tuple
# from database import UserStore, SessionStore

# user_store    = UserStore()
# session_store = SessionStore()


# def signup(
#     email: str,
#     password: str,
#     name: str,
#     role: str = "Software Engineer",
#     department: str = "Engineering",
# ) -> Tuple[bool, str]:
#     """
#     Register a new user.
#     Returns (success: bool, message: str).
#     """
#     if not email or "@" not in email:
#         return False, "Please enter a valid email address."
#     if len(password) < 6:
#         return False, "Password must be at least 6 characters."
#     if not name.strip():
#         return False, "Please enter your full name."

#     try:
#         user_store.create_user(
#             email=email.strip().lower(),
#             password=password,
#             name=name.strip(),
#             role=role,
#             department=department,
#         )
#         return True, "Account created! You can now log in."
#     except ValueError as e:
#         return False, str(e)


# def login(email: str, password: str) -> Tuple[Optional[str], str]:
#     """
#     Authenticate user and create a session.
#     Returns (token | None, message).
#     """
#     user = user_store.authenticate(email.strip().lower(), password)
#     if not user:
#         return None, "Invalid email or password."

#     token = session_store.create_session(email.strip().lower())
#     return token, f"Welcome back, {user['name']}!"


# def logout(token: str):
#     """Destroy the session."""
#     session_store.delete_session(token)


# def get_current_user(token: Optional[str]) -> Optional[Dict]:
#     """
#     Resolve a session token to a user dict.
#     Returns None if the token is missing or expired.
#     """
#     if not token:
#         return None
#     session = session_store.get_session(token)
#     if not session:
#         return None
#     return user_store.get_by_email(session["email"])


"""
auth.py — Streamlit-side authentication helpers

Calls the FastAPI backend (/auth/signup, /auth/login, etc.)
instead of hitting MongoDB directly.  This keeps all DB logic
on the server side.
"""

import requests
from typing import Optional, Dict, Tuple
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def signup(
    email: str,
    password: str,
    name: str,
    role: str = "Software Engineer",
    department: str = "Engineering",
) -> Tuple[bool, str]:
    """Register a new user via POST /auth/signup."""
    if not email or "@" not in email:
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not name.strip():
        return False, "Please enter your full name."

    try:
        r = requests.post(f"{API_BASE}/auth/signup", json={
            "email": email.strip().lower(),
            "password": password,
            "name": name.strip(),
            "role": role,
            "department": department,
        }, timeout=10)

        if r.status_code == 201:
            return True, r.json().get("message", "Account created!")
        return False, r.json().get("detail", "Signup failed.")
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach the API server. Is it running?"


def login(email: str, password: str) -> Tuple[Optional[str], str]:
    """
    Authenticate via POST /auth/login.
    Returns (token | None, message).
    """
    try:
        r = requests.post(f"{API_BASE}/auth/login", json={
            "email": email.strip().lower(),
            "password": password,
        }, timeout=10)

        if r.status_code == 200:
            data = r.json()
            return data["token"], data["message"]
        return None, r.json().get("detail", "Login failed.")
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the API server. Is it running?"


def logout(token: str):
    """Invalidate session via POST /auth/logout."""
    try:
        requests.post(
            f"{API_BASE}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    except Exception:
        pass  # Best-effort; session expires via TTL anyway


def get_current_user(token: Optional[str]) -> Optional[Dict]:
    """
    Resolve a session token to a user profile via GET /users/me.
    Returns None if the token is missing or expired.
    """
    if not token:
        return None
    try:
        r = requests.get(
            f"{API_BASE}/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def get_my_requests(token: str) -> list:
    """Fetch the logged-in user's last 20 requests via GET /users/me/requests."""
    try:
        r = requests.get(
            f"{API_BASE}/users/me/requests",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []