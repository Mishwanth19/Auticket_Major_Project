"""
Granter Agent - LLM-Powered Policy Reasoning

This agent uses LLM ONLY for:
1. Reasoning over policies
2. Risk assessment
3. Generating structured approval decisions

Architecture Decision: ONE LLM call per batch request.
RAG retrieves relevant policy snippets (top-k=5 max).
Policies are pre-summarized to minimize tokens.
Output is structured JSON - no conversational responses.
"""

import logging
from typing import Dict, List
import json
from datetime import datetime
from dotenv import load_dotenv
# LangChain imports (ONLY for RAG and structured output)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from pydantic import BaseModel, Field



from policies import POLICY_DOCUMENTS, ACCESS_MATRIX, get_policy_summary
load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# STRUCTURED OUTPUT MODELS
# ============================================================================
LLM_AVAILABLE = True
class ToolDecisionOutput(BaseModel):
    """Structured output for a single tool decision"""
    tool_name: str = Field(description="Name of the tool being evaluated")
    decision: str = Field(description="APPROVED or REJECTED")
    risk_level: str = Field(description="low, medium, high, or critical")
    policy_reference: str = Field(description="Specific policy section referenced")
    reason: str = Field(description="Clear explanation for the decision")
    resolution_steps: str = Field(
        default="",
        description="Steps to resolve if rejected, empty if approved"
    )

class BatchDecisionOutput(BaseModel):
    """Structured output for batch decisions"""
    decisions: List[ToolDecisionOutput] = Field(
        description="List of decisions for each requested tool"
    )


# ============================================================================
# GRANTER AGENT
# ============================================================================

class GranterAgent:
    """
    Granter Agent - Policy Reasoning with LLM + RAG
    
    This agent:
    1. Uses RAG to retrieve relevant policy snippets (top-k ≤ 5)
    2. Retrieves access rules from pre-computed matrix
    3. Makes ONE LLM call per batch to reason over all tools
    4. Returns structured JSON decisions
    
    Token Efficiency Strategy:
    - Policies are pre-summarized (see policies.py)
    - RAG returns only relevant snippets (top-k=5)
    - Batch processing (all tools in one LLM call)
    - Structured output (no conversational fluff)
    - No chat history maintained
    """
    
    def __init__(self):
        """Initialize the granter agent with RAG pipeline"""
        logger.info("Initializing Granter Agent (LLM + RAG)")
        
        # Initialize RAG vector store
        self.vector_store = self._initialize_vector_store()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize prompt template
        self.prompt_template = self._create_prompt_template()
        
        logger.info("✓ Granter Agent ready (RAG initialized)")
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def _initialize_vector_store(self) -> FAISS:
        """
        Initialize FAISS vector store with policy documents.
        
        In production:
        - Use Chroma/Pinecone for persistence
        - Regularly update with new policies
        - Version control policy documents
        """
        logger.info("Initializing RAG vector store...")
        
        # Use lightweight embeddings (no API calls needed)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Create vector store from policy documents
        # Each document is already summarized (token-efficient)
        texts = []
        metadatas = []
        
        for policy_id, policy_data in POLICY_DOCUMENTS.items():
            # Use the pre-summarized content
            texts.append(policy_data["summary"])
            metadatas.append({
                "policy_id": policy_id,
                "title": policy_data["title"],
                "category": policy_data["category"]
            })
        
        vector_store = FAISS.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas
        )
        
        logger.info(f"✓ Vector store initialized with {len(texts)} policy documents")
        
        return vector_store
    
    def _initialize_llm(self):
        """
        Initialize Groq LLM for policy reasoning.
        """
        if not LLM_AVAILABLE:
            logger.warning("⚠ GROQ_API_KEY not set - using Mock LLM")
            return MockLLM()

        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_tokens=2000,
            )
            logger.info("✓ LLM initialized: Groq (llama-3.3-70b-versatile)")
            return llm
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            return MockLLM()

    
    def _create_prompt_template(self) -> PromptTemplate:
        """
        Create the prompt template for policy reasoning.
        
        This prompt is carefully designed to:
        - Be concise (minimize tokens)
        - Request structured output
        - Focus on reasoning, not conversation
        - Handle batch evaluations
        """
        template = """You are a Policy Evaluation Agent for an enterprise IT system.

Your task: Evaluate tool access requests against company policies and return structured decisions.

EMPLOYEE CONTEXT:
- Role: {role}
- Department: {department}
- Security Clearance: {security_clearance}
- Location: {location}

RELEVANT POLICIES (retrieved via RAG):
{relevant_policies}

ACCESS RULES (from role-based matrix):
{access_rules}

TOOLS REQUESTED:
{tools_requested}

EVALUATION CRITERIA:
1. Does the employee's role typically need this tool?
2. Is the justification valid and specific?
3. What is the security risk level?
4. Are there any policy violations?
5. Does urgency warrant elevated risk acceptance?

RISK LEVELS:
- low: Standard tools, minimal data access, common for role
- medium: Elevated privileges, sensitive data access, requires justification
- high: Admin tools, production access, significant risk
- critical: Security tools, root access, compliance-sensitive

DECISION RULES:
- APPROVED: Policy allows, low-medium risk, good justification
- REJECTED: Policy prohibits, unjustified high risk, insufficient justification

OUTPUT REQUIREMENTS:
Return a JSON object with a "decisions" array. Each decision must include:
- tool_name: exact name from request
- decision: "APPROVED" or "REJECTED"
- risk_level: "low", "medium", "high", or "critical"
- policy_reference: specific policy section (e.g., "POL-SEC-001 §3.2")
- reason: clear, specific explanation (2-3 sentences)
- resolution_steps: if rejected, how to get approval (empty if approved)

CRITICAL: Return ONLY valid JSON. No preamble, no markdown, no explanations outside the JSON structure.

{format_instructions}
"""
        
        # Create parser for structured output
        parser = PydanticOutputParser(pydantic_object=BatchDecisionOutput)
        
        prompt = PromptTemplate(
            template=template,
            input_variables=[
                "role",
                "department", 
                "security_clearance",
                "location",
                "relevant_policies",
                "access_rules",
                "tools_requested"
            ],
            partial_variables={
                "format_instructions": parser.get_format_instructions()
            }
        )
        
        return prompt
    
    # ========================================================================
    # CORE EVALUATION METHOD
    # ========================================================================
    
    def evaluate_batch_request(
        self,
        request_id: str,
        tools: List,
        employee_context: Dict,
        urgency: str = "normal"
    ) -> Dict:
        """
        Evaluate a batch of tool requests using LLM reasoning.
        
        This is the ONLY method that calls the LLM.
        ONE call handles all tools in the batch.
        
        Flow:
        1. Retrieve relevant policies via RAG (top-k=5)
        2. Retrieve access rules from matrix
        3. Format prompt with all context
        4. LLM reasons and returns structured JSON
        5. Parse and return decisions
        """
        logger.info(f"[{request_id}] Starting policy evaluation for {len(tools)} tools")
        
        # ====================================================================
        # STEP 1: Retrieve relevant policies via RAG
        # ====================================================================
        
        # Combine all tool names and justifications for semantic search
        query_text = " ".join([
            f"{tool.tool_name} {tool.justification}" 
            for tool in tools
        ])
        
        # Retrieve top-k relevant policies (k=5 for token efficiency)
        relevant_docs = self.vector_store.similarity_search(
            query=query_text,
            k=5
        )
        
        # Format policies for prompt
        relevant_policies = "\n\n".join([
            f"Policy: {doc.metadata['title']}\n{doc.page_content}"
            for doc in relevant_docs
        ])
        
        logger.info(f"[{request_id}] Retrieved {len(relevant_docs)} relevant policies")
        
        # ====================================================================
        # STEP 2: Retrieve access rules from matrix
        # ====================================================================
        
        employee_role = employee_context.get("role", "Unknown")
        access_rules = self._get_access_rules(employee_role, tools)
        
        # ====================================================================
        # STEP 3: Format tools for prompt
        # ====================================================================
        
        tools_requested = "\n".join([
            f"Tool {i+1}: {tool.tool_name}\n"
            f"  Version: {tool.version or 'latest'}\n"
            f"  Justification: {tool.justification}\n"
            f"  Urgency: {urgency}"
            for i, tool in enumerate(tools)
        ])
        
        # ====================================================================
        # STEP 4: Make LLM call (ONE call for entire batch)
        # ====================================================================
        
        prompt = self.prompt_template.format(
            role=employee_context.get("role", "Unknown"),
            department=employee_context.get("department", "Unknown"),
            security_clearance=employee_context.get("security_clearance", "standard"),
            location=employee_context.get("location", "Unknown"),
            relevant_policies=relevant_policies,
            access_rules=access_rules,
            tools_requested=tools_requested
        )
        
        logger.info(f"[{request_id}] Calling LLM for policy reasoning...")
        
        try:
            # Call LLM
            response = self.llm.invoke(prompt)
            
            # Extract content (different for real vs mock LLM)
            if isinstance(response, dict):
                content = response["content"]
            else:
                content = response.content
            
            # Parse structured output
            parser = PydanticOutputParser(pydantic_object=BatchDecisionOutput)
            
            # Clean the response (remove markdown if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            parsed_output = parser.parse(content)
            
            decisions = [decision.dict() for decision in parsed_output.decisions]
            
            logger.info(f"[{request_id}] ✓ LLM evaluation complete: {len(decisions)} decisions")
            
            return {
                "request_id": request_id,
                "decisions": decisions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[{request_id}] LLM evaluation failed: {str(e)}")
            
            # Fallback: reject all with error message
            fallback_decisions = [
                {
                    "tool_name": tool.tool_name,
                    "decision": "REJECTED",
                    "risk_level": "unknown",
                    "policy_reference": "ERROR",
                    "reason": f"Policy evaluation failed: {str(e)}. Please contact IT Security.",
                    "resolution_steps": "Contact IT Security to manually review this request."
                }
                for tool in tools
            ]
            
            return {
                "request_id": request_id,
                "decisions": fallback_decisions,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_access_rules(self, role: str, tools: List) -> str:
        """
        Retrieve access rules from pre-computed matrix.
        
        This is deterministic lookup - no LLM needed.
        """
        rules = []
        
        for tool in tools:
            tool_name_lower = tool.tool_name.lower()
            
            # Check if role has default access
            if role in ACCESS_MATRIX:
                role_rules = ACCESS_MATRIX[role]
                
                # Check for exact or partial match
                matching_tools = [
                    t for t in role_rules.get("allowed_tools", [])
                    if t.lower() in tool_name_lower or tool_name_lower in t.lower()
                ]
                
                if matching_tools:
                    rules.append(
                        f"{tool.tool_name}: Role '{role}' has default access (standard tools)"
                    )
                else:
                    rules.append(
                        f"{tool.tool_name}: Role '{role}' requires manager approval (not in standard set)"
                    )
            else:
                rules.append(
                    f"{tool.tool_name}: Role '{role}' not in access matrix, requires security review"
                )
        
        return "\n".join(rules) if rules else "No specific access rules found for this role."


# ============================================================================
# MOCK LLM (for testing without API keys)
# ============================================================================

class MockLLM:
    """Mock LLM for testing without API keys"""
    
    def invoke(self, prompt: str) -> Dict:
        """Return a mock structured response"""
        # Extract tool names from prompt
        import re
        tool_matches = re.findall(r"Tool \d+: (.+?)\n", prompt)
        
        # Generate mock decisions
        decisions = []
        for tool_name in tool_matches:
            # Simple heuristic for mock decisions
            risk_level = "medium"
            decision = "APPROVED"
            reason = f"Mock evaluation: {tool_name} approved for testing purposes."
            
            # Simulate some rejections
            if "admin" in tool_name.lower() or "root" in tool_name.lower():
                decision = "REJECTED"
                risk_level = "high"
                reason = f"Mock evaluation: {tool_name} requires elevated privileges."
            
            decisions.append({
                "tool_name": tool_name,
                "decision": decision,
                "risk_level": risk_level,
                "policy_reference": "MOCK-POL-001",
                "reason": reason,
                "resolution_steps": "Contact manager for approval" if decision == "REJECTED" else ""
            })
        
        # Return in expected format
        response_json = {
            "decisions": decisions
        }
        
        return {
            "content": json.dumps(response_json, indent=2)
        }


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Test the granter agent independently
    from collections import namedtuple
    
    agent = GranterAgent()
    
    # Mock tool request
    ToolRequest = namedtuple("ToolRequest", ["tool_name", "version", "justification"])
    
    test_tools = [
        ToolRequest(
            tool_name="Docker",
            version="latest",
            justification="Need to containerize microservices for the customer portal project"
        ),
        ToolRequest(
            tool_name="PostgreSQL Admin",
            version="14",
            justification="Database administration for production troubleshooting"
        )
    ]
    
    test_context = {
        "employee_id": "EMP001",
        "role": "Software Engineer",
        "department": "Engineering",
        "security_clearance": "standard",
        "location": "US-West"
    }
    
    # Evaluate
    result = agent.evaluate_batch_request(
        request_id="TEST-001",
        tools=test_tools,
        employee_context=test_context,
        urgency="normal"
    )
    
    print("\n" + "="*60)
    print("GRANTER AGENT TEST RESULTS")
    print("="*60)
    for decision in result["decisions"]:
        print(f"\nTool: {decision['tool_name']}")
        print(f"Decision: {decision['decision']}")
        print(f"Risk: {decision['risk_level']}")
        print(f"Reason: {decision['reason']}")
