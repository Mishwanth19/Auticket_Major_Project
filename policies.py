"""
Policy Documents and Access Matrix

This module contains:
1. Pre-summarized policy documents (token-efficient)
2. Role-based access control matrix
3. Helper functions for policy retrieval

Architecture Decision: Policies are PRE-SUMMARIZED to minimize LLM tokens.
Full policies would be stored separately; LLM only sees summaries.
"""

from typing import Dict, List

# ============================================================================
# POLICY DOCUMENTS (Summarized for RAG)
# ============================================================================

POLICY_DOCUMENTS = {
    "POL-SEC-001": {
        "title": "Software Installation Security Policy",
        "category": "security",
        "full_text_url": "https://intranet.company.com/policies/POL-SEC-001.pdf",
        "summary": """
POL-SEC-001: Software Installation Security Policy

§1. General Requirements
All software installations must be approved through the IT Service Portal.
Unauthorized installations are prohibited and may result in disciplinary action.

§2. Risk-Based Approval
- Low Risk (productivity tools): Auto-approved for most roles
- Medium Risk (development tools): Manager approval required
- High Risk (admin tools, security tools): Security team approval required
- Critical Risk (kernel-level, network tools): CISO approval required

§3. Role-Based Restrictions
- Interns: Limited to approved productivity tools only
- Contractors: No admin or development tools without client approval
- Standard Employees: Tools aligned with job function
- Engineers: Development tools approved, admin tools require justification
- DevOps/SRE: Elevated privileges, admin tools case-by-case
- Security Team: Broad access with audit logging

§4. Prohibited Software
- Hacking tools (Metasploit, Mimikatz, SQLMap)
- Unlicensed software
- Software from unverified sources
- Cryptocurrency miners
- Peer-to-peer file sharing tools

§5. Compliance
All installations must comply with SOC 2, ISO 27001, and GDPR requirements.
Audit logs maintained for 2 years.
        """.strip()
    },
    
    "POL-DATA-002": {
        "title": "Data Access and Database Policy",
        "category": "data_governance",
        "full_text_url": "https://intranet.company.com/policies/POL-DATA-002.pdf",
        "summary": """
POL-DATA-002: Data Access and Database Policy

§1. Production Database Access
Production database access is restricted to:
- Database Administrators (DBA team)
- On-call engineers during incidents (read-only)
- Approved data analysts (read-only, non-PII tables)

§2. Database Tools
- Standard engineers: Development/staging databases only
- Senior engineers: Read-only production access with justification
- DBAs: Full production access with audit logging
- Data Scientists: Analytics databases, anonymized data only

§3. PII and Sensitive Data
Access to personally identifiable information (PII) requires:
- Privacy training completion
- Business justification
- Manager and Privacy Officer approval
- Annual recertification

§4. Tool Restrictions
- Admin tools (pgAdmin, MySQL Workbench): Senior+ only
- CLI tools (psql, mysql): Engineers with approved use cases
- ORM frameworks: Standard development practice
- Query tools: Based on role and data classification

§5. Audit Requirements
All database access logged and reviewed monthly.
Anomalous access patterns trigger automatic security review.
        """.strip()
    },
    
    "POL-CLOUD-003": {
        "title": "Cloud Access and Infrastructure Policy",
        "category": "cloud",
        "full_text_url": "https://intranet.company.com/policies/POL-CLOUD-003.pdf",
        "summary": """
POL-CLOUD-003: Cloud Access and Infrastructure Policy

§1. Cloud Provider Access
- AWS, GCP, Azure access requires role-based IAM
- Standard engineers: ReadOnly or limited dev environment access
- DevOps engineers: Elevated access to infrastructure resources
- Security team: Security audit and compliance access

§2. Tool Approval
- Cloud CLI tools (aws-cli, gcloud, az): Engineers and DevOps
- Infrastructure-as-Code (Terraform, CloudFormation): DevOps and SRE
- Container orchestration (kubectl, helm): DevOps and platform teams
- Serverless frameworks: Engineers with cloud project assignments

§3. Production Access
Production cloud resources require:
- Explicit business need documented
- Time-limited access grants (max 7 days)
- MFA enforcement
- Access review by infrastructure lead

§4. Cost Management
Tools that can incur costs (deployment tools, instance creation) require:
- Budget approval
- Cost monitoring alerts
- Monthly usage reviews

§5. Compliance
Cloud access must maintain compliance with:
- SOC 2 Type II
- PCI-DSS (for payment processing systems)
- HIPAA (for healthcare data systems)
        """.strip()
    },
    
    "POL-DEV-004": {
        "title": "Development Tools and Environment Policy",
        "category": "development",
        "full_text_url": "https://intranet.company.com/policies/POL-DEV-004.pdf",
        "summary": """
POL-DEV-004: Development Tools and Environment Policy

§1. Standard Development Tools
All engineers are pre-approved for:
- IDEs (VS Code, IntelliJ, PyCharm)
- Version control (Git, GitHub Desktop)
- Package managers (npm, pip, maven)
- Local databases (PostgreSQL, MySQL, Redis)
- Containerization (Docker, Docker Compose)

§2. Advanced Development Tools
Require justification and approval:
- Debuggers and profilers (for production debugging)
- Network analysis tools (Wireshark, tcpdump)
- Load testing tools (JMeter, Locust)
- Mobile development tools (Xcode, Android Studio)

§3. AI/ML Tools
Machine learning tools evaluated case-by-case:
- Standard libraries (scikit-learn, pandas): Auto-approved for engineers
- GPU compute tools (CUDA, TensorFlow): Approved for ML engineers
- Cloud ML services: Requires project approval and budget

§4. Open Source Compliance
All open source tools must:
- Be scanned for vulnerabilities
- Have compatible licenses (Apache, MIT, BSD)
- Be from reputable sources (verified publishers)

§5. Local Admin Rights
Engineers do not have local admin rights by default.
Admin access for tool installation via IT Service Portal.
        """.strip()
    },
    
    "POL-NET-005": {
        "title": "Network and VPN Access Policy",
        "category": "network",
        "full_text_url": "https://intranet.company.com/policies/POL-NET-005.pdf",
        "summary": """
POL-NET-005: Network and VPN Access Policy

§1. VPN Access
- Standard VPN: All remote employees (automatic approval)
- Engineering VPN: Engineers accessing dev environments
- Admin VPN: System administrators only
- Customer VPN: Customer-facing roles with client approval

§2. Network Tools
- Basic tools (ping, traceroute): All employees
- Advanced tools (nmap, netcat): Security team only
- Packet analyzers (Wireshark): Network engineers with justification
- VPN clients: Based on role and remote work needs

§3. Network Segmentation
Access to network segments based on principle of least privilege:
- Corporate network: All employees
- Development network: Engineers
- Production network: On-call rotation, DBAs, SREs
- DMZ: Security team and approved contractors

§4. Remote Access
Remote access requires:
- Company-issued device
- Full disk encryption
- Endpoint security software
- MFA enforcement

§5. Monitoring
All network access is logged and monitored for:
- Unauthorized access attempts
- Data exfiltration patterns
- Anomalous traffic
- Compliance violations
        """.strip()
    },
    
    "POL-BYOD-006": {
        "title": "Bring Your Own Device (BYOD) Policy",
        "category": "device_management",
        "full_text_url": "https://intranet.company.com/policies/POL-BYOD-006.pdf",
        "summary": """
POL-BYOD-006: Bring Your Own Device (BYOD) Policy

§1. BYOD Eligibility
Personal devices may access company resources if:
- Enrolled in MDM (Mobile Device Management)
- Meet minimum security requirements
- Employee signs BYOD agreement

§2. Tool Restrictions on BYOD
Personal devices have restricted tool access:
- No admin tools or development environments
- No access to production systems
- Limited to web-based applications and approved mobile apps
- No local data storage of company information

§3. Software on Personal Devices
Software installation on BYOD devices:
- Must use company app store or approved sources
- Cannot include unlicensed software
- Subject to security scanning
- Can be remotely wiped if device is lost/stolen

§4. Acceptable Use
BYOD devices may be used for:
- Email and calendar
- Chat and collaboration tools
- Document viewing and light editing
- Time tracking and expense reporting

§5. Prohibited Activities
BYOD devices cannot:
- Access source code repositories
- Connect to production databases
- Use admin or deployment tools
- Store unencrypted company data
        """.strip()
    }
}

# ============================================================================
# ROLE-BASED ACCESS CONTROL MATRIX
# ============================================================================

ACCESS_MATRIX = {
    "Software Engineer": {
        "allowed_tools": [
            "Git", "GitHub Desktop", "VS Code", "IntelliJ IDEA", "PyCharm",
            "Docker", "Docker Compose", "PostgreSQL", "MySQL", "Redis",
            "Node.js", "Python", "Java", "npm", "pip", "maven",
            "Postman", "curl", "wget", "jq"
        ],
        "requires_approval": [
            "AWS CLI", "gcloud", "Azure CLI",
            "Kubernetes", "kubectl", "helm",
            "Jenkins", "GitLab Runner",
            "Terraform", "Ansible"
        ],
        "prohibited": [
            "Production database admin tools",
            "Network scanning tools",
            "Security testing tools"
        ],
        "default_risk_level": "medium"
    },
    
    "DevOps Engineer": {
        "allowed_tools": [
            "Git", "Docker", "Kubernetes", "kubectl", "helm",
            "Terraform", "Ansible", "Jenkins", "GitLab Runner",
            "AWS CLI", "gcloud", "Azure CLI",
            "Prometheus", "Grafana", "ELK Stack",
            "bash", "python", "go"
        ],
        "requires_approval": [
            "Production database access",
            "Root access to production servers",
            "Network configuration tools"
        ],
        "prohibited": [
            "Offensive security tools",
            "Unauthorized network scanners"
        ],
        "default_risk_level": "medium"
    },
    
    "Data Analyst": {
        "allowed_tools": [
            "Tableau", "Power BI", "Excel", "R", "Python",
            "Jupyter Notebook", "pandas", "numpy",
            "SQL clients (read-only)",
            "Google Analytics", "Looker"
        ],
        "requires_approval": [
            "Database admin tools",
            "ETL tools with write access",
            "Production database access"
        ],
        "prohibited": [
            "Development tools",
            "Infrastructure tools",
            "Admin tools"
        ],
        "default_risk_level": "low"
    },
    
    "Intern": {
        "allowed_tools": [
            "Git", "GitHub Desktop", "VS Code",
            "Docker (local only)", "PostgreSQL (local only)",
            "Postman", "Browser developer tools"
        ],
        "requires_approval": [
            "Any cloud access (AWS, GCP, Azure)",
            "Any production access",
            "Database tools beyond local development"
        ],
        "prohibited": [
            "Admin tools",
            "Production systems",
            "Security tools",
            "Network tools"
        ],
        "default_risk_level": "low"
    },
    
    "Security Engineer": {
        "allowed_tools": [
            "All development tools",
            "Wireshark", "tcpdump", "nmap",
            "Burp Suite", "OWASP ZAP",
            "Metasploit (authorized testing only)",
            "Security scanning tools",
            "SIEM tools", "IDS/IPS tools"
        ],
        "requires_approval": [
            "Production system modifications",
            "Offensive security tools (with pen test authorization)"
        ],
        "prohibited": [
            "Unauthorized network access",
            "Unauthorized penetration testing"
        ],
        "default_risk_level": "high"
    },
    
    "Manager": {
        "allowed_tools": [
            "Office suite", "Email", "Calendar",
            "Project management tools", "JIRA", "Confluence",
            "Reporting tools", "BI dashboards"
        ],
        "requires_approval": [
            "Technical tools (based on background)",
            "Admin tools",
            "Development environments"
        ],
        "prohibited": [
            "Production system access (unless technical manager)",
            "Security tools (unless security manager)"
        ],
        "default_risk_level": "low"
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_policy_summary(policy_id: str) -> str:
    """Get summary for a specific policy"""
    if policy_id in POLICY_DOCUMENTS:
        return POLICY_DOCUMENTS[policy_id]["summary"]
    return "Policy not found"

def get_policies_by_category(category: str) -> List[Dict]:
    """Get all policies in a category"""
    return [
        {"id": pid, **pdata}
        for pid, pdata in POLICY_DOCUMENTS.items()
        if pdata["category"] == category
    ]

def get_role_access_info(role: str) -> Dict:
    """Get access information for a specific role"""
    if role in ACCESS_MATRIX:
        return ACCESS_MATRIX[role]
    return {
        "allowed_tools": [],
        "requires_approval": [],
        "prohibited": [],
        "default_risk_level": "high"  # Unknown roles get high risk
    }

def check_tool_access(role: str, tool_name: str) -> Dict:
    """
    Check if a role has default access to a tool.
    Returns: {"access": "allowed|requires_approval|prohibited", "reason": str}
    """
    role_info = get_role_access_info(role)
    
    tool_lower = tool_name.lower()
    
    # Check allowed tools
    for allowed in role_info["allowed_tools"]:
        if allowed.lower() in tool_lower or tool_lower in allowed.lower():
            return {
                "access": "allowed",
                "reason": f"Tool is in the standard set for {role}"
            }
    
    # Check prohibited tools
    for prohibited in role_info["prohibited"]:
        if prohibited.lower() in tool_lower or tool_lower in prohibited.lower():
            return {
                "access": "prohibited",
                "reason": f"Tool is explicitly prohibited for {role}"
            }
    
    # Check requires approval
    for requires in role_info["requires_approval"]:
        if requires.lower() in tool_lower or tool_lower in requires.lower():
            return {
                "access": "requires_approval",
                "reason": f"Tool requires manager/security approval for {role}"
            }
    
    # Default: requires approval
    return {
        "access": "requires_approval",
        "reason": f"Tool not in standard set for {role}, requires justification"
    }

# ============================================================================
# POLICY METADATA
# ============================================================================

def get_all_policy_metadata() -> List[Dict]:
    """Get metadata for all policies"""
    return [
        {
            "id": pid,
            "title": pdata["title"],
            "category": pdata["category"],
            "url": pdata["full_text_url"]
        }
        for pid, pdata in POLICY_DOCUMENTS.items()
    ]


if __name__ == "__main__":
    # Test policy retrieval
    print("="*60)
    print("POLICY SYSTEM TEST")
    print("="*60)
    
    print("\n1. Testing role access check:")
    result = check_tool_access("Software Engineer", "Docker")
    print(f"   Docker for Software Engineer: {result['access']} - {result['reason']}")
    
    result = check_tool_access("Intern", "AWS CLI")
    print(f"   AWS CLI for Intern: {result['access']} - {result['reason']}")
    
    print("\n2. Available policies:")
    for meta in get_all_policy_metadata():
        print(f"   - {meta['id']}: {meta['title']} ({meta['category']})")
    
    print("\n3. Sample policy summary:")
    summary = get_policy_summary("POL-SEC-001")
    print(f"   {summary[:200]}...")
