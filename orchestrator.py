"""
FastAPI Orchestrator for Agentic IT Service Approval System

This orchestrator acts as the deterministic control plane:
- Routes requests between agents
- Manages request lifecycle
- Triggers execution workflows
- NO LLM calls here - pure coordination logic

Architecture: The orchestrator is the "nervous system" - it coordinates
but doesn't reason. All reasoning is delegated to specialized agents.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
import logging
from datetime import datetime

from requester_agent import RequesterAgent
from granter_agent import GranterAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic IT Service Approval System",
    description="Token-efficient, goal-driven approval automation",
    version="1.0.0"
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ToolRequest(BaseModel):
    """Individual tool request"""
    tool_name: str = Field(..., description="Name of software/tool requested")
    version: Optional[str] = Field(None, description="Specific version if needed")
    justification: str = Field(..., description="Business justification for access")

class BatchRequest(BaseModel):
    """Batch request from user"""
    employee_email: str = Field(..., description="Requester's email")
    tools: List[ToolRequest] = Field(..., description="List of tools requested")
    urgency: Optional[str] = Field("normal", description="normal/high/critical")

class DecisionEnum(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class ToolDecision(BaseModel):
    """Decision for a single tool"""
    tool_name: str
    decision: DecisionEnum
    risk_level: str
    policy_reference: str
    reason: str
    resolution_steps: Optional[str] = None

class BatchResponse(BaseModel):
    """Response after granter evaluation"""
    request_id: str
    decisions: List[ToolDecision]
    timestamp: str
    overall_status: str

class ExecutionStatus(BaseModel):
    """Status response for request tracking"""
    request_id: str
    status: str
    approved_count: int
    rejected_count: int
    executed_count: int
    details: List[Dict]

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

# Initialize agents once at startup (singleton pattern)
requester_agent = RequesterAgent()
granter_agent = GranterAgent()

# In-memory request tracking (use Redis/DB in production)
request_store: Dict[str, Dict] = {}

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.post("/submit-request", response_model=BatchResponse)
async def submit_request(
    request: BatchRequest,
    background_tasks: BackgroundTasks
) -> BatchResponse:
    """
    Main entry point for tool access requests.
    
    Workflow:
    1. Validate and enrich request (via Requester Agent)
    2. Send to Granter Agent for policy evaluation
    3. Return structured decision
    4. Trigger execution in background for approved tools
    
    This is deterministic orchestration - no LLM reasoning here.
    """
    request_id = f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    logger.info(f"[{request_id}] Received request from {request.employee_email}")
    logger.info(f"[{request_id}] Tools requested: {[t.tool_name for t in request.tools]}")
    
    try:
        # ====================================================================
        # STEP 1: REQUESTER AGENT - Validate and enrich request
        # ====================================================================
        # Deterministic operations: no LLM, just data retrieval and validation
        
        employee_context = requester_agent.retrieve_employee_context(
            request.employee_email
        )
        
        validation_result = requester_agent.validate_request(
            tools=request.tools,
            employee_context=employee_context
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request: {validation_result['reason']}"
            )
        
        # ====================================================================
        # STEP 2: GRANTER AGENT - Policy reasoning and approval decision
        # ====================================================================
        # LLM reasoning happens here - ONE call for the entire batch
        
        logger.info(f"[{request_id}] Sending to Granter Agent for evaluation")
        
        granter_response = granter_agent.evaluate_batch_request(
            request_id=request_id,
            tools=request.tools,
            employee_context=employee_context,
            urgency=request.urgency
        )
        
        # ====================================================================
        # STEP 3: Store and prepare response
        # ====================================================================
        
        request_store[request_id] = {
            "request": request.dict(),
            "employee_context": employee_context,
            "decisions": granter_response["decisions"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "evaluated"
        }
        
        # Count approvals/rejections
        approved = [d for d in granter_response["decisions"] if d["decision"] == "APPROVED"]
        rejected = [d for d in granter_response["decisions"] if d["decision"] == "REJECTED"]
        
        overall_status = "FULLY_APPROVED" if len(rejected) == 0 else \
                        "FULLY_REJECTED" if len(approved) == 0 else \
                        "PARTIALLY_APPROVED"
        
        response = BatchResponse(
            request_id=request_id,
            decisions=[ToolDecision(**d) for d in granter_response["decisions"]],
            timestamp=datetime.utcnow().isoformat(),
            overall_status=overall_status
        )
        
        # ====================================================================
        # STEP 4: Trigger execution in background for approved tools
        # ====================================================================
        
        if len(approved) > 0:
            background_tasks.add_task(
                execute_approved_tools,
                request_id,
                approved,
                employee_context
            )
        
        # Send notifications for rejected tools
        if len(rejected) > 0:
            background_tasks.add_task(
                notify_rejections,
                request_id,
                rejected,
                employee_context
            )
        
        logger.info(f"[{request_id}] Evaluation complete: {len(approved)} approved, {len(rejected)} rejected")
        
        return response
        
    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/request-status/{request_id}", response_model=ExecutionStatus)
async def get_request_status(request_id: str) -> ExecutionStatus:
    """
    Check the status of a submitted request.
    Useful for tracking execution progress.
    """
    if request_id not in request_store:
        raise HTTPException(status_code=404, detail="Request not found")
    
    stored_request = request_store[request_id]
    decisions = stored_request["decisions"]
    
    approved = [d for d in decisions if d["decision"] == "APPROVED"]
    rejected = [d for d in decisions if d["decision"] == "REJECTED"]
    
    # Check execution status
    executed_count = sum(1 for d in decisions if d.get("executed", False))
    
    return ExecutionStatus(
        request_id=request_id,
        status=stored_request.get("status", "unknown"),
        approved_count=len(approved),
        rejected_count=len(rejected),
        executed_count=executed_count,
        details=decisions
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agentic-approval-orchestrator",
        "agents": {
            "requester": "active",
            "granter": "active"
        }
    }

# ============================================================================
# BACKGROUND EXECUTION TASKS
# ============================================================================

async def execute_approved_tools(
    request_id: str,
    approved_tools: List[Dict],
    employee_context: Dict
):
    """
    Execute installation/provisioning for approved tools.
    Runs in background to avoid blocking the response.
    
    This is deterministic execution - no LLM reasoning.
    """
    logger.info(f"[{request_id}] Starting execution for {len(approved_tools)} approved tools")
    
    for tool_decision in approved_tools:
        try:
            # Use Requester Agent to handle execution
            execution_result = requester_agent.execute_tool_provisioning(
                tool_name=tool_decision["tool_name"],
                employee_id=employee_context["employee_id"],
                decision_context=tool_decision
            )
            
            # Update execution status
            tool_decision["executed"] = execution_result["success"]
            tool_decision["execution_timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"[{request_id}] Executed {tool_decision['tool_name']}: {execution_result['status']}")
            
        except Exception as e:
            logger.error(f"[{request_id}] Execution failed for {tool_decision['tool_name']}: {str(e)}")
            tool_decision["executed"] = False
            tool_decision["execution_error"] = str(e)
    
    # Update overall request status
    request_store[request_id]["status"] = "executed"
    
    # Notify user of completion
    requester_agent.notify_user(
        email=employee_context["email"],
        subject=f"Access Request {request_id} - Execution Complete",
        approved_tools=[t["tool_name"] for t in approved_tools]
    )


async def notify_rejections(
    request_id: str,
    rejected_tools: List[Dict],
    employee_context: Dict
):
    """
    Send notifications for rejected tools with resolution steps.
    """
    logger.info(f"[{request_id}] Sending rejection notifications for {len(rejected_tools)} tools")
    
    requester_agent.notify_rejection(
        email=employee_context["email"],
        request_id=request_id,
        rejected_tools=rejected_tools,
        manager_email=employee_context.get("manager_email")
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 Agentic IT Approval System starting up")
    logger.info("✓ Requester Agent initialized")
    logger.info("✓ Granter Agent initialized (with RAG)")
    logger.info("✓ Orchestrator ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Agentic IT Approval System")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
