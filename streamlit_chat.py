"""
Streamlit Chat — Auticket v2
Adds: Login / Signup pages, session token in st.session_state,
      user profile pre-filled from MongoDB.
"""

import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json
import time
import re

from auth import login, logout, signup, get_current_user
from tool_downloads import get_download_links_for_approved

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="IT Service Approval Portal",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = "http://localhost:8000"

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    .user-message {
        background-color: #007bff; color: white;
        padding: 1rem; border-radius: 1rem;
        margin-bottom: 0.5rem; max-width: 80%;
        margin-left: auto; text-align: left;
    }
    .bot-message {
        background-color: #e9ecef; color: #333;
        padding: 1rem; border-radius: 1rem;
        margin-bottom: 0.5rem; max-width: 80%;
        margin-right: auto;
    }
    .system-message {
        background-color: #d4edda; color: #155724;
        padding: 1rem; border-radius: 0.5rem;
        margin: 1rem 0; border: 1px solid #c3e6cb;
    }
    .auth-card {
        background: white; padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 420px; margin: 4rem auto;
    }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1f77b4; }
    .sub-header  { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE BOOTSTRAP
# ============================================================================

def init_state():
    defaults = {
        "auth_token":       None,
        "current_user":     None,
        "auth_page":        "login",    # "login" | "signup"
        "current_page":     "💬 Chat Interface",
        "messages":         [],
        "current_request":  None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================================
# AUTH PAGES
# ============================================================================

def render_login():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("## 🔐 Sign In")
    st.markdown("Access the IT Service Approval Portal")
    st.markdown("---")

    email    = st.text_input("Work Email", placeholder="you@company.com", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign In", type="primary", use_container_width=True):
            if email and password:
                token, msg = login(email, password)
                if token:
                    st.session_state.auth_token   = token
                    st.session_state.current_user = get_current_user(token)
                    st.session_state.messages     = _welcome_messages(
                        st.session_state.current_user["name"]
                    )
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Please fill in all fields.")

    with col2:
        if st.button("Create Account", use_container_width=True):
            st.session_state.auth_page = "signup"
            st.rerun()

    st.markdown("---")
    st.caption("Demo accounts: john.doe@company.com / password123")
    st.markdown('</div>', unsafe_allow_html=True)


def render_signup():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("## 🆕 Create Account")
    st.markdown("---")

    name       = st.text_input("Full Name",    key="su_name")
    email      = st.text_input("Work Email",   key="su_email")
    password   = st.text_input("Password",     type="password", key="su_pw")
    confirm_pw = st.text_input("Confirm Password", type="password", key="su_pw2")

    role = st.selectbox("Your Role", [
        "Software Engineer", "DevOps Engineer", "Data Analyst",
        "Security Engineer", "Manager", "Intern",
    ], key="su_role")

    department = st.text_input("Department", value="Engineering", key="su_dept")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign Up", type="primary", use_container_width=True):
            if password != confirm_pw:
                st.error("Passwords do not match.")
            elif email and password and name:
                ok, msg = signup(email, password, name, role, department)
                if ok:
                    st.success(msg)
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Please fill in all fields.")

    with col2:
        if st.button("Back to Login", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def _welcome_messages(name: str) -> List[Dict]:
    return [{
        "role": "assistant",
        "content": (
            f"👋 Welcome back, **{name}**!\n\n"
            "I'm your IT Service Approval Assistant. I can help you request access to approved tools.\n\n"
            "**Available Tools:**\n"
            "• **Development:** Docker, Git, VS Code, Python, Node.js, Java\n"
            "• **Database:** PostgreSQL, MySQL, MongoDB, Redis\n" 
            "• **Cloud:** AWS CLI, Kubernetes, Terraform, Jenkins\n"
            "• **Data Science:** TensorFlow, Jupyter, Pandas, Tableau\n\n"
            "**🚨 STRICT JUSTIFICATION REQUIRED:**\n"
            "You MUST include:\n"
            "• Specific project/work purpose\n"
            "• Business context (why this tool)\n"
            "• Duration/timeline\n"
            "• Minimum 30 characters\n\n"
            "**Good Examples:**\n"
            "- *\"I need Docker for building microservices web application for Q2 customer portal - need 3 months\"*\n"
            "- *\"Can I get AWS CLI for cloud migration project to deploy EC2 instances - need 6 months\"*\n\n"
            "**❌ Will be REJECTED:**\n"
            "- *\"I need Docker\"* (too vague)\n"
            "- *\"For development\"* (no specifics)\n"
            "- *\"Need for work\"* (no context)\n\n"
            "**Important:** Only tools from the approved list above will be considered. "
            "All others will be automatically rejected.\n\n"
            "What would you like to request?"
        ),
    }]

# ============================================================================
# UTILITY
# ============================================================================

def check_api() -> bool:
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=2).status_code == 200
    except:
        return False


def submit_request(email: str, tools: List[Dict], urgency: str) -> Dict:
    try:
        r = requests.post(f"{API_BASE_URL}/submit-request",
                          json={"employee_email": email, "tools": tools, "urgency": urgency},
                          timeout=30)
        if r.status_code == 200:
            return {"success": True,  "data":  r.json()}
        return {"success": False, "error": r.json().get("detail", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_status(request_id: str) -> Dict:
    try:
        r = requests.get(f"{API_BASE_URL}/request-status/{request_id}")
        if r.status_code == 200:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.json().get("detail", "Not found")}
    except Exception as e:
        return {"success": False, "error": str(e)}


TOOL_PATTERNS = {
    # Development Tools
    "docker":     r"\bdocker\b",
    "git":        r"\bgit\b",
    "vs code":    r"\bvs\s*code\b",
    "intellij":   r"\bintellij\b",
    "pycharm":    r"\bpycharm\b",
    "python":     r"\bpython\b",
    "node":       r"\bnode(?:\.js)?|\bnpm\b",
    "java":       r"\bjava\b",
    "maven":      r"\bmaven\b",
    "postman":    r"\bpostman\b",
    "curl":       r"\bcurl\b",
    "wget":       r"\bwget\b",
    "jq":         r"\bjq\b",
    
    # Database Tools
    "postgresql": r"\bpostgres(?:ql)?\b",
    "mysql":      r"\bmysql\b",
    "mongodb":    r"\bmongodb\b",
    "redis":      r"\bredis\b",
    
    # Cloud & Infrastructure
    "aws cli":    r"\baws\s*cli\b",
    "kubernetes": r"\bkubernetes\b|\bk8s\b",
    "kubectl":    r"\bkubectl\b",
    "helm":       r"\bhelm\b",
    "terraform":  r"\bterraform\b",
    "ansible":    r"\bansible\b",
    "jenkins":    r"\bjenkins\b",
    "gitlab":     r"\bgitlab\b",
    "gcloud":     r"\bgcloud\b",
    "azure cli":  r"\bazure\s*cli\b",
    
    # Data Science & Analytics
    "tensorflow": r"\btensorflow\b",
    "pytorch":    r"\bpytorch\b",
    "jupyter":    r"\bjupyter\b",
    "pandas":     r"\bpandas\b",
    "numpy":      r"\bnumpy\b",
    "tableau":    r"\btableau\b",
    "power bi":   r"\bpower\s*bi\b",
    "excel":      r"\bexcel\b",
    "r":          r"\b\br\b(?!\w)",
    
    # Security Tools (will be rejected for most roles)
    "nmap":       r"\bnmap\b",
    "wireshark":  r"\bwireshark\b",
    "burp suite": r"\bburp\s+suite\b",
    "owasp zap":  r"\bowasp\s+zap\b",
    "metasploit": r"\bmetasploit\b",
    
    # Common Tools that will be rejected
    "utorrent":   r"\butorrent\b",
    "bitcoin":    r"\bbitcoin\b",
    "cryptocurrency": r"\bcryptocurrency\b",
}


def parse_request(message: str) -> Tuple[Optional[List[Dict]], str]:
    found = []
    low = message.lower()
    for name, pat in TOOL_PATTERNS.items():
        if re.search(pat, low):
            ver_match = re.search(rf"{re.escape(name)}\s*(?:version\s*)?([0-9]+(?:\.[0-9]+)*)", low)
            # Use the entire message as justification - no automatic fallbacks
            justification = message.strip()
            found.append({
                "tool_name":     name.title(),
                "version":       ver_match.group(1) if ver_match else None,
                "justification": justification,
            })
    if not found:
        # Provide helpful guidance with examples of approved tools
        return None, """I couldn't identify specific tools from your request. 

**Please use exact tool names from this approved list:**

**Development:** Docker, Git, VS Code, Python, Node.js, Java
**Database:** PostgreSQL, MySQL, MongoDB, Redis  
**Cloud:** AWS CLI, Kubernetes, Terraform, Jenkins
**Data Science:** TensorFlow, Jupyter, Pandas, Tableau

**Examples with proper justification:**
- "I need Docker and PostgreSQL for building a microservices web application for the Q2 customer portal project - need for 3 months"
- "Can I get AWS CLI for our cloud migration project to deploy EC2 instances and configure S3 buckets - need for 6 months"
- "I need TensorFlow for machine learning model development for our fraud detection system - need for 4 months"

**Important:** You MUST include specific project details, business need, and duration. 
Tools not in the approved list will be automatically rejected."""
    return found, ""


# ============================================================================
# CHAT PAGE
# ============================================================================

def chat_page(user: Dict, api_ok: bool):
    st.markdown('<p class="main-header">💬 IT Service Approval Chat</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Request tool access through natural conversation</p>',
                unsafe_allow_html=True)

    if not api_ok:
        st.error("⚠️ API server offline. Run: `python orchestrator.py`")
        return

    # Chat history
    for msg in st.session_state.messages:
        cls = {"user": "user-message", "assistant": "bot-message", "system": "system-message"}.get(
            msg["role"], "bot-message"
        )
        st.markdown(f'<div class="{cls}">{msg["content"]}</div>', unsafe_allow_html=True)

    # ── Download panel ────────────────────────────────────────────────────────
    req = st.session_state.current_request
    if req and any(d["decision"] == "APPROVED" for d in req.get("decisions", [])):
        download_items = get_download_links_for_approved(req["decisions"])

        with st.expander("📥 Download Approved Tools", expanded=True):
            st.markdown(
                f"**Request `{req['request_id']}`** — "
                f"{len(download_items)} tool(s) approved and ready to install."
            )
            st.markdown("---")

            for item in download_items:
                risk_badge = {"low": "🟢 Low", "medium": "🟡 Medium",
                              "high": "🟠 High", "critical": "🔴 Critical"}.get(
                    item.get("risk_level", ""), "⚪ Unknown"
                )

                col_info, col_links = st.columns([2, 3])

                with col_info:
                    st.markdown(f"### {item['display_name']}")
                    st.caption(item["description"])
                    st.markdown(f"**Category:** {item['category']}  \n"
                                f"**Risk:** {risk_badge}  \n"
                                f"**License:** {item.get('license', '—')}  \n"
                                f"**Policy:** `{item.get('policy_ref', '—')}`")
                    if item.get("docs"):
                        st.markdown(f"[📖 Documentation]({item['docs']})")

                with col_links:
                    st.markdown("**Installer links:**")
                    for platform, url in item["links"].items():
                        st.markdown(
                            f"<a href='{url}' target='_blank' style='"
                            "display:inline-block; margin:3px 4px 3px 0;"
                            "padding:6px 14px; background:#1f77b4; color:white;"
                            "border-radius:6px; text-decoration:none;"
                            "font-size:0.85rem; font-weight:600;'>"
                            f"⬇️ {platform}</a>",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")

        # Approval letter text download
        approved_list = [d for d in req["decisions"] if d["decision"] == "APPROVED"]
        letter = (
            f"IT SERVICE APPROVAL LETTER\n{'='*42}\n"
            f"Request ID : {req['request_id']}\n"
            f"Date       : {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Employee   : {user['email']}\n\n"
            "APPROVED TOOLS:\n"
            + "\n".join(f"  - {d['tool_name']} (risk: {d['risk_level']})" for d in approved_list)
            + "\n\nPOLICY REFERENCES:\n"
            + "\n".join(f"  - {d['policy_reference']}" for d in approved_list)
            + f"\n\nValid until: {datetime.now().replace(year=datetime.now().year+1):%Y-%m-%d}\n"
            "Generated by: Auticket Agentic IT Approval System\n"
        )
        st.download_button(
            "📄 Download Approval Letter (.txt)",
            data=letter,
            file_name=f"approval_{req['request_id']}.txt",
            mime="text/plain",
        )

    st.markdown("---")
    col_input, col_send, col_clear = st.columns([6, 1, 1])
    with col_input:
        user_msg = st.text_input("Message", placeholder="e.g., I need Docker for my project",
                                 label_visibility="collapsed", key="chat_input")
    with col_send:
        send = st.button("Send", type="primary", use_container_width=True)
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = _welcome_messages(user["name"])
            st.session_state.current_request = None
            st.rerun()

    if send and user_msg.strip():
        _handle_message(user_msg.strip(), user["email"])
        st.rerun()


def _handle_message(text: str, email: str):
    st.session_state.messages.append({"role": "user", "content": text})

    tools, err = parse_request(text)
    if err:
        st.session_state.messages.append({"role": "assistant", "content": err})
        return

    summary = "\n".join(
        f"• {t['tool_name']}" + (f" v{t['version']}" if t["version"] else "")
        for t in tools
    )
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Found these tools:\n\n{summary}\n\nSubmitting for evaluation…",
    })

    result = submit_request(email, tools, "normal")

    if result["success"]:
        data = result["data"]
        st.session_state.current_request = data

        body = f"✅ **Request ID:** `{data['request_id']}`\n\n"
        for d in data["decisions"]:
            emoji = "✅" if d["decision"] == "APPROVED" else "❌"
            risk  = {"low":"🟢","medium":"🟡","high":"🟠","critical":"🔴"}.get(d["risk_level"],"⚪")
            body += f"{emoji} **{d['tool_name']}** — {d['decision']} {risk}\n"
            body += f"> {d['reason']}\n"
            body += f"> Policy: `{d['policy_reference']}`\n\n"
        body += f"**Overall:** {data['overall_status']}"

        st.session_state.messages.append({"role": "system", "content": body})
    else:
        st.session_state.messages.append({
            "role": "system",
            "content": f"❌ Request failed: {result['error']}",
        })


# ============================================================================
# OTHER PAGES
# ============================================================================

def track_page(api_ok: bool):
    st.markdown('<p class="main-header">📊 Track Request</p>', unsafe_allow_html=True)
    if not api_ok:
        st.error("API offline.")
        return

    rid = st.text_input("Request ID", placeholder="REQ-20260101120000")
    if st.button("Track", type="primary") and rid:
        r = get_status(rid)
        if r["success"]:
            d = r["data"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Status",   d["status"].upper())
            c2.metric("Approved", d["approved_count"])
            c3.metric("Rejected", d["rejected_count"])
            c4.metric("Executed", d["executed_count"])
            for dec in d["details"]:
                color = "#28a745" if dec["decision"] == "APPROVED" else "#dc3545"
                with st.expander(f"{dec['tool_name']} — {dec['decision']}"):
                    st.write(f"**Reason:** {dec['reason']}")
                    st.write(f"**Policy:** {dec['policy_reference']}")
                    st.write(f"**Risk:** {dec['risk_level']}")
                    if dec.get("resolution_steps"):
                        st.warning(dec["resolution_steps"])
        else:
            st.error(r["error"])


def profile_page(user: Dict):
    st.markdown('<p class="main-header">👤 My Profile</p>', unsafe_allow_html=True)
    st.markdown(f"**Name:** {user['name']}")
    st.markdown(f"**Email:** {user['email']}")
    st.markdown(f"**Role:** {user['role']}")
    st.markdown(f"**Department:** {user.get('department','—')}")
    st.markdown(f"**Security Clearance:** {user.get('security_clearance','standard')}")
    st.markdown(f"**Location:** {user.get('location','—')}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Not logged in → show auth pages
    if not st.session_state.auth_token:
        if st.session_state.auth_page == "login":
            render_login()
        else:
            render_signup()
        return

    # Re-validate token on each render
    user = get_current_user(st.session_state.auth_token)
    if not user:
        st.session_state.auth_token  = None
        st.session_state.current_user = None
        st.warning("Session expired. Please log in again.")
        st.rerun()
        return

    st.session_state.current_user = user
    api_ok = check_api()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.title("💬 IT Service Portal")
    st.sidebar.markdown("---")
    st.sidebar.success("🟢 Online" if api_ok else "🔴 API Offline")
    st.sidebar.markdown(f"**{user['name']}**  \n*{user['role']}*")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")

    pages = ["💬 Chat Interface", "📊 Track Request", "👤 Profile"]
    for p in pages:
        active = st.session_state.current_page == p
        if st.sidebar.button(p, use_container_width=True,
                             type="primary" if active else "secondary"):
            st.session_state.current_page = p
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout(st.session_state.auth_token)
        for k in ["auth_token", "current_user", "messages", "current_request"]:
            st.session_state[k] = None
        st.rerun()

    # ── Page router ──────────────────────────────────────────────────────────
    page = st.session_state.current_page
    if   page == "💬 Chat Interface": chat_page(user, api_ok)
    elif page == "📊 Track Request":  track_page(api_ok)
    elif page == "👤 Profile":        profile_page(user)

    st.markdown("---")
    st.caption("Auticket v2.0 · Powered by FastAPI + MongoDB + LangChain")


if __name__ == "__main__":
    main()
