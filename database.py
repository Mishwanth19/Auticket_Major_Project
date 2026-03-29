"""
MongoDB Database Layer for Auticket

Collections:
- users           → login/signup, session tokens
- sessions        → active user sessions
- requests        → access request history
- policies        → policy documents (replaces policies.py hardcoded data)
- access_matrix   → role-based access rules

Run `python database.py` to seed initial data into MongoDB.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import hashlib
import secrets
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION
# ============================================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB_NAME", "auticket")

_client: Optional[MongoClient] = None

def get_db():
    """Return the MongoDB database instance (singleton)."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        logger.info(f"Connected to MongoDB: {MONGO_URI}/{DB_NAME}")
    return _client[DB_NAME]


# ============================================================================
# INDEX SETUP  (call once at startup)
# ============================================================================

def create_indexes():
    db = get_db()

    # users
    db.users.create_index("email", unique=True)

    # sessions
    db.sessions.create_index("token", unique=True)
    db.sessions.create_index("expires_at", expireAfterSeconds=0)   # TTL index

    # requests
    db.requests.create_index("request_id", unique=True)
    db.requests.create_index("employee_email")
    db.requests.create_index([("created_at", DESCENDING)])

    # policies
    db.policies.create_index("policy_id", unique=True)
    db.policies.create_index("category")

    # access_matrix
    db.access_matrix.create_index("role", unique=True)

    logger.info("MongoDB indexes created.")


# ============================================================================
# USER HELPERS
# ============================================================================

def _hash_password(password: str) -> str:
    """SHA-256 hash with salt.  Use bcrypt in production."""
    salt = "auticket_salt_v1"          # replace with per-user salt in prod
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


class UserStore:
    """CRUD operations for the `users` collection."""

    def __init__(self):
        self.col = get_db().users

    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        role: str = "Software Engineer",
        department: str = "Engineering",
        security_clearance: str = "standard",
        location: str = "Unknown",
        manager_email: Optional[str] = None,
    ) -> Dict:
        """Register a new user.  Raises ValueError on duplicate email."""
        doc = {
            "email": email.lower().strip(),
            "password_hash": _hash_password(password),
            "name": name,
            "role": role,
            "department": department,
            "security_clearance": security_clearance,
            "location": location,
            "manager_email": manager_email,
            "created_at": datetime.utcnow(),
            "is_active": True,
        }
        try:
            result = self.col.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            logger.info(f"User created: {email}")
            return doc
        except DuplicateKeyError:
            raise ValueError(f"Email already registered: {email}")

    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Return user doc if credentials match, else None."""
        user = self.col.find_one({"email": email.lower().strip()})
        if user and user["password_hash"] == _hash_password(password):
            user["_id"] = str(user["_id"])
            return user
        return None

    def get_by_email(self, email: str) -> Optional[Dict]:
        user = self.col.find_one({"email": email.lower().strip()})
        if user:
            user["_id"] = str(user["_id"])
        return user

    def update_profile(self, email: str, updates: Dict) -> bool:
        """Update allowed profile fields."""
        allowed_fields = {"name", "role", "department", "location", "manager_email", "security_clearance"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not safe_updates:
            return False
        result = self.col.update_one({"email": email}, {"$set": safe_updates})
        return result.modified_count > 0


# ============================================================================
# SESSION HELPERS
# ============================================================================

SESSION_TTL_HOURS = 24

class SessionStore:
    """Manages login sessions in the `sessions` collection."""

    def __init__(self):
        self.col = get_db().sessions

    def create_session(self, email: str) -> str:
        """Create a new session token for a user."""
        token = secrets.token_urlsafe(32)
        self.col.insert_one({
            "token": token,
            "email": email.lower().strip(),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
        })
        return token

    def get_session(self, token: str) -> Optional[Dict]:
        """Return session if valid and not expired."""
        session = self.col.find_one({
            "token": token,
            "expires_at": {"$gt": datetime.utcnow()},
        })
        if session:
            session["_id"] = str(session["_id"])
        return session

    def delete_session(self, token: str):
        self.col.delete_one({"token": token})

    def delete_all_user_sessions(self, email: str):
        self.col.delete_many({"email": email.lower().strip()})


# ============================================================================
# REQUEST STORE
# ============================================================================

class RequestStore:
    """Persists approval requests and their decisions."""

    def __init__(self):
        self.col = get_db().requests

    def save_request(
        self,
        request_id: str,
        employee_email: str,
        employee_context: Dict,
        raw_tools: List[Dict],
        decisions: List[Dict],
        overall_status: str,
    ) -> str:
        doc = {
            "request_id": request_id,
            "employee_email": employee_email.lower().strip(),
            "employee_context": employee_context,
            "tools_requested": raw_tools,
            "decisions": decisions,
            "overall_status": overall_status,
            "status": "evaluated",
            "created_at": datetime.utcnow(),
        }
        self.col.insert_one(doc)
        return request_id

    def get_request(self, request_id: str) -> Optional[Dict]:
        doc = self.col.find_one({"request_id": request_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def update_status(self, request_id: str, status: str, decision_updates: Optional[List[Dict]] = None):
        update: Dict = {"$set": {"status": status}}
        if decision_updates is not None:
            update["$set"]["decisions"] = decision_updates
        self.col.update_one({"request_id": request_id}, update)

    def get_user_requests(self, email: str, limit: int = 20) -> List[Dict]:
        docs = list(
            self.col.find({"employee_email": email.lower().strip()})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs


# ============================================================================
# POLICY STORE  (replaces hardcoded policies.py for the DB-backed version)
# ============================================================================

class PolicyStore:
    """Read/write policies in MongoDB."""

    def __init__(self):
        self.col = get_db().policies

    def get_all(self) -> List[Dict]:
        return list(self.col.find({}, {"_id": 0}))

    def get_by_id(self, policy_id: str) -> Optional[Dict]:
        return self.col.find_one({"policy_id": policy_id}, {"_id": 0})

    def get_by_category(self, category: str) -> List[Dict]:
        return list(self.col.find({"category": category}, {"_id": 0}))

    def upsert(self, policy: Dict):
        self.col.update_one(
            {"policy_id": policy["policy_id"]},
            {"$set": policy},
            upsert=True,
        )


# ============================================================================
# ACCESS MATRIX STORE
# ============================================================================

class AccessMatrixStore:
    """Read/write role-based access rules in MongoDB."""

    def __init__(self):
        self.col = get_db().access_matrix

    def get_role(self, role: str) -> Optional[Dict]:
        return self.col.find_one({"role": role}, {"_id": 0})

    def get_all(self) -> List[Dict]:
        return list(self.col.find({}, {"_id": 0}))

    def upsert(self, role_doc: Dict):
        self.col.update_one(
            {"role": role_doc["role"]},
            {"$set": role_doc},
            upsert=True,
        )


# ============================================================================
# SEED DATA  — run `python database.py` once to populate MongoDB
# ============================================================================

def seed_database():
    """Migrate all hardcoded data from policies.py into MongoDB."""
    from policies import POLICY_DOCUMENTS, ACCESS_MATRIX

    db_policies = PolicyStore()
    db_matrix   = AccessMatrixStore()
    user_store  = UserStore()

    # --- Policies ---
    for policy_id, data in POLICY_DOCUMENTS.items():
        db_policies.upsert({"policy_id": policy_id, **data})
    print(f"✓ Seeded {len(POLICY_DOCUMENTS)} policies")

    # --- Access matrix ---
    for role, rules in ACCESS_MATRIX.items():
        db_matrix.upsert({"role": role, **rules})
    print(f"✓ Seeded {len(ACCESS_MATRIX)} roles in access matrix")

    # --- Demo users ---
    demo_users = [
        {
            "email": "john.doe@company.com",
            "password": "password123",
            "name": "John Doe",
            "role": "Software Engineer",
            "department": "Engineering",
            "security_clearance": "standard",
            "location": "US-West",
            "manager_email": "jane.manager@company.com",
        },
        {
            "email": "alice.admin@company.com",
            "password": "password123",
            "name": "Alice Admin",
            "role": "DevOps Engineer",
            "department": "Infrastructure",
            "security_clearance": "elevated",
            "location": "US-East",
            "manager_email": "bob.manager@company.com",
        },
        {
            "email": "intern.user@company.com",
            "password": "password123",
            "name": "Intern User",
            "role": "Intern",
            "department": "Engineering",
            "security_clearance": "restricted",
            "location": "US-West",
            "manager_email": "jane.manager@company.com",
        },
    ]

    for u in demo_users:
        try:
            user_store.create_user(**u)
            print(f"✓ Demo user created: {u['email']}")
        except ValueError:
            print(f"  (skipped, already exists): {u['email']}")

    print("\n✅ Database seeded successfully.")
    print("   Demo password for all users: password123")


if __name__ == "__main__":
    create_indexes()
    seed_database()
