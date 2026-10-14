"""MCP BONUS: serves the same tools over the network with FastMCP.
Terminal 1:  python mcp_server.py        (listens on http://127.0.0.1:8001/mcp)
Terminal 2:  python app.py --mcp         (agent fetches the tools at runtime)"""
from mcp.server.fastmcp import FastMCP
import toolbox
from nyaya import toolbox as nt

mcp = FastMCP("nyaymitra-tools", host="127.0.0.1", port=8001)

@mcp.tool()
def list_contracts() -> str:
    """List the contracts that have been uploaded, with their ids and types.
    Call this first if you do not know which contract_id to use."""
    return toolbox.list_contracts()

@mcp.tool()
def retrieve_contract_text(query: str, contract_id: str = "") -> str:
    """Search the contract and return the 3 most relevant clauses with their clause numbers.
    Use for questions about WHAT a clause says or means. Answer only from the returned text
    and cite the clause number."""
    return toolbox.retrieve_contract_text(query, contract_id)

@mcp.tool()
def check_contract_compliance(contract_id: str, contract_type: str = "auto") -> str:
    """Run the deterministic compliance checklist on the whole contract. Returns PASS, FLAG
    (risky term present) or MISSING (required clause absent) per rule with clause numbers.
    Use for risks, red flags, missing clauses or 'is this safe to sign'."""
    return toolbox.check_contract_compliance(contract_id, contract_type)

@mcp.tool()
def extract_key_terms(contract_id: str) -> str:
    """Extract amounts (Rs), notice periods, durations and dates with clause numbers."""
    return toolbox.extract_key_terms(contract_id)

# ---- legal-aid tools (Indian law): triage, rights + steps, drafts, court-order explainer ----
@mcp.tool()
def classify_issue(text: str) -> str:
    """Identify the area of Indian law (rti, fir, consumer, domestic_violence, cyber, tenancy, wages) for the user's problem."""
    return nt.classify_issue(text)

@mcp.tool()
def explain_rights_and_steps(category: str, language: str = "en") -> str:
    """Rights, step-by-step filing procedure, authority and law for a category. language: en, hi or gu."""
    return nt.explain_rights_and_steps(category, language)

@mcp.tool()
def draft_document(doc_type: str, details_json: str = "{}") -> str:
    """Ready-to-file draft: rti, fir, consumer or demand_letter. details_json holds facts the user gave; missing ones stay [PLACEHOLDERS]."""
    return nt.draft_document(doc_type, details_json)

@mcp.tool()
def summarize_court_order(order_text: str) -> str:
    """Plain-language explanation of a court order: decision, directions, deadlines, hard words."""
    return nt.summarize_court_order(order_text)

@mcp.tool()
def legal_aid_contacts(language: str = "en") -> str:
    """Free legal aid and emergency helplines (15100, 112, 181, 1930, 1915) with eligibility."""
    return nt.legal_aid_contacts(language)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
