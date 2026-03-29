# """
# FastAPI Orchestrator — MongoDB-backed version

# Changes from original:
# - Imports RequestStore from database.py
# - Saves every request + decisions to MongoDB (replaces in-memory dict)
# - Reads request status from MongoDB
# - Startup event creates indexes
# """

# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from pydantic import BaseModel, Field
# from typing import List, Dict, Optional
# from enum import Enum
# import logging
# from datetime import datetime

# from requester_agent import RequesterAgent
# from granter_agent import GranterAgent
# from database import RequestStore, create_indexes

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="Agentic IT Service Approval System",
#     description="Token-efficient, goal-driven approval automation (MongoDB)",
#     version="2.0.0",
# )

# # ============================================================================
# # MODELS
# # ============================================================================

# class ToolRequest(BaseModel):
#     tool_name: str
#     version: Optional[str] = None
#     justification: str

# class BatchRequest(BaseModel):
#     employee_email: str
#     tools: List[ToolRequest]
#     urgency: Optional[str] = "normal"

# class DecisionEnum(str, Enum):
#     APPROVED = "APPROVED"
#     REJECTED = "REJECTED"
#     PENDING = "PENDING"

# class ToolDecision(BaseModel):
#     tool_name: str
#     decision: DecisionEnum
#     risk_level: str
#     policy_reference: str
#     reason: str
#     resolution_steps: Optional[str] = None

# class BatchResponse(BaseModel):
#     request_id: str
#     decisions: List[ToolDecision]
#     timestamp: str
#     overall_status: str

# class ExecutionStatus(BaseModel):
#     request_id: str
#     status: str
#     approved_count: int
#     rejected_count: int
#     executed_count: int
#     details: List[Dict]

# # ============================================================================
# # AGENTS + STORES
# # ============================================================================

# requester_agent = RequesterAgent()
# granter_agent   = GranterAgent()
# request_store   = RequestStore()          # MongoDB-backed

# # ============================================================================
# # ENDPOINTS
# # ============================================================================

# @app.post("/submit-request", response_model=BatchResponse)
# async def submit_request(request: BatchRequest, background_tasks: BackgroundTasks):
#     request_id = f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
#     logger.info(f"[{request_id}] From {request.employee_email}")

#     try:
#         # Step 1: Validate
#         employee_context = requester_agent.retrieve_employee_context(request.employee_email)
#         validation = requester_agent.validate_request(request.tools, employee_context)
#         if not validation["valid"]:
#             raise HTTPException(status_code=400, detail=validation["reason"])

#         # Step 2: LLM evaluation
#         granter_response = granter_agent.evaluate_batch_request(
#             request_id=request_id,
#             tools=request.tools,
#             employee_context=employee_context,
#             urgency=request.urgency,
#         )

#         decisions = granter_response["decisions"]
#         approved  = [d for d in decisions if d["decision"] == "APPROVED"]
#         rejected  = [d for d in decisions if d["decision"] == "REJECTED"]

#         overall = (
#             "FULLY_APPROVED"    if not rejected  else
#             "FULLY_REJECTED"    if not approved  else
#             "PARTIALLY_APPROVED"
#         )

#         # Step 3: Persist to MongoDB
#         request_store.save_request(
#             request_id=request_id,
#             employee_email=request.employee_email,
#             employee_context=employee_context,
#             raw_tools=[t.dict() for t in request.tools],
#             decisions=decisions,
#             overall_status=overall,
#         )

#         # Step 4: Background tasks
#         if approved:
#             background_tasks.add_task(execute_approved_tools, request_id, approved, employee_context)
#         if rejected:
#             background_tasks.add_task(notify_rejections, request_id, rejected, employee_context)

#         return BatchResponse(
#             request_id=request_id,
#             decisions=[ToolDecision(**d) for d in decisions],
#             timestamp=datetime.utcnow().isoformat(),
#             overall_status=overall,
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[{request_id}] {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/request-status/{request_id}", response_model=ExecutionStatus)
# async def get_request_status(request_id: str):
#     doc = request_store.get_request(request_id)
#     if not doc:
#         raise HTTPException(status_code=404, detail="Request not found")

#     decisions     = doc["decisions"]
#     approved_cnt  = sum(1 for d in decisions if d["decision"] == "APPROVED")
#     rejected_cnt  = sum(1 for d in decisions if d["decision"] == "REJECTED")
#     executed_cnt  = sum(1 for d in decisions if d.get("executed", False))

#     return ExecutionStatus(
#         request_id=request_id,
#         status=doc.get("status", "unknown"),
#         approved_count=approved_cnt,
#         rejected_count=rejected_cnt,
#         executed_count=executed_cnt,
#         details=decisions,
#     )


# @app.get("/my-requests/{email}")
# async def get_user_requests(email: str):
#     """Return the last 20 requests for a given email (used by the chat UI)."""
#     return request_store.get_user_requests(email)


# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "version": "2.0.0", "store": "mongodb"}


# # ============================================================================
# # BACKGROUND TASKS
# # ============================================================================

# async def execute_approved_tools(request_id, approved_tools, employee_context):
#     logger.info(f"[{request_id}] Executing {len(approved_tools)} approved tools")
#     for tool in approved_tools:
#         try:
#             result = requester_agent.execute_tool_provisioning(
#                 tool_name=tool["tool_name"],
#                 employee_id=employee_context["employee_id"],
#                 decision_context=tool,
#             )
#             tool["executed"] = result["success"]
#             tool["execution_timestamp"] = datetime.utcnow().isoformat()
#         except Exception as e:
#             tool["executed"] = False
#             tool["execution_error"] = str(e)

#     # Refresh all decisions in MongoDB
#     doc = request_store.get_request(request_id)
#     if doc:
#         updated = doc["decisions"]
#         for d in updated:
#             match = next((t for t in approved_tools if t["tool_name"] == d["tool_name"]), None)
#             if match:
#                 d.update(match)
#         request_store.update_status(request_id, "executed", updated)

#     requester_agent.notify_user(
#         email=employee_context["email"],
#         subject=f"Access Request {request_id} - Execution Complete",
#         approved_tools=[t["tool_name"] for t in approved_tools],
#     )


# async def notify_rejections(request_id, rejected_tools, employee_context):
#     requester_agent.notify_rejection(
#         email=employee_context["email"],
#         request_id=request_id,
#         rejected_tools=rejected_tools,
#         manager_email=employee_context.get("manager_email"),
#     )


# # ============================================================================
# # STARTUP
# # ============================================================================

# @app.on_event("startup")
# async def startup_event():
#     create_indexes()
#     logger.info("🚀 Auticket API v2 started (MongoDB)")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")




"""
FastAPI Orchestrator — MongoDB-backed version

Changes from original:
- Imports RequestStore from database.py
- Saves every request + decisions to MongoDB (replaces in-memory dict)
- Reads request status from MongoDB
- Startup event creates indexes
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
import logging
from datetime import datetime

from fastapi import Header
from requester_agent import RequesterAgent
from granter_agent import GranterAgent
from database import RequestStore, UserStore, SessionStore, create_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic IT Service Approval System",
    description="Token-efficient, goal-driven approval automation (MongoDB)",
    version="2.0.0",
)

# ============================================================================
# MODELS
# ============================================================================

class ToolRequest(BaseModel):
    tool_name: str
    version: Optional[str] = None
    justification: str

class BatchRequest(BaseModel):
    employee_email: str
    tools: List[ToolRequest]
    urgency: Optional[str] = "normal"

class DecisionEnum(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class ToolDecision(BaseModel):
    tool_name: str
    decision: DecisionEnum
    risk_level: str
    policy_reference: str
    reason: str
    resolution_steps: Optional[str] = None

class BatchResponse(BaseModel):
    request_id: str
    decisions: List[ToolDecision]
    timestamp: str
    overall_status: str

class ExecutionStatus(BaseModel):
    request_id: str
    status: str
    approved_count: int
    rejected_count: int
    executed_count: int
    details: List[Dict]

# Auth models
class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    role: Optional[str] = "Software Engineer"
    department: Optional[str] = "Engineering"
    security_clearance: Optional[str] = "standard"
    location: Optional[str] = "Unknown"
    manager_email: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    email: str
    name: str
    role: str
    department: str
    message: str

# ============================================================================
# AGENTS + STORES
# ============================================================================

requester_agent = RequesterAgent()
granter_agent   = GranterAgent()
request_store   = RequestStore()
user_store      = UserStore()
session_store   = SessionStore()

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/submit-request", response_model=BatchResponse)
async def submit_request(request: BatchRequest, background_tasks: BackgroundTasks):
    request_id = f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"[{request_id}] From {request.employee_email}")

    try:
        # Step 1: Validate
        employee_context = requester_agent.retrieve_employee_context(request.employee_email)
        validation = requester_agent.validate_request(request.tools, employee_context)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["reason"])

        # Step 2: LLM evaluation
        granter_response = granter_agent.evaluate_batch_request(
            request_id=request_id,
            tools=request.tools,
            employee_context=employee_context,
            urgency=request.urgency,
        )

        decisions = granter_response["decisions"]
        approved  = [d for d in decisions if d["decision"] == "APPROVED"]
        rejected  = [d for d in decisions if d["decision"] == "REJECTED"]

        overall = (
            "FULLY_APPROVED"    if not rejected  else
            "FULLY_REJECTED"    if not approved  else
            "PARTIALLY_APPROVED"
        )

        # Step 3: Persist to MongoDB
        request_store.save_request(
            request_id=request_id,
            employee_email=request.employee_email,
            employee_context=employee_context,
            raw_tools=[t.dict() for t in request.tools],
            decisions=decisions,
            overall_status=overall,
        )

        # Step 4: Background tasks
        if approved:
            background_tasks.add_task(execute_approved_tools, request_id, approved, employee_context)
        if rejected:
            background_tasks.add_task(notify_rejections, request_id, rejected, employee_context)

        return BatchResponse(
            request_id=request_id,
            decisions=[ToolDecision(**d) for d in decisions],
            timestamp=datetime.utcnow().isoformat(),
            overall_status=overall,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/request-status/{request_id}", response_model=ExecutionStatus)
async def get_request_status(request_id: str):
    doc = request_store.get_request(request_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Request not found")

    decisions     = doc["decisions"]
    approved_cnt  = sum(1 for d in decisions if d["decision"] == "APPROVED")
    rejected_cnt  = sum(1 for d in decisions if d["decision"] == "REJECTED")
    executed_cnt  = sum(1 for d in decisions if d.get("executed", False))

    return ExecutionStatus(
        request_id=request_id,
        status=doc.get("status", "unknown"),
        approved_count=approved_cnt,
        rejected_count=rejected_cnt,
        executed_count=executed_cnt,
        details=decisions,
    )


@app.get("/my-requests/{email}")
async def get_user_requests(email: str):
    """Return the last 20 requests for a given email (used by the chat UI)."""
    return request_store.get_user_requests(email)


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

def _resolve_session(authorization: Optional[str]) -> Optional[Dict]:
    """
    Helper: extract Bearer token from Authorization header and
    return the user dict, or None if invalid/expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    session = session_store.get_session(token)
    if not session:
        return None
    return user_store.get_by_email(session["email"])


@app.post("/auth/signup", status_code=201)
async def signup(body: SignupRequest):
    """
    Register a new user.
    Stores email (lowercased), hashed password, and profile in the
    `users` collection.
    """
    try:
        user_store.create_user(
            email=body.email,
            password=body.password,
            name=body.name,
            role=body.role,
            department=body.department,
            security_clearance=body.security_clearance,
            location=body.location,
            manager_email=body.manager_email,
        )
        logger.info(f"New user registered: {body.email}")
        return {"message": "Account created successfully. You can now log in."}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """
    Authenticate user, create a session in the `sessions` collection,
    and return a Bearer token.
    """
    user = user_store.authenticate(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = session_store.create_session(user["email"])
    logger.info(f"User logged in: {user['email']}")

    return LoginResponse(
        token=token,
        email=user["email"],
        name=user.get("name", ""),
        role=user.get("role", ""),
        department=user.get("department", ""),
        message=f"Welcome back, {user.get('name', user['email'])}!",
    )


@app.post("/auth/logout")
async def logout_endpoint(authorization: Optional[str] = Header(None)):
    """
    Invalidate the session token.
    Pass the token as:  Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Missing Authorization header.")
    token = authorization.split(" ", 1)[1].strip()
    session_store.delete_session(token)
    return {"message": "Logged out successfully."}


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/users/me")
async def get_me(authorization: Optional[str] = Header(None)):
    """
    Return the profile of the currently logged-in user.
    Reads from the `users` collection using the session token.
    """
    user = _resolve_session(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")

    # Strip internal fields before returning
    return {
        "email":              user["email"],
        "name":               user.get("name"),
        "role":               user.get("role"),
        "department":         user.get("department"),
        "security_clearance": user.get("security_clearance"),
        "location":           user.get("location"),
        "manager_email":      user.get("manager_email"),
        "created_at":         str(user.get("created_at", "")),
    }


@app.get("/users/me/requests")
async def get_my_requests(authorization: Optional[str] = Header(None)):
    """
    Return the last 20 approval requests for the logged-in user.
    Reads from the `requests` collection filtered by email.
    """
    user = _resolve_session(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")

    docs = request_store.get_user_requests(user["email"])

    # Serialize datetime fields for JSON
    for doc in docs:
        if "created_at" in doc:
            doc["created_at"] = str(doc["created_at"])
    return docs


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "store": "mongodb"}


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def execute_approved_tools(request_id, approved_tools, employee_context):
    logger.info(f"[{request_id}] Executing {len(approved_tools)} approved tools")
    for tool in approved_tools:
        try:
            result = requester_agent.execute_tool_provisioning(
                tool_name=tool["tool_name"],
                employee_id=employee_context["employee_id"],
                decision_context=tool,
            )
            tool["executed"] = result["success"]
            tool["execution_timestamp"] = datetime.utcnow().isoformat()
        except Exception as e:
            tool["executed"] = False
            tool["execution_error"] = str(e)

    # Refresh all decisions in MongoDB
    doc = request_store.get_request(request_id)
    if doc:
        updated = doc["decisions"]
        for d in updated:
            match = next((t for t in approved_tools if t["tool_name"] == d["tool_name"]), None)
            if match:
                d.update(match)
        request_store.update_status(request_id, "executed", updated)

    requester_agent.notify_user(
        email=employee_context["email"],
        subject=f"Access Request {request_id} - Execution Complete",
        approved_tools=[t["tool_name"] for t in approved_tools],
    )


async def notify_rejections(request_id, rejected_tools, employee_context):
    requester_agent.notify_rejection(
        email=employee_context["email"],
        request_id=request_id,
        rejected_tools=rejected_tools,
        manager_email=employee_context.get("manager_email"),
    )


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    create_indexes()
    logger.info("🚀 Auticket API v2 started (MongoDB)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")