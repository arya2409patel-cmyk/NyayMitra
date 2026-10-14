"""Step 6-7: custom tools, decorated with @tool. The docstrings are what the agent reads
to decide which tool to call, so each one says exactly what it does and returns."""
from langchain_core.tools import tool
import toolbox

@tool
def list_contracts() -> str:
    """List the contracts that have been uploaded, with their ids and types.
    Call this first if you do not know which contract_id to use."""
    return toolbox.list_contracts()

@tool
def retrieve_contract_text(query: str, contract_id: str = "") -> str:
    """Search the contract and return the 3 most relevant clauses with their clause numbers.
    Use for questions about WHAT a clause says or means (termination, deposit, payment,
    jurisdiction...). contract_id is the id of the selected contract. Answer only from the
    returned text and cite the clause number."""
    return toolbox.retrieve_contract_text(query, contract_id)

@tool
def check_contract_compliance(contract_id: str, contract_type: str = "auto") -> str:
    """Run the deterministic compliance checklist on the whole contract. Returns PASS, FLAG
    (risky term present) or MISSING (required clause absent) per rule, with clause numbers and
    an overall risk level. Use for questions about risks, red flags, missing clauses, fairness
    or 'is this safe to sign'. contract_type is rental, employment, freelance, nda or auto."""
    return toolbox.check_contract_compliance(contract_id, contract_type)

@tool
def extract_key_terms(contract_id: str) -> str:
    """Extract amounts (Rs), notice periods, durations and dates from the contract with their
    clause numbers. Use for questions such as 'how much', 'how long', 'what is the notice
    period' or 'when does it start'."""
    return toolbox.extract_key_terms(contract_id)

TOOLS = [list_contracts, retrieve_contract_text, check_contract_compliance, extract_key_terms]
