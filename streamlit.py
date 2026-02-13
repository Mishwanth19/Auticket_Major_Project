"""
Streamlit Frontend for Agentic IT Service Approval System

A user-friendly interface for:
- Submitting tool access requests
- Viewing request status
- Exploring policies and access rules
- Monitoring system health

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict
import json
import time

# Configure page
st.set_page_config(
    page_title="IT Service Approval Portal",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
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
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .tool-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .metric-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
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

def get_decision_color(decision: str) -> str:
    """Get color for decision badge"""
    colors = {
        "APPROVED": "#28a745",
        "REJECTED": "#dc3545",
        "PENDING": "#ffc107"
    }
    return colors.get(decision, "#6c757d")

def get_risk_color(risk_level: str) -> str:
    """Get color for risk level badge"""
    colors = {
        "low": "#28a745",
        "medium": "#ffc107",
        "high": "#fd7e14",
        "critical": "#dc3545"
    }
    return colors.get(risk_level, "#6c757d")

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3064/3064197.png", width=100)
st.sidebar.title("IT Service Portal")
st.sidebar.markdown("---")

# Check API status
api_status = check_api_health()
if api_status:
    st.sidebar.success("🟢 System Online")
else:
    st.sidebar.error("🔴 System Offline")
    st.sidebar.warning("Please start the API server:\n```bash\npython orchestrator.py\n```")

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "📝 Submit Request", "📊 Track Request", "📚 View Policies", "👥 Access Rules", "⚙️ System Info"],
    key="navigation"
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Quick Guide:**
1. Submit a tool request
2. Wait for AI evaluation
3. Track your request status
4. Approved tools are auto-provisioned
""")

# ============================================================================
# PAGE: HOME
# ============================================================================

if page == "🏠 Home":
    st.markdown('<p class="main-header">🔐 IT Service Approval System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automated, AI-powered tool access management</p>', unsafe_allow_html=True)
    
    # Hero section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h2>⚡</h2>
            <h3>Fast Approvals</h3>
            <p>2-4 second AI evaluation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h2>🤖</h2>
            <h3>AI-Powered</h3>
            <p>Policy-based reasoning</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h2>🔒</h2>
            <h3>Secure</h3>
            <p>Compliance-ready decisions</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How it works
    st.header("📖 How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Submit Request")
        st.write("""
        - Select the tools you need
        - Provide business justification
        - Choose urgency level
        """)
        
        st.subheader("2️⃣ AI Evaluation")
        st.write("""
        - Granter Agent retrieves relevant policies
        - Assesses risk level
        - Makes approval decision
        - Provides detailed reasoning
        """)
    
    with col2:
        st.subheader("3️⃣ Automatic Execution")
        st.write("""
        - Approved tools are provisioned
        - Access is configured
        - You receive notification
        """)
        
        st.subheader("4️⃣ Track Status")
        st.write("""
        - Monitor request progress
        - View decision details
        - Check execution status
        """)
    
    st.markdown("---")
    
    # Quick stats
    st.header("📈 System Capabilities")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Policy Documents", "6", delta="Categories")
    
    with col2:
        st.metric("Role Types", "6", delta="Access Levels")
    
    with col3:
        st.metric("Batch Processing", "Yes", delta="Multiple Tools")
    
    with col4:
        st.metric("Avg Response", "2-4s", delta="Per Request")
    
    st.markdown("---")
    
    # Get started
    st.header("🚀 Get Started")
    st.info("👈 Use the sidebar to navigate to **Submit Request** and create your first tool access request!")

# ============================================================================
# PAGE: SUBMIT REQUEST
# ============================================================================

elif page == "📝 Submit Request":
    st.markdown('<p class="main-header">📝 Submit Tool Access Request</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Request access to development tools and software</p>', unsafe_allow_html=True)
    
    if not api_status:
        st.error("⚠️ API server is not running. Please start it with: `python orchestrator.py`")
        st.stop()
    
    # Employee information
    st.subheader("👤 Employee Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        employee_email = st.selectbox(
            "Select Your Email",
            [
                "john.doe@company.com",
                "alice.admin@company.com",
                "intern.user@company.com",
                "custom@company.com"
            ],
            help="Select your email or choose 'custom' to enter a different one"
        )
        
        if employee_email == "custom@company.com":
            employee_email = st.text_input("Enter Your Email")
    
    with col2:
        urgency = st.selectbox(
            "Request Urgency",
            ["normal", "high", "critical"],
            help="Urgency may influence approval for higher-risk tools"
        )
    
    st.markdown("---")
    
    # Tools section
    st.subheader("🛠️ Tools Requested")
    
    # Initialize session state for tools
    if 'tools' not in st.session_state:
        st.session_state.tools = [{"tool_name": "", "version": "", "justification": ""}]
    
    # Display each tool
    for idx, tool in enumerate(st.session_state.tools):
        with st.expander(f"Tool #{idx + 1}", expanded=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                tool_name = st.text_input(
                    "Tool Name",
                    value=tool["tool_name"],
                    key=f"tool_name_{idx}",
                    placeholder="e.g., Docker, AWS CLI, PostgreSQL"
                )
                st.session_state.tools[idx]["tool_name"] = tool_name
            
            with col2:
                version = st.text_input(
                    "Version (Optional)",
                    value=tool["version"],
                    key=f"version_{idx}",
                    placeholder="latest"
                )
                st.session_state.tools[idx]["version"] = version
            
            with col3:
                if len(st.session_state.tools) > 1:
                    if st.button("🗑️ Remove", key=f"remove_{idx}"):
                        st.session_state.tools.pop(idx)
                        st.rerun()
            
            justification = st.text_area(
                "Business Justification (min 20 characters)",
                value=tool["justification"],
                key=f"justification_{idx}",
                height=100,
                placeholder="Explain why you need this tool and how it relates to your work. Be specific about the project or task."
            )
            st.session_state.tools[idx]["justification"] = justification
            
            # Show character count
            char_count = len(justification)
            if char_count < 20:
                st.warning(f"⚠️ {20 - char_count} more characters needed")
            else:
                st.success(f"✓ {char_count} characters")
    
    # Add tool button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Add Another Tool"):
            if len(st.session_state.tools) < 10:
                st.session_state.tools.append({"tool_name": "", "version": "", "justification": ""})
                st.rerun()
            else:
                st.error("Maximum 10 tools per request")
    
    st.markdown("---")
    
    # Submit button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        submit_button = st.button("🚀 Submit Request", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🔄 Clear Form", use_container_width=True):
            st.session_state.tools = [{"tool_name": "", "version": "", "justification": ""}]
            st.rerun()
    
    # Handle submission
    if submit_button:
        # Validate inputs
        if not employee_email or employee_email == "custom@company.com":
            st.error("❌ Please enter a valid email address")
            st.stop()
        
        # Filter out empty tools
        valid_tools = [
            {
                "tool_name": tool["tool_name"],
                "version": tool["version"] if tool["version"] else None,
                "justification": tool["justification"]
            }
            for tool in st.session_state.tools
            if tool["tool_name"] and tool["justification"]
        ]
        
        if not valid_tools:
            st.error("❌ Please add at least one tool with name and justification")
            st.stop()
        
        # Check justification length
        for tool in valid_tools:
            if len(tool["justification"]) < 20:
                st.error(f"❌ Justification for '{tool['tool_name']}' is too short (min 20 characters)")
                st.stop()
        
        # Show progress
        with st.spinner("🤖 Submitting request to AI evaluation system..."):
            result = submit_request(employee_email, valid_tools, urgency)
        
        if result["success"]:
            response_data = result["data"]
            
            st.success("✅ Request submitted successfully!")
            
            # Display request ID prominently
            st.markdown(f"""
            <div class="success-box">
                <h3>📋 Request ID: {response_data['request_id']}</h3>
                <p>Save this ID to track your request status</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display decisions
            st.subheader("🎯 Evaluation Results")
            
            for decision in response_data["decisions"]:
                decision_color = get_decision_color(decision["decision"])
                risk_color = get_risk_color(decision["risk_level"])
                
                with st.expander(f"{decision['tool_name']} - {decision['decision']}", expanded=True):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="background-color: {decision_color}; color: white; padding: 0.5rem; border-radius: 0.3rem; text-align: center; margin-bottom: 0.5rem;">
                            <strong>{decision['decision']}</strong>
                        </div>
                        <div style="background-color: {risk_color}; color: white; padding: 0.5rem; border-radius: 0.3rem; text-align: center;">
                            Risk: {decision['risk_level'].upper()}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.write(f"**Reason:** {decision['reason']}")
                        st.write(f"**Policy:** {decision['policy_reference']}")
                        
                        if decision.get("resolution_steps"):
                            st.info(f"**Next Steps:** {decision['resolution_steps']}")
            
            # Overall status
            st.markdown("---")
            status_emoji = "✅" if response_data["overall_status"] == "FULLY_APPROVED" else "⚠️" if response_data["overall_status"] == "PARTIALLY_APPROVED" else "❌"
            st.markdown(f"### {status_emoji} Overall Status: {response_data['overall_status']}")
            
            # Track button
            if st.button("📊 Track This Request"):
                st.session_state.tracking_id = response_data['request_id']
                st.info("Navigate to '📊 Track Request' to see execution status")
            
            # Clear form
            st.session_state.tools = [{"tool_name": "", "version": "", "justification": ""}]
        
        else:
            st.error(f"❌ Request failed: {result['error']}")

# ============================================================================
# PAGE: TRACK REQUEST
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
        st.write("")  # Spacing
        st.write("")  # Spacing
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
                decision_color = get_decision_color(decision["decision"])
                
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
    
    Go to **Submit Request** to create a new request and get an ID.
    """)

# ============================================================================
# PAGE: VIEW POLICIES
# ============================================================================

elif page == "📚 View Policies":
    st.markdown('<p class="main-header">📚 Company Policies</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Understand the policies governing tool access</p>', unsafe_allow_html=True)
    
    # Policy categories
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
        },
        "POL-DEV-004": {
            "title": "Development Tools and Environment Policy",
            "category": "💻 Development",
            "summary": "Defines standard development tools and approval requirements for advanced tools."
        },
        "POL-NET-005": {
            "title": "Network and VPN Access Policy",
            "category": "🌐 Network",
            "summary": "Controls VPN access, network tools, and segmentation based on role."
        },
        "POL-BYOD-006": {
            "title": "Bring Your Own Device (BYOD) Policy",
            "category": "📱 Device Management",
            "summary": "Governs personal device usage for company resources with restrictions."
        }
    }
    
    # Category filter
    categories = list(set([p["category"] for p in policies.values()]))
    selected_category = st.selectbox("Filter by Category", ["All"] + categories)
    
    st.markdown("---")
    
    # Display policies
    for policy_id, policy_data in policies.items():
        if selected_category == "All" or policy_data["category"] == selected_category:
            with st.expander(f"{policy_data['category']} - {policy_data['title']}", expanded=False):
                st.write(f"**Policy ID:** {policy_id}")
                st.write(f"**Summary:** {policy_data['summary']}")
                
                st.markdown("---")
                
                st.markdown("**Key Points:**")
                if "Security" in policy_data["title"]:
                    st.markdown("""
                    - Risk-based approval: Low → High → Critical
                    - Role-based restrictions apply
                    - Prohibited software list maintained
                    - SOC 2, ISO 27001, GDPR compliance required
                    """)
                elif "Data" in policy_data["title"]:
                    st.markdown("""
                    - Production DB access restricted
                    - PII access requires special approval
                    - Admin tools: Senior+ only
                    - Monthly audit reviews
                    """)
                elif "Cloud" in policy_data["title"]:
                    st.markdown("""
                    - IAM-based access control
                    - Production access time-limited (max 7 days)
                    - MFA enforcement required
                    - Cost monitoring mandatory
                    """)
                elif "Development" in policy_data["title"]:
                    st.markdown("""
                    - Standard tools pre-approved
                    - Advanced tools need justification
                    - Open source compliance required
                    - No local admin rights by default
                    """)
                elif "Network" in policy_data["title"]:
                    st.markdown("""
                    - VPN access based on role
                    - Network segmentation enforced
                    - Remote access requires MDM
                    - All access logged and monitored
                    """)
                elif "BYOD" in policy_data["title"]:
                    st.markdown("""
                    - MDM enrollment required
                    - Restricted tool access
                    - No production system access
                    - Remote wipe capability
                    """)
                
                st.info(f"📄 Full Policy: https://intranet.company.com/policies/{policy_id}.pdf")

# ============================================================================
# PAGE: ACCESS RULES
# ============================================================================

elif page == "👥 Access Rules":
    st.markdown('<p class="main-header">👥 Role-Based Access Rules</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Understand what tools are available for each role</p>', unsafe_allow_html=True)
    
    # Role selector
    roles = {
        "Software Engineer": "💻",
        "DevOps Engineer": "⚙️",
        "Data Analyst": "📊",
        "Intern": "🎓",
        "Security Engineer": "🔒",
        "Manager": "👔"
    }
    
    selected_role = st.selectbox(
        "Select Role",
        list(roles.keys()),
        format_func=lambda x: f"{roles[x]} {x}"
    )
    
    st.markdown("---")
    
    # Access matrix data (simplified for display)
    access_matrix = {
        "Software Engineer": {
            "allowed": ["Git", "VS Code", "Docker", "PostgreSQL", "Python", "npm"],
            "requires_approval": ["AWS CLI", "Kubernetes", "Terraform"],
            "prohibited": ["Production DB admin", "Network scanning", "Security testing"],
            "risk_level": "medium"
        },
        "DevOps Engineer": {
            "allowed": ["Docker", "Kubernetes", "Terraform", "AWS CLI", "Jenkins", "Prometheus"],
            "requires_approval": ["Production DB access", "Root access", "Network config tools"],
            "prohibited": ["Offensive security tools", "Unauthorized scanners"],
            "risk_level": "medium"
        },
        "Data Analyst": {
            "allowed": ["Tableau", "Excel", "Python", "Jupyter", "SQL clients (read-only)"],
            "requires_approval": ["DB admin tools", "ETL tools", "Production DB"],
            "prohibited": ["Development tools", "Infrastructure tools", "Admin tools"],
            "risk_level": "low"
        },
        "Intern": {
            "allowed": ["Git", "VS Code", "Docker (local)", "PostgreSQL (local)"],
            "requires_approval": ["Cloud access", "Production access", "Advanced DB tools"],
            "prohibited": ["Admin tools", "Production systems", "Security tools", "Network tools"],
            "risk_level": "low"
        },
        "Security Engineer": {
            "allowed": ["Wireshark", "nmap", "Burp Suite", "OWASP ZAP", "SIEM tools"],
            "requires_approval": ["Production modifications", "Offensive security tools"],
            "prohibited": ["Unauthorized network access", "Unauthorized pen testing"],
            "risk_level": "high"
        },
        "Manager": {
            "allowed": ["Office suite", "Email", "JIRA", "Confluence", "BI dashboards"],
            "requires_approval": ["Technical tools", "Admin tools", "Dev environments"],
            "prohibited": ["Production system access", "Security tools"],
            "risk_level": "low"
        }
    }
    
    role_data = access_matrix[selected_role]
    
    # Display access information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: #28a745; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">
            <h3>✅ Auto-Approved</h3>
            <p style="font-size: 2rem; margin: 0;">{len(role_data['allowed'])}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: #ffc107; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">
            <h3>⚠️ Needs Approval</h3>
            <p style="font-size: 2rem; margin: 0;">{len(role_data['requires_approval'])}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background-color: #dc3545; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">
            <h3>🚫 Prohibited</h3>
            <p style="font-size: 2rem; margin: 0;">{len(role_data['prohibited'])}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed lists
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("✅ Auto-Approved Tools")
        for tool in role_data['allowed']:
            st.success(f"✓ {tool}")
    
    with col2:
        st.subheader("⚠️ Requires Approval")
        for tool in role_data['requires_approval']:
            st.warning(f"⚠ {tool}")
    
    with col3:
        st.subheader("🚫 Prohibited")
        for tool in role_data['prohibited']:
            st.error(f"✗ {tool}")
    
    st.markdown("---")
    
    # Risk level
    risk_color = get_risk_color(role_data['risk_level'])
    st.markdown(f"""
    <div style="background-color: {risk_color}; color: white; padding: 1rem; border-radius: 0.5rem;">
        <h3>Default Risk Level: {role_data['risk_level'].upper()}</h3>
        <p>This is the baseline risk assessment for this role. Individual tools may have different risk levels based on specific use cases.</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGE: SYSTEM INFO
# ============================================================================

elif page == "⚙️ System Info":
    st.markdown('<p class="main-header">⚙️ System Information</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Technical details about the approval system</p>', unsafe_allow_html=True)
    
    # Architecture overview
    st.header("🏗️ System Architecture")
    
    st.markdown("""
    This system uses an **agentic, non-conversational** AI architecture:
    
    ### Two Specialized Agents:
    
    **1. Requester Agent (Deterministic)**
    - Employee context retrieval
    - Request validation
    - Tool provisioning
    - User notifications
    - ⚡ No LLM - pure execution logic
    
    **2. Granter Agent (AI-Powered)**
    - RAG-based policy retrieval
    - Risk assessment
    - Approval decisions
    - 🤖 Uses LLM for reasoning
    
    ### Key Features:
    - ✅ **Token Efficient**: 97% reduction vs traditional systems
    - ✅ **Batch Processing**: One LLM call per request
    - ✅ **Policy-Based**: RAG retrieves relevant policies
    - ✅ **Async Execution**: Background provisioning
    """)
    
    st.markdown("---")
    
    # Technical stack
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Technology Stack")
        st.markdown("""
        **Backend:**
        - FastAPI (Orchestrator)
        - LangChain (RAG only)
        - FAISS (Vector store)
        - Groq/Llama 3.3 70B (LLM)
        
        **Frontend:**
        - Streamlit
        - Python Requests
        
        **Data:**
        - In-memory storage
        - Mock employee database
        - Pre-summarized policies
        """)
    
    with col2:
        st.subheader("📊 Performance Metrics")
        st.markdown("""
        **Response Times:**
        - Validation: < 100ms
        - Policy evaluation: 2-4s
        - Total request: 2-4s
        
        **Token Usage:**
        - Per request: ~2,500 tokens
        - RAG retrieval: Top-5 policies
        - Batch evaluation: 1 LLM call
        
        **Scalability:**
        - Stateless design
        - Horizontal scaling ready
        - Async background tasks
        """)
    
    st.markdown("---")
    
    # API endpoints
    st.header("🔌 API Endpoints")
    
    with st.expander("POST /submit-request", expanded=False):
        st.code("""
POST http://localhost:8000/submit-request

Request Body:
{
  "employee_email": "john.doe@company.com",
  "tools": [
    {
      "tool_name": "Docker",
      "version": "latest",
      "justification": "Need to containerize microservices..."
    }
  ],
  "urgency": "normal"
}

Response:
{
  "request_id": "REQ-20260124120000",
  "decisions": [...],
  "timestamp": "2026-01-24T12:00:00.000Z",
  "overall_status": "FULLY_APPROVED"
}
        """, language="json")
    
    with st.expander("GET /request-status/{request_id}", expanded=False):
        st.code("""
GET http://localhost:8000/request-status/REQ-20260124120000

Response:
{
  "request_id": "REQ-20260124120000",
  "status": "executed",
  "approved_count": 2,
  "rejected_count": 0,
  "executed_count": 2,
  "details": [...]
}
        """, language="json")
    
    with st.expander("GET /health", expanded=False):
        st.code("""
GET http://localhost:8000/health

Response:
{
  "status": "healthy",
  "service": "agentic-approval-orchestrator",
  "agents": {
    "requester": "active",
    "granter": "active"
  }
}
        """, language="json")
    
    st.markdown("---")
    
    # System status
    st.header("🔍 System Status")
    
    if api_status:
        try:
            health_response = requests.get(f"{API_BASE_URL}/health")
            health_data = health_response.json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success("✅ API Server")
                st.write(f"Status: {health_data['status']}")
            
            with col2:
                st.success("✅ Requester Agent")
                st.write(f"Status: {health_data['agents']['requester']}")
            
            with col3:
                st.success("✅ Granter Agent")
                st.write(f"Status: {health_data['agents']['granter']}")
            
        except Exception as e:
            st.error(f"Error fetching health: {str(e)}")
    else:
        st.error("🔴 API Server Offline")
        st.code("python orchestrator.py", language="bash")
    
    st.markdown("---")
    
    # Project info
    st.header("📚 Project Information")
    
    st.markdown("""
    **Project:** Agentic Enterprise IT Service Approval System
    
    **Purpose:** Final-year computer science project demonstrating production-quality agentic AI
    
    **Innovation:** 
    - Token-efficient agentic architecture (97% reduction)
    - Non-conversational goal-driven agents
    - Real-time policy reasoning with RAG
    - Enterprise-grade compliance and auditability
    
    **Key Differentiators:**
    - ONE LLM call per batch (not per tool)
    - Pre-summarized policies (token optimization)
    - Deterministic execution separate from AI reasoning
    - Async background provisioning
    
    **Documentation:** See ARCHITECTURE.md and README.md for detailed technical documentation
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🔐 Agentic IT Service Approval System | Version 1.0.0</p>
    <p>Powered by FastAPI, LangChain, and Groq LLM</p>
</div>
""", unsafe_allow_html=True)