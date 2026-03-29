"""
Requester Agent - Deterministic Orchestration and Execution

Changes from original:
- Employee context is now retrieved from MongoDB (UserStore) instead of
  the hardcoded EMPLOYEE_DATABASE dict.
- Everything else (validation, execution simulation, notifications) unchanged.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import re

from database import UserStore

logger = logging.getLogger(__name__)

# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

BLOCKED_TOOLS = ["mimikatz", "metasploit", "sqlmap"]
MAX_TOOLS_PER_REQUEST = 10
MIN_JUSTIFICATION_LENGTH = 20


class RequesterAgent:
    def __init__(self):
        logger.info("Initializing Requester Agent (non-LLM, MongoDB-backed)")
        self.user_store = UserStore()
        self.notification_queue = []

    # ========================================================================
    # CONTEXT RETRIEVAL  — now reads from MongoDB
    # ========================================================================

    def retrieve_employee_context(self, email: str) -> Dict:
        """Fetch employee info from MongoDB users collection."""
        logger.info(f"Retrieving context for {email}")

        user = self.user_store.get_by_email(email)

        if not user:
            return {
                "employee_id": "UNKNOWN",
                "email": email,
                "role": "Unknown",
                "department": "Unknown",
                "manager_id": None,
                "manager_email": None,
                "security_clearance": "restricted",
                "location": "Unknown",
                "name": "Unknown",
            }

        context = {
            "employee_id": user.get("_id", "UNKNOWN"),
            "email": user["email"],
            "name": user.get("name", "Unknown"),
            "role": user.get("role", "Unknown"),
            "department": user.get("department", "Unknown"),
            "manager_email": user.get("manager_email"),
            "security_clearance": user.get("security_clearance", "standard"),
            "location": user.get("location", "Unknown"),
            "retrieval_timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Retrieved context: {context['name']} ({context['role']})")
        return context

    # ========================================================================
    # VALIDATION  (unchanged)
    # ========================================================================

    def validate_request(self, tools: List, employee_context: Dict) -> Dict:
        if len(tools) > MAX_TOOLS_PER_REQUEST:
            return {"valid": False, "reason": f"Too many tools (max {MAX_TOOLS_PER_REQUEST})"}

        for tool in tools:
            if tool.tool_name.lower() in BLOCKED_TOOLS:
                return {"valid": False, "reason": f"'{tool.tool_name}' is blocked by security policy"}

        for tool in tools:
            if len(tool.justification) < MIN_JUSTIFICATION_LENGTH:
                return {
                    "valid": False,
                    "reason": f"Justification for '{tool.tool_name}' is too short (min {MIN_JUSTIFICATION_LENGTH} chars)",
                }
            placeholder_patterns = [r"test", r"need it", r"want it", r"asdf", r"xxx"]
            if any(re.search(p, tool.justification.lower()) for p in placeholder_patterns):
                if len(tool.justification) < 50:
                    return {
                        "valid": False,
                        "reason": f"Justification for '{tool.tool_name}' appears to be a placeholder.",
                    }

        if employee_context.get("employee_id") == "UNKNOWN":
            return {"valid": False, "reason": "Employee not found. Please contact IT support."}

        logger.info(f"Validation passed for {len(tools)} tools")
        return {"valid": True, "reason": "All checks passed"}

    # ========================================================================
    # EXECUTION  (unchanged — simulated)
    # ========================================================================

    def execute_tool_provisioning(self, tool_name: str, employee_id: str, decision_context: Dict) -> Dict:
        logger.info(f"Provisioning {tool_name} for {employee_id}")

        if "docker" in tool_name.lower():
            steps = ["Added user to docker group", "Updated registry permissions", "Configured limits"]
        elif "aws" in tool_name.lower() or "cloud" in tool_name.lower():
            steps = ["Created IAM role", "Attached ReadOnlyAccess policy", "Generated credentials"]
        elif "database" in tool_name.lower() or "sql" in tool_name.lower():
            steps = ["Created DB user", "Granted SELECT permissions", "Configured pooling"]
        else:
            steps = [f"Installed {tool_name} via package manager", "Set env vars", "Added to PATH"]

        import time; time.sleep(0.1)

        return {
            "success": True,
            "tool_name": tool_name,
            "employee_id": employee_id,
            "status": "provisioned",
            "execution_steps": steps,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": decision_context.get("risk_level", "unknown"),
        }

    # ========================================================================
    # NOTIFICATIONS  (unchanged)
    # ========================================================================

    def notify_user(self, email: str, subject: str, approved_tools: List[str]) -> Dict:
        body = f"Approved: {', '.join(approved_tools)}. Tools are ready to use."
        notification = {"type": "approval", "to": email, "subject": subject, "body": body,
                        "timestamp": datetime.utcnow().isoformat()}
        self.notification_queue.append(notification)
        logger.info(f"Notification queued: {email}")
        return {"status": "queued"}

    def notify_rejection(self, email: str, request_id: str, rejected_tools: List[Dict],
                         manager_email: Optional[str] = None) -> Dict:
        notification = {"type": "rejection", "to": email, "cc": manager_email,
                        "subject": f"Request {request_id} - Action Required",
                        "timestamp": datetime.utcnow().isoformat()}
        self.notification_queue.append(notification)
        logger.info(f"Rejection notification queued: {email}")
        return {"status": "queued"}

    def get_notification_queue(self) -> List[Dict]:
        return self.notification_queue.copy()
