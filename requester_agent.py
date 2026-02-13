"""
Requester Agent - Deterministic Orchestration and Execution

This agent is NON-LLM and handles:
1. Employee context retrieval
2. Request validation
3. Tool provisioning/installation (simulated)
4. User notifications

Architecture Decision: This agent is purely deterministic - no reasoning,
just execution. This keeps it fast, predictable, and token-free.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# ============================================================================
# MOCK DATA STORES
# In production, these would be database/LDAP/Active Directory queries
# ============================================================================

EMPLOYEE_DATABASE = {
    "john.doe@company.com": {
        "employee_id": "EMP001",
        "name": "John Doe",
        "email": "john.doe@company.com",
        "role": "Software Engineer",
        "department": "Engineering",
        "manager_id": "MGR001",
        "manager_email": "jane.manager@company.com",
        "security_clearance": "standard",
        "location": "US-West"
    },
    "alice.admin@company.com": {
        "employee_id": "EMP002",
        "name": "Alice Admin",
        "email": "alice.admin@company.com",
        "role": "DevOps Engineer",
        "department": "Infrastructure",
        "manager_id": "MGR002",
        "manager_email": "bob.manager@company.com",
        "security_clearance": "elevated",
        "location": "US-East"
    },
    "intern.user@company.com": {
        "employee_id": "EMP003",
        "name": "Intern User",
        "email": "intern.user@company.com",
        "role": "Intern",
        "department": "Engineering",
        "manager_id": "MGR001",
        "manager_email": "jane.manager@company.com",
        "security_clearance": "restricted",
        "location": "US-West"
    }
}

# Validation rules (deterministic checks)
BLOCKED_TOOLS = ["mimikatz", "metasploit", "sqlmap"]  # Example security blocklist
MAX_TOOLS_PER_REQUEST = 10
MIN_JUSTIFICATION_LENGTH = 20


class RequesterAgent:
    """
    Requester Agent - Pure execution and coordination
    
    This agent does NOT use LLMs. It's a service layer that:
    - Retrieves data from corporate systems
    - Validates inputs against business rules
    - Executes approved actions
    - Sends notifications
    
    Why no LLM? Speed, cost, determinism. These operations should be
    predictable and fast.
    """
    
    def __init__(self):
        """Initialize the requester agent"""
        logger.info("Initializing Requester Agent (non-LLM)")
        self.notification_queue = []  # Mock notification system
    
    # ========================================================================
    # CONTEXT RETRIEVAL (Deterministic)
    # ========================================================================
    
    def retrieve_employee_context(self, email: str) -> Dict:
        """
        Retrieve employee information from corporate directory.
        
        In production, this would query:
        - Active Directory / LDAP
        - HRIS system
        - IAM database
        
        Returns enriched context needed for policy evaluation.
        """
        logger.info(f"Retrieving context for {email}")
        
        # Mock database lookup
        if email not in EMPLOYEE_DATABASE:
            # In production, raise an exception or create limited context
            return {
                "employee_id": "UNKNOWN",
                "email": email,
                "role": "Unknown",
                "department": "Unknown",
                "manager_id": None,
                "manager_email": None,
                "security_clearance": "restricted",
                "location": "Unknown"
            }
        
        employee_data = EMPLOYEE_DATABASE[email].copy()
        
        # Add additional context
        employee_data["retrieval_timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(f"Retrieved context: {employee_data['name']} ({employee_data['role']})")
        
        return employee_data
    
    # ========================================================================
    # REQUEST VALIDATION (Deterministic)
    # ========================================================================
    
    def validate_request(
        self,
        tools: List,
        employee_context: Dict
    ) -> Dict[str, any]:
        """
        Validate request against business rules.
        
        This is pure logic - no LLM needed for rule checking.
        Returns: {"valid": bool, "reason": str}
        """
        # Check 1: Tool count limit
        if len(tools) > MAX_TOOLS_PER_REQUEST:
            return {
                "valid": False,
                "reason": f"Too many tools requested (max {MAX_TOOLS_PER_REQUEST})"
            }
        
        # Check 2: Blocked tools
        for tool in tools:
            if tool.tool_name.lower() in BLOCKED_TOOLS:
                return {
                    "valid": False,
                    "reason": f"Tool '{tool.tool_name}' is blocked by security policy"
                }
        
        # Check 3: Justification quality
        for tool in tools:
            if len(tool.justification) < MIN_JUSTIFICATION_LENGTH:
                return {
                    "valid": False,
                    "reason": f"Justification for '{tool.tool_name}' is too short (min {MIN_JUSTIFICATION_LENGTH} chars)"
                }
            
            # Check for placeholder text
            placeholder_patterns = [
                r"test",
                r"need it",
                r"want it",
                r"asdf",
                r"xxx"
            ]
            justification_lower = tool.justification.lower()
            if any(re.search(pattern, justification_lower) for pattern in placeholder_patterns):
                if len(tool.justification) < 50:  # Be lenient if they write more
                    return {
                        "valid": False,
                        "reason": f"Justification for '{tool.tool_name}' appears to be a placeholder. Please provide a real business justification."
                    }
        
        # Check 4: Employee context exists
        if employee_context.get("employee_id") == "UNKNOWN":
            return {
                "valid": False,
                "reason": "Employee not found in directory. Please contact IT support."
            }
        
        # All checks passed
        logger.info(f"Request validation passed for {len(tools)} tools")
        return {
            "valid": True,
            "reason": "All validation checks passed"
        }
    
    # ========================================================================
    # TOOL EXECUTION (Simulated)
    # ========================================================================
    
    def execute_tool_provisioning(
        self,
        tool_name: str,
        employee_id: str,
        decision_context: Dict
    ) -> Dict:
        """
        Execute the actual provisioning of an approved tool.
        
        In production, this would:
        - Call package managers (apt, yum, chocolatey)
        - Update IAM roles
        - Grant database access
        - Configure VPN access
        - Update LDAP groups
        
        For this project, we simulate the execution.
        """
        logger.info(f"Executing provisioning: {tool_name} for {employee_id}")
        
        # Simulate different provisioning methods based on tool type
        execution_steps = []
        
        # Mock execution based on tool name patterns
        if "docker" in tool_name.lower():
            execution_steps = [
                "Added user to docker group",
                "Updated container registry permissions",
                "Configured resource limits"
            ]
        elif "aws" in tool_name.lower() or "cloud" in tool_name.lower():
            execution_steps = [
                "Created IAM role",
                "Attached policy: ReadOnlyAccess",
                "Generated access credentials"
            ]
        elif "database" in tool_name.lower() or "sql" in tool_name.lower():
            execution_steps = [
                "Created database user account",
                "Granted SELECT permissions",
                "Configured connection pooling"
            ]
        else:
            execution_steps = [
                f"Installed {tool_name} via package manager",
                "Configured environment variables",
                "Added to system PATH"
            ]
        
        # Simulate execution time (in production, this would be actual work)
        import time
        time.sleep(0.1)  # Simulate work
        
        result = {
            "success": True,
            "tool_name": tool_name,
            "employee_id": employee_id,
            "status": "provisioned",
            "execution_steps": execution_steps,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": decision_context.get("risk_level", "unknown")
        }
        
        logger.info(f"✓ Provisioning complete: {tool_name}")
        
        return result
    
    # ========================================================================
    # NOTIFICATIONS (Simulated)
    # ========================================================================
    
    def notify_user(
        self,
        email: str,
        subject: str,
        approved_tools: List[str]
    ) -> Dict:
        """
        Send approval notification to user.
        
        In production: SMTP, Slack, Teams, ServiceNow
        """
        message = f"""
        Your access request has been approved!
        
        Approved Tools:
        {chr(10).join(f'  - {tool}' for tool in approved_tools)}
        
        These tools have been provisioned and are ready to use.
        
        Questions? Contact IT Support.
        """
        
        notification = {
            "type": "approval",
            "to": email,
            "subject": subject,
            "body": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.notification_queue.append(notification)
        logger.info(f"📧 Notification queued: {email} - {subject}")
        
        return {"status": "queued", "notification_id": len(self.notification_queue)}
    
    def notify_rejection(
        self,
        email: str,
        request_id: str,
        rejected_tools: List[Dict],
        manager_email: Optional[str] = None
    ) -> Dict:
        """
        Send rejection notification with resolution steps.
        """
        tools_with_reasons = "\n".join([
            f"""
  Tool: {tool['tool_name']}
  Reason: {tool['reason']}
  Resolution: {tool.get('resolution_steps', 'Contact your manager for approval')}
  Policy Reference: {tool['policy_reference']}
            """
            for tool in rejected_tools
        ])
        
        message = f"""
        Your access request {request_id} was rejected for the following tools:
        
        {tools_with_reasons}
        
        Next Steps:
        - Review the resolution steps above
        - Contact your manager ({manager_email or 'manager'}) if you need an exception
        - Resubmit with additional justification if appropriate
        
        Questions? Contact IT Security.
        """
        
        notification = {
            "type": "rejection",
            "to": email,
            "cc": manager_email,
            "subject": f"Access Request {request_id} - Action Required",
            "body": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.notification_queue.append(notification)
        logger.info(f"📧 Rejection notification queued: {email}")
        
        return {"status": "queued", "notification_id": len(self.notification_queue)}
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_notification_queue(self) -> List[Dict]:
        """Get all pending notifications (for testing/debugging)"""
        return self.notification_queue.copy()
    
    def clear_notification_queue(self):
        """Clear notification queue (for testing)"""
        self.notification_queue.clear()
        logger.info("Notification queue cleared")


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Test the requester agent independently
    agent = RequesterAgent()
    
    # Test context retrieval
    context = agent.retrieve_employee_context("john.doe@company.com")
    print(f"✓ Retrieved context: {context['name']}")
    
    # Test execution
    result = agent.execute_tool_provisioning(
        tool_name="Docker",
        employee_id="EMP001",
        decision_context={"risk_level": "medium"}
    )
    print(f"✓ Execution result: {result['status']}")
    
    # Test notifications
    agent.notify_user(
        email="john.doe@company.com",
        subject="Test Notification",
        approved_tools=["Docker", "AWS CLI"]
    )
    print(f"✓ Notifications queued: {len(agent.get_notification_queue())}")
