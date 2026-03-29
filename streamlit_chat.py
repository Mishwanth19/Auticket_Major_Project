"""
Streamlit Chat-based Frontend for Agentic IT Service Approval System

A conversational interface for:
- Submitting tool access requests via natural language
- Viewing request status
- Exploring policies and access rules
- Monitoring system health

Run with: streamlit run streamlit_chat.py
"""

import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import json
import time
import re

# Configure page
st.set_page_config(
    page_title="IT Service Approval Portal",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        background-color: #f9f9f9;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 0.5rem;
        max-width: 80%;
        margin-left: auto;
        text-align: left;
    }
    
    .bot-message {
        background-color: #e9ecef;
        color: #333;
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 0.5rem;
        max-width: 80%;
        margin-right: auto;
        text-align: left;
    }
    
    .system-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #c3e6cb;
    }
    
    .decision-approved {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    
    .decision-rejected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .stButton>button {
        width: 100%;
    }
    
    .download-btn {
        background-color: #28a745 !important;
        color: white !important;
    }
    
    .nav-button {
        margin: 2px 0 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .nav-button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Hide default radio button styling if any exists */
    .stRadio > div > div > label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def submit_request(employee_email: str, tools: List[Dict], urgency: str) -> Dict:
    """Submit a tool access request to the API"""
    payload = {
        "employee_email": employee_email,
        "tools": tools,
        "urgency": urgency
    }
    
    response = requests.post(
        f"{API_BASE_URL}/submit-request",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {"success": False, "error": response.json().get("detail", "Unknown error")}

def get_request_status(request_id: str) -> Dict:
    """Get the status of a submitted request"""
    response = requests.get(f"{API_BASE_URL}/request-status/{request_id}")
    
    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {"success": False, "error": response.json().get("detail", "Request not found")}

def parse_natural_language_request(message: str, employee_email: str) -> Tuple[List[Dict], str]:
    """
    Parse natural language message to extract tool requests.
    
    Expected format examples:
    "I need Docker and PostgreSQL for my web development project"
    "Can I get access to AWS CLI and Kubernetes? It's for our cloud migration"
    "I need TensorFlow with version 2.8 for machine learning model training"
    """
    
    # Common tool patterns
    tool_patterns = {
        'docker': r'\bdocker\b',
        'postgresql': r'\bpostgres(?:ql)?\b',
        'mysql': r'\bmysql\b',
        'mongodb': r'\bmongodb\b',
        'aws cli': r'\baws\s*cli\b',
        'kubernetes': r'\bkubernetes\b|\bk8s\b',
        'terraform': r'\bterraform\b',
        'jenkins': r'\bjenkins\b',
        'git': r'\bgit\b',
        'vs code': r'\bvs\s*code\b',
        'python': r'\bpython\b',
        'node': r'\bnode(?:\.js)?\b|\bnpm\b',
        'java': r'\bjava\b',
        'tensorflow': r'\btensorflow\b',
        'pytorch': r'\bpytorch\b',
        'tableau': r'\btableau\b',
        'excel': r'\bexcel\b',
        'jupyter': r'\bjupyter\b',
        'numpy': r'\bnumpy\b',
        'pandas': r'\bpandas\b'
    }
    
    # Extract tools from message
    extracted_tools = []
    message_lower = message.lower()
    
    for tool_name, pattern in tool_patterns.items():
        if re.search(pattern, message_lower):
            # Extract version if mentioned
            version_pattern = rf'{re.escape(tool_name)}\s*(?:version\s*)?([0-9]+(?:\.[0-9]+)*)'
            version_match = re.search(version_pattern, message_lower)
            version = version_match.group(1) if version_match else None
            
            # Extract justification (everything after the tool mentions)
            justification = message.strip()
            if not justification or len(justification) < 20:
                justification = f"Need access to {tool_name} for development work"
            
            extracted_tools.append({
                "tool_name": tool_name.title(),
                "version": version,
                "justification": justification
            })
    
    # If no tools found, ask for clarification
    if not extracted_tools:
        return None, "I couldn't identify any specific tools in your request. Could you please specify which tools you need access to?"
    
    return extracted_tools, ""

def generate_system_prompt() -> str:
    """Generate system prompt for the chat interface"""
    return """
You are an IT Service Approval Assistant. Help users submit tool access requests through natural conversation.

When users request tools, extract:
1. Tool names (e.g., Docker, PostgreSQL, AWS CLI)
2. Versions (if specified)
3. Business justification

Common tools you can recognize:
- Development: Git, VS Code, Python, Node.js, Java, Docker, Kubernetes
- Database: PostgreSQL, MySQL, MongoDB
- Cloud: AWS CLI, Terraform
- Data Science: TensorFlow, PyTorch, Jupyter, Pandas
- Analytics: Tableau, Excel

If the user's request is unclear, ask for specific tool names and justification.
Always be helpful and guide them through the process.

Once you have the tool information, format it as a structured request for processing.
"""

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Hello! I'm your IT Service Approval Assistant. I can help you request access to various tools and software.\n\nJust tell me what you need in natural language, for example:\n- \"I need Docker and PostgreSQL for my web development project\"\n- \"Can I get access to AWS CLI for our cloud deployment?\"\n- \"I need TensorFlow 2.8 for machine learning work\"\n\nWhat tools would you like to request access to?"}
        ]
    
    if 'current_request' not in st.session_state:
        st.session_state.current_request = None
    
    if 'employee_email' not in st.session_state:
        st.session_state.employee_email = None

# ============================================================================
# CHAT INTERFACE
# ============================================================================

def display_chat_messages():
    """Display all chat messages"""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "system":
            st.markdown(f'<div class="system-message">{message["content"]}</div>', unsafe_allow_html=True)

def handle_user_input(user_input: str):
    """Process user input and generate response"""
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # If employee email not set, ask for it first
    if not st.session_state.employee_email:
        if "@" in user_input and "." in user_input:
            st.session_state.employee_email = user_input
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"Thanks! I've noted your email as {user_input}. Now, what tools would you like to request access to?"
            })
        else:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Before we proceed, could you please provide your work email address?"
            })
        return
    
    # Parse the natural language request
    tools, error_message = parse_natural_language_request(user_input, st.session_state.employee_email)
    
    if error_message:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": error_message
        })
        return
    
    if tools:
        # Show parsed tools for confirmation
        tools_summary = "\n".join([
            f"• {tool['tool_name']}" + (f" (v{tool['version']})" if tool['version'] else "")
            for tool in tools
        ])
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"I've identified the following tools in your request:\n\n{tools_summary}\n\nI'll now submit this request for AI evaluation. Please wait..."
        })
        
        # Submit the request
        with st.spinner("🤖 Submitting request to AI evaluation system..."):
            result = submit_request(st.session_state.employee_email, tools, "normal")
        
        if result["success"]:
            response_data = result["data"]
            st.session_state.current_request = response_data
            
            # Format the response
            response_message = f"✅ **Request submitted successfully!**\n\n**Request ID:** {response_data['request_id']}\n\n**Evaluation Results:**\n\n"
            
            for decision in response_data["decisions"]:
                decision_emoji = "✅" if decision["decision"] == "APPROVED" else "❌"
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(decision["risk_level"], "⚪")
                
                response_message += f"{decision_emoji} **{decision['tool_name']}** - {decision['decision']} {risk_emoji} {decision['risk_level'].upper()}\n"
                response_message += f"Reason: {decision['reason']}\n"
                response_message += f"Policy: {decision['policy_reference']}\n\n"
            
            response_message += f"**Overall Status:** {response_data['overall_status']}"
            
            st.session_state.messages.append({
                "role": "system", 
                "content": response_message
            })
            
            # Add download button if any tools are approved
            if any(decision["decision"] == "APPROVED" for decision in response_data["decisions"]):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "🎉 Some tools were approved! You can download your approval letter below."
                })
            
        else:
            st.session_state.messages.append({
                "role": "system", 
                "content": f"❌ **Request failed:** {result['error']}"
            })

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application function"""
    initialize_session_state()
    
    # Sidebar
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3064/3064197.png", width=100)
    st.sidebar.title("💬 IT Service Portal")
    st.sidebar.markdown("---")
    
    # Check API status
    api_status = check_api_health()
    if api_status:
        st.sidebar.success("🟢 System Online")
    else:
        st.sidebar.error("🔴 System Offline")
        st.sidebar.warning("Please start the API server:\n```bash\npython orchestrator.py\n```")
    
    st.sidebar.markdown("---")
    
    # Navigation - Modern Buttons
    st.sidebar.markdown("### Navigation")
    
    # Initialize page in session state if not exists
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "💬 Chat Interface"
    
    # Navigation buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("💬 Chat", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "💬 Chat Interface" else "secondary"):
            st.session_state.current_page = "💬 Chat Interface"
            st.rerun()
    
    with col2:
        if st.button("📊 Track", use_container_width=True,
                    type="primary" if st.session_state.current_page == "📊 Track Request" else "secondary"):
            st.session_state.current_page = "📊 Track Request"
            st.rerun()
    
    col3, col4 = st.sidebar.columns(2)
    
    with col3:
        if st.button("📚 Policies", use_container_width=True,
                    type="primary" if st.session_state.current_page == "📚 View Policies" else "secondary"):
            st.session_state.current_page = "📚 View Policies"
            st.rerun()
    
    with col4:
        if st.button("👥 Access", use_container_width=True,
                    type="primary" if st.session_state.current_page == "👥 Access Rules" else "secondary"):
            st.session_state.current_page = "👥 Access Rules"
            st.rerun()
    
    # Center the System Info button
    if st.button("⚙️ System Info", use_container_width=True,
                type="primary" if st.session_state.current_page == "⚙️ System Info" else "secondary"):
        st.session_state.current_page = "⚙️ System Info"
        st.rerun()
    
    page = st.session_state.current_page
    
    st.sidebar.markdown("---")
    
    # Show current user if logged in
    if st.session_state.employee_email:
        st.sidebar.info(f"**Current User:**\n{st.session_state.employee_email}")
    else:
        st.sidebar.info("**Please provide your email**\nin the chat to get started")
    
    # ============================================================================
    # PAGE: CHAT INTERFACE
    # ============================================================================
    
    if page == "💬 Chat Interface":
        st.markdown('<p class="main-header">💬 IT Service Approval Chat</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Request tool access through natural conversation</p>', unsafe_allow_html=True)
        
        if not api_status:
            st.error("⚠️ API server is not running. Please start it with: `python orchestrator.py`")
            st.stop()
        
        # Chat container
        chat_container = st.container()
        with chat_container:
            display_chat_messages()
        
        # Download button (only show if there's an approved request)
        if st.session_state.current_request and any(
            decision["decision"] == "APPROVED" 
            for decision in st.session_state.current_request.get("decisions", [])
        ):
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📥 Download Approval Letter", type="primary", use_container_width=True, key="download_btn"):
                    # Generate approval letter content
                    approved_tools = [
                        decision for decision in st.session_state.current_request["decisions"]
                        if decision["decision"] == "APPROVED"
                    ]
                    
                    approval_content = f"""
IT SERVICE APPROVAL LETTER
==========================

Request ID: {st.session_state.current_request['request_id']}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Employee: {st.session_state.employee_email}

APPROVED TOOLS:
{chr(10).join([f"- {tool['tool_name']} (Risk: {tool['risk_level']})" for tool in approved_tools])}

This approval is granted based on the following policies:
{chr(10).join([f"- {tool['policy_reference']}" for tool in approved_tools])}

Generated by: Agentic IT Approval System
Valid until: {datetime.now().replace(year=datetime.now().year + 1).strftime('%Y-%m-%d')}
"""
                    
                    st.download_button(
                        label="📄 Download PDF/Text",
                        data=approval_content,
                        file_name=f"approval_{st.session_state.current_request['request_id']}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        
        # User input
        st.markdown("---")
        user_input = st.text_input(
            "Type your message here...",
            placeholder="e.g., I need Docker and PostgreSQL for my web development project",
            key="user_input"
        )
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button("📤 Send", type="primary", use_container_width=True):
                if user_input.strip():
                    handle_user_input(user_input)
                    st.rerun()
        
        with col2:
            if st.button("🔄 Clear", use_container_width=True):
                st.session_state.messages = [
                    {"role": "assistant", "content": "Chat cleared! How can I help you today?"}
                ]
                st.session_state.current_request = None
                st.rerun()
    
    # ============================================================================
    # OTHER PAGES (reuse from original)
    # ============================================================================
    
    elif page == "📊 Track Request":
        st.markdown('<p class="main-header">📊 Track Request Status</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Monitor your tool access request progress</p>', unsafe_allow_html=True)
        
        if not api_status:
            st.error("⚠️ API server is not running.")
            st.stop()
        
        # Request ID input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            request_id = st.text_input(
                "Enter Request ID",
                value=st.session_state.get("tracking_id", ""),
                placeholder="REQ-20260124120000"
            )
        
        with col2:
            st.write("")
            st.write("")
            track_button = st.button("🔍 Track", type="primary", use_container_width=True)
        
        if track_button and request_id:
            with st.spinner("🔍 Fetching request status..."):
                result = get_request_status(request_id)
            
            if result["success"]:
                status_data = result["data"]
                
                # Status header
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Status", status_data["status"].upper())
                
                with col2:
                    st.metric("Approved", status_data["approved_count"], delta="✓")
                
                with col3:
                    st.metric("Rejected", status_data["rejected_count"], delta="✗" if status_data["rejected_count"] > 0 else None)
                
                with col4:
                    st.metric("Executed", status_data["executed_count"], delta=f"/{status_data['approved_count']}")
                
                st.markdown("---")
                
                # Detailed decisions
                st.subheader("📋 Decision Details")
                
                for idx, decision in enumerate(status_data["details"]):
                    decision_color = "#28a745" if decision["decision"] == "APPROVED" else "#dc3545"
                    
                    with st.expander(f"{idx + 1}. {decision['tool_name']} - {decision['decision']}", expanded=True):
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            st.markdown(f"""
                            <div style="background-color: {decision_color}; color: white; padding: 0.5rem; border-radius: 0.3rem; text-align: center;">
                                <strong>{decision['decision']}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if decision.get("executed"):
                                st.success("✅ Executed")
                            elif decision["decision"] == "APPROVED":
                                st.info("⏳ Pending Execution")
                        
                        with col2:
                            st.write(f"**Reason:** {decision['reason']}")
                            st.write(f"**Policy Reference:** {decision['policy_reference']}")
                            st.write(f"**Risk Level:** {decision['risk_level']}")
                            
                            if decision.get("resolution_steps"):
                                st.warning(f"**Resolution Steps:** {decision['resolution_steps']}")
                            
                            if decision.get("execution_timestamp"):
                                st.caption(f"Executed at: {decision['execution_timestamp']}")
                
                # Auto-refresh option
                st.markdown("---")
                if st.checkbox("🔄 Auto-refresh (every 5 seconds)"):
                    time.sleep(5)
                    st.rerun()
            
            else:
                st.error(f"❌ {result['error']}")
        
        elif not request_id and track_button:
            st.warning("⚠️ Please enter a Request ID")
        
        # Example requests
        st.markdown("---")
        st.info("""
        **💡 Tip:** Request IDs are generated when you submit a request. 
        Format: `REQ-YYYYMMDDHHMMSS`
        
        Go to **Chat Interface** to create a new request and get an ID.
        """)
    
    # Add other pages from original implementation...
    elif page == "📚 View Policies":
        st.markdown('<p class="main-header">📚 Company Policies</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Understand the policies governing tool access</p>', unsafe_allow_html=True)
        
        # Policy categories (simplified for chat version)
        policies = {
            "POL-SEC-001": {
                "title": "Software Installation Security Policy",
                "category": "🔒 Security",
                "summary": "Governs software installation approval process, risk levels, and role-based restrictions."
            },
            "POL-DATA-002": {
                "title": "Data Access and Database Policy", 
                "category": "💾 Data Governance",
                "summary": "Controls access to databases, PII, and sensitive data based on role and justification."
            },
            "POL-CLOUD-003": {
                "title": "Cloud Access and Infrastructure Policy",
                "category": "☁️ Cloud", 
                "summary": "Manages access to AWS, GCP, Azure and infrastructure-as-code tools."
            }
        }
        
        for policy_id, policy_data in policies.items():
            with st.expander(f"{policy_data['category']} - {policy_data['title']}", expanded=False):
                st.write(f"**Policy ID:** {policy_id}")
                st.write(f"**Summary:** {policy_data['summary']}")
                st.info(f"📄 Full Policy: https://intranet.company.com/policies/{policy_id}.pdf")
    
    elif page == "👥 Access Rules":
        st.markdown('<p class="main-header">👥 Role-Based Access Rules</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Understand what tools are available for each role</p>', unsafe_allow_html=True)
        
        roles = {
            "Software Engineer": "💻",
            "DevOps Engineer": "⚙️", 
            "Data Analyst": "📊",
            "Intern": "🎓"
        }
        
        selected_role = st.selectbox(
            "Select Role",
            list(roles.keys()),
            format_func=lambda x: f"{roles[x]} {x}"
        )
        
        st.info(f"📋 Access rules for {selected_role} would be displayed here in a full implementation.")
    
    elif page == "⚙️ System Info":
        st.markdown('<p class="main-header">⚙️ System Information</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Technical details about the approval system</p>', unsafe_allow_html=True)
        
        st.markdown("""
        **Chat-Based IT Approval System**
        
        This version provides a conversational interface for requesting tool access.
        Users can simply type their requests in natural language, and the system will:
        
        1. Parse the request to extract tool names and justifications
        2. Submit the structured request to the AI evaluation system
        3. Provide immediate feedback with approval decisions
        4. Offer download functionality for approved requests
        
        **Key Features:**
        - 🗣️ Natural language input
        - 🤖 AI-powered parsing and evaluation
        - 📥 Download approval letters for approved tools
        - 💬 Conversational user experience
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>💬 Agentic IT Service Approval System | Chat Interface v1.0.0</p>
        <p>Powered by FastAPI, LangChain, and AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
