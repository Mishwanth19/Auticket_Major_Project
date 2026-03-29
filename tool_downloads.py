"""
tool_downloads.py — Official Download Links Registry

When the Granter approves a tool, this module resolves the
official installer/download page URL for it.

Strategy: Option 1 — Official download links (stub)
  - No file hosting required
  - Always points to the vendor's latest version
  - Works for any tool, no maintenance overhead
  - Suitable for enterprise intranet too (swap URLs for internal mirrors)
"""

from typing import Optional, Dict, List

# ============================================================================
# DOWNLOAD REGISTRY
# key: lowercase tool name (partial match supported)
# ============================================================================

DOWNLOAD_REGISTRY: Dict[str, Dict] = {

    # ── Version Control ───────────────────────────────────────────────────────
    "git": {
        "display_name": "Git",
        "description":  "Distributed version control system",
        "category":     "Version Control",
        "links": {
            "Windows": "https://git-scm.com/download/win",
            "macOS":   "https://git-scm.com/download/mac",
            "Linux":   "https://git-scm.com/download/linux",
        },
        "docs":    "https://git-scm.com/doc",
        "license": "GPLv2",
    },

    # ── IDEs / Editors ────────────────────────────────────────────────────────
    "vs code": {
        "display_name": "Visual Studio Code",
        "description":  "Lightweight but powerful source-code editor",
        "category":     "IDE / Editor",
        "links": {
            "Windows": "https://code.visualstudio.com/download#windows",
            "macOS":   "https://code.visualstudio.com/download#mac",
            "Linux":   "https://code.visualstudio.com/download#linux",
        },
        "docs":    "https://code.visualstudio.com/docs",
        "license": "MIT (binaries: proprietary)",
    },
    "intellij": {
        "display_name": "IntelliJ IDEA",
        "description":  "JVM-focused IDE by JetBrains",
        "category":     "IDE / Editor",
        "links": {
            "All platforms": "https://www.jetbrains.com/idea/download/",
        },
        "docs":    "https://www.jetbrains.com/idea/documentation/",
        "license": "Commercial / Community Edition (Apache 2.0)",
    },
    "pycharm": {
        "display_name": "PyCharm",
        "description":  "Python IDE by JetBrains",
        "category":     "IDE / Editor",
        "links": {
            "All platforms": "https://www.jetbrains.com/pycharm/download/",
        },
        "docs":    "https://www.jetbrains.com/pycharm/documentation/",
        "license": "Commercial / Community Edition (Apache 2.0)",
    },

    # ── Runtimes / Languages ─────────────────────────────────────────────────
    "python": {
        "display_name": "Python",
        "description":  "General-purpose programming language",
        "category":     "Runtime / Language",
        "links": {
            "Windows": "https://www.python.org/downloads/windows/",
            "macOS":   "https://www.python.org/downloads/macos/",
            "Linux":   "https://www.python.org/downloads/source/",
        },
        "docs":    "https://docs.python.org/3/",
        "license": "PSF License",
    },
    "node": {
        "display_name": "Node.js",
        "description":  "JavaScript runtime built on Chrome's V8 engine",
        "category":     "Runtime / Language",
        "links": {
            "All platforms": "https://nodejs.org/en/download",
        },
        "docs":    "https://nodejs.org/en/docs",
        "license": "MIT",
    },
    "java": {
        "display_name": "Java (OpenJDK)",
        "description":  "Open-source Java Development Kit",
        "category":     "Runtime / Language",
        "links": {
            "All platforms": "https://adoptium.net/temurin/releases/",
        },
        "docs":    "https://docs.oracle.com/en/java/",
        "license": "GPLv2 with Classpath Exception",
    },

    # ── Containers ────────────────────────────────────────────────────────────
    "docker": {
        "display_name": "Docker Desktop",
        "description":  "Container platform for building, sharing, and running apps",
        "category":     "Containerisation",
        "links": {
            "Windows": "https://docs.docker.com/desktop/install/windows-install/",
            "macOS":   "https://docs.docker.com/desktop/install/mac-install/",
            "Linux":   "https://docs.docker.com/desktop/install/linux-install/",
        },
        "docs":    "https://docs.docker.com/",
        "license": "Docker Subscription Service Agreement",
    },
    "kubernetes": {
        "display_name": "kubectl (Kubernetes CLI)",
        "description":  "CLI tool for running commands against Kubernetes clusters",
        "category":     "Containerisation",
        "links": {
            "All platforms": "https://kubernetes.io/docs/tasks/tools/",
        },
        "docs":    "https://kubernetes.io/docs/home/",
        "license": "Apache 2.0",
    },

    # ── Cloud CLIs ────────────────────────────────────────────────────────────
    "aws cli": {
        "display_name": "AWS CLI v2",
        "description":  "Command-line interface for Amazon Web Services",
        "category":     "Cloud CLI",
        "links": {
            "Windows": "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#windows",
            "macOS":   "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#macos",
            "Linux":   "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#linux",
        },
        "docs":    "https://docs.aws.amazon.com/cli/",
        "license": "Apache 2.0",
    },
    "terraform": {
        "display_name": "Terraform",
        "description":  "Infrastructure-as-Code by HashiCorp",
        "category":     "Infrastructure",
        "links": {
            "All platforms": "https://developer.hashicorp.com/terraform/install",
        },
        "docs":    "https://developer.hashicorp.com/terraform/docs",
        "license": "BSL 1.1",
    },
    "jenkins": {
        "display_name": "Jenkins",
        "description":  "Open-source automation / CI-CD server",
        "category":     "CI/CD",
        "links": {
            "All platforms": "https://www.jenkins.io/download/",
        },
        "docs":    "https://www.jenkins.io/doc/",
        "license": "MIT",
    },

    # ── Databases ─────────────────────────────────────────────────────────────
    "postgresql": {
        "display_name": "PostgreSQL",
        "description":  "Advanced open-source relational database",
        "category":     "Database",
        "links": {
            "Windows": "https://www.postgresql.org/download/windows/",
            "macOS":   "https://www.postgresql.org/download/macosx/",
            "Linux":   "https://www.postgresql.org/download/linux/",
        },
        "docs":    "https://www.postgresql.org/docs/",
        "license": "PostgreSQL License",
    },
    "mysql": {
        "display_name": "MySQL Community Server",
        "description":  "World's most popular open-source database",
        "category":     "Database",
        "links": {
            "All platforms": "https://dev.mysql.com/downloads/mysql/",
        },
        "docs":    "https://dev.mysql.com/doc/",
        "license": "GPLv2",
    },
    "mongodb": {
        "display_name": "MongoDB Community Edition",
        "description":  "Document-oriented NoSQL database",
        "category":     "Database",
        "links": {
            "All platforms": "https://www.mongodb.com/try/download/community",
        },
        "docs":    "https://www.mongodb.com/docs/",
        "license": "SSPL",
    },

    # ── Data Science ──────────────────────────────────────────────────────────
    "tensorflow": {
        "display_name": "TensorFlow",
        "description":  "End-to-end open-source ML platform",
        "category":     "Data Science / ML",
        "links": {
            "All platforms (pip)": "https://www.tensorflow.org/install",
        },
        "docs":    "https://www.tensorflow.org/api_docs",
        "license": "Apache 2.0",
    },
    "pytorch": {
        "display_name": "PyTorch",
        "description":  "Open-source machine learning framework",
        "category":     "Data Science / ML",
        "links": {
            "All platforms": "https://pytorch.org/get-started/locally/",
        },
        "docs":    "https://pytorch.org/docs/",
        "license": "BSD",
    },
    "jupyter": {
        "display_name": "JupyterLab",
        "description":  "Web-based interactive development environment",
        "category":     "Data Science / ML",
        "links": {
            "All platforms (pip)": "https://jupyter.org/install",
        },
        "docs":    "https://jupyterlab.readthedocs.io/",
        "license": "BSD",
    },
    "tableau": {
        "display_name": "Tableau Desktop",
        "description":  "Visual analytics and business intelligence platform",
        "category":     "Analytics / BI",
        "links": {
            "All platforms": "https://www.tableau.com/support/releases",
        },
        "docs":    "https://help.tableau.com/current/pro/desktop/en-us/",
        "license": "Commercial",
    },
    "excel": {
        "display_name": "Microsoft Excel",
        "description":  "Spreadsheet application — part of Microsoft 365",
        "category":     "Analytics / BI",
        "links": {
            "All platforms": "https://www.microsoft.com/en-us/microsoft-365/excel",
        },
        "docs":    "https://support.microsoft.com/en-us/excel",
        "license": "Commercial",
    },
}

# ============================================================================
# LOOKUP HELPERS
# ============================================================================

def get_download_info(tool_name: str) -> Optional[Dict]:
    """
    Fuzzy-match tool_name against the registry and return its download info.
    Returns None if no match found.
    """
    key = tool_name.lower().strip()

    # Exact match
    if key in DOWNLOAD_REGISTRY:
        return DOWNLOAD_REGISTRY[key]

    # Partial match (tool_name contains a registry key, or vice-versa)
    for reg_key, info in DOWNLOAD_REGISTRY.items():
        if reg_key in key or key in reg_key:
            return info

    return None


def get_download_links_for_approved(decisions: List[Dict]) -> List[Dict]:
    """
    Given a list of decision dicts from the granter, return enriched
    entries for every APPROVED tool that has a known download entry.

    Each returned dict:
      {
        "tool_name":    str,
        "display_name": str,
        "description":  str,
        "category":     str,
        "links":        {platform: url, ...},
        "docs":         str,
        "license":      str,
        "risk_level":   str,
        "policy_ref":   str,
      }
    """
    result = []
    for d in decisions:
        if d.get("decision") != "APPROVED":
            continue
        info = get_download_info(d["tool_name"])
        if info:
            result.append({
                **info,
                "tool_name":  d["tool_name"],
                "risk_level": d.get("risk_level", ""),
                "policy_ref": d.get("policy_reference", ""),
            })
        else:
            # Tool approved but not in registry → show a generic web search link
            result.append({
                "tool_name":    d["tool_name"],
                "display_name": d["tool_name"],
                "description":  "Approved tool — visit the official website to download.",
                "category":     "Other",
                "links": {
                    "Official site": (
                        f"https://www.google.com/search?q={d['tool_name'].replace(' ','+')}+official+download"
                    )
                },
                "docs":       "",
                "license":    "",
                "risk_level": d.get("risk_level", ""),
                "policy_ref": d.get("policy_reference", ""),
            })
    return result


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    tests = ["Docker", "PostgreSQL", "AWS CLI", "TensorFlow", "UnknownTool 3000"]
    for t in tests:
        info = get_download_info(t)
        if info:
            print(f"✓ {t}: {info['display_name']} — {list(info['links'].keys())}")
        else:
            print(f"✗ {t}: not in registry")
