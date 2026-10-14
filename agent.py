"""Step 8: the agent. create_agent + a system prompt that sequences retrieval and tools.
Includes a safety net: if the small local model answers WITHOUT calling any tool, a
deterministic router runs the right tool(s) so the demo never returns an ungrounded answer."""
import re
import config, store, toolbox

SYSTEM_PROMPT = """You are NyayMitra, a contract review assistant for people who cannot afford a lawyer.
You help the user understand ONE contract they uploaded. You are NOT a lawyer and you never give legal advice.

The user message starts with "[Selected contract: <id>]". Use that id in every tool call.

Choose tools like this:
1. Question about what a clause says or means (termination, deposit, payment, jurisdiction, ...):
   call retrieve_contract_text, then answer ONLY from the returned text and cite "Clause N".
2. Question about risks, red flags, missing clauses, fairness, compliance or "is it safe to sign":
   call check_contract_compliance and report FLAG / MISSING / PASS exactly as returned, with clause numbers.
3. Question about amounts, notice periods, durations or dates: call extract_key_terms.
4. If a question needs more than one of these, call all the tools you need before answering.
5. If a tool says nothing was found or the contract does not exist, say so plainly.
   NEVER invent clauses, amounts, laws or section numbers. If it is not in a tool result, say you could not find it.
6. Keep answers short and in simple English. End with: "This is not legal advice. Please have a licensed lawyer review before you sign."
"""

THINK_RE = re.compile(r"<think>.*?</think>", re.S)

def build_agent(llm=None, tools=None):
    from langchain.agents import create_agent
    from tools import TOOLS
    return create_agent(llm or config.get_llm(), tools or TOOLS, system_prompt=SYSTEM_PROMPT)

# ------------------------------------------------------------------ helpers
def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content or "")

def clean(text: str) -> str:
    return THINK_RE.sub("", _text(text)).strip()

def with_disclaimer(answer: str) -> str:
    if "not legal advice" in answer.lower():
        return answer
    return f"{answer}\n\n_{config.DISCLAIMER}_"

def trace_from(messages) -> list:
    """Names of tools the agent actually called, in order."""
    names = []
    for m in messages:
        for tc in (getattr(m, "tool_calls", None) or []):
            names.append(tc["name"] if isinstance(tc, dict) else tc.name)
    return names

RISK = ("risk", "red flag", "safe", "fair", "unfair", "missing", "compliance", "check", "problem", "trap", "danger", "sign")
TERMS = ("how much", "how long", "amount", "notice period", "period", "duration", "date", "when", "rent", "salary", "fee", "deposit amount", "cost")

def route_fallback(question: str, cid: str):
    """Deterministic router used only when the model made no tool call."""
    q = question.lower()
    parts, used = [], []
    if any(k in q for k in RISK):
        parts.append(toolbox.check_contract_compliance(cid)); used.append("check_contract_compliance")
    if any(k in q for k in TERMS):
        parts.append(toolbox.extract_key_terms(cid)); used.append("extract_key_terms")
    if not parts or not any(k in q for k in RISK):
        parts.append(toolbox.retrieve_contract_text(question, cid)); used.append("retrieve_contract_text")
    return "\n\n".join(parts), used

def pick_contract(cid: str):
    data = store.load()
    if cid and store.resolve_id(cid):
        return store.resolve_id(cid)
    return next(iter(data)) if len(data) == 1 else None

# ------------------------------------------------------------------ main entry
async def aask(agent, question: str, contract_id: str = "") -> dict:
    cid = pick_contract(contract_id)
    if not store.load():
        return {"answer": with_disclaimer(toolbox.NO_CONTRACTS), "tools": [], "fallback": False, "evidence": []}
    if cid is None:
        return {"answer": with_disclaimer("Please select which contract you are asking about.\n\n" + toolbox.list_contracts()), "tools": [], "fallback": False, "evidence": []}
    msg = f"[Selected contract: {cid}]\n{question}"
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": msg}]})
        messages = result["messages"]
        tools_used = trace_from(messages)
        evidence = [_text(m.content) for m in messages if m.__class__.__name__ == "ToolMessage"]
        answer = clean(messages[-1].content)
    except Exception as e:                                   # model/tool crash -> graceful
        messages, tools_used, answer, evidence = [], [], "", []
        err = f"{type(e).__name__}: {e}"
        print("agent error:", err)
    if not tools_used or not answer:
        text, used = route_fallback(question, cid)
        return {"answer": with_disclaimer(f"**Checked directly (fallback mode):**\n\n{text}"), "tools": used, "fallback": True, "evidence": [text]}
    return {"answer": with_disclaimer(answer), "tools": tools_used, "fallback": False, "evidence": evidence}
