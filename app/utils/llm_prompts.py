def get_vulnerability_analysis_prompt(cve_data: dict, org_context: dict) -> str:
    """
    Proprietary and secure prompt engineering for vulnerability analysis.
    This function should NEVER be exposed to the frontend.
    """
    cve_id = cve_data.get("cve_id", "N/A")
    description = cve_data.get("description", "No description available.")
    cvss_score = cve_data.get("cvss_score", "N/A")
    severity = cve_data.get("severity", "UNKNOWN")
    epss_score = cve_data.get("epss_score", "N/A")
    is_kev = cve_data.get("is_kev", False)
    ssvc_decision = cve_data.get("ssvc_decision", "N/A")
    universal_risk_score = cve_data.get("universal_risk_score", "N/A")
    industry = org_context.get("industry", "Unknown")
    tech_stack = ", ".join(org_context.get("tech_stack", [])) or "Not specified"
    risk_appetite = org_context.get("risk_appetite", "Medium")
    cloud_provider = org_context.get("cloud_provider", "Not specified")
    ip_ranges = org_context.get("ip_ranges", "Not specified")
    compliance = (
        ", ".join(org_context.get("compliance_requirements", [])) or "Not specified"
    )
    return f"""\n    You are a world-class cybersecurity analyst AI, tasked with providing a concise, actionable risk assessment for a specific vulnerability within a client's organizational context. Your output must be a single, valid JSON object and nothing else.\n\n    **Vulnerability Data:**\n    - **CVE ID:** {cve_id}\n    - **Description:** {description}\n\n    **Scoring Intelligence:**\n    - **CVSS v3.1 Score:** {cvss_score}/10 (Severity: {severity})\n    - **EPSS Score:** {epss_score} (Probability of exploitation in next 30 days)\n    - **In CISA KEV Catalog:** {("Yes" if is_kev else "No")}\n    - **SSVC Decision:** {ssvc_decision}\n    - **Universal Risk Score:** {universal_risk_score}/100\n\n    **Organizational Context:**\n    - **Industry:** {industry}\n    - **Relevant Tech Stack:** {tech_stack}\n    - **Primary Cloud Provider:** {cloud_provider}\n    - **Exposed IP Ranges:** {ip_ranges}\n    - **Compliance Requirements:** {compliance}\n    - **Risk Appetite:** {risk_appetite}\n\n    **Your Task:**\n    Based on all the information above, generate a structured risk analysis. The output MUST be a single, valid JSON object with the following keys:\n    - `executive_summary`: A 2-3 sentence overview for leadership, explaining the risk in business terms.\n    - `technical_impact`: A detailed assessment of the technical consequences if exploited. Mention if it relates to their cloud provider.\n    - `exploitation_likelihood`: An analysis of how likely this is to be exploited, considering attacker profiles, available tools, and exposed IP ranges.\n    - `recommended_actions`: A JSON array of 3-5 concrete, prioritized actions for the security team.\n    - `remediation_timeline`: A realistic, single-string timeframe for remediation (e.g., 'Within 72 hours', '2-4 weeks').\n    - `business_risk_context`: A paragraph explaining the potential business impact, including compliance, financial, and reputational risks. Specifically mention compliance risks if applicable.\n\n    **JSON Output Example:**\n    {{\n      "executive_summary": "...",\n      "technical_impact": "...",\n      "exploitation_likelihood": "...",\n      "recommended_actions": ["Action 1", "Action 2"],\n      "remediation_timeline": "...",\n      "business_risk_context": "..."\n    }}\n\n    Begin JSON output now:\n    """