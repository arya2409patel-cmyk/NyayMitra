"""Plain-Python tool implementations, shared by the local @tool wrappers (tools.py)
and the FastMCP server (mcp_server.py). All 'judgement' here is deterministic code."""
import core, store

NO_CONTRACTS = "No contracts have been uploaded yet. Ask the user to upload a PDF first."

def _resolve(contract_id: str):
    data = store.load()
    if not data:
        return None, NO_CONTRACTS
    cid = store.resolve_id(contract_id)
    if cid is None:
        return None, f"Contract '{contract_id}' was not found. Available contracts: {', '.join(data)}."
    return cid, None

def list_contracts() -> str:
    data = store.load()
    if not data:
        return NO_CONTRACTS
    return "\n".join(f"- {cid} (type: {v['type']}, {len(v['clauses'])} clauses)" for cid, v in data.items())

def retrieve_contract_text(query: str, contract_id: str = "") -> str:
    cid = ""
    if contract_id:
        cid, err = _resolve(contract_id)
        if err:
            return err
    elif not store.load():
        return NO_CONTRACTS
    from ingest import get_retriever
    docs = get_retriever(cid, k=3).invoke(query)
    if not docs:
        return "No relevant text was found in the contract for that question."
    out = [f"Top {len(docs)} matching clauses" + (f" in '{cid}':" if cid else ":")]
    for i, d in enumerate(docs, 1):
        m = d.metadata
        body = d.page_content.split("] ", 1)[-1]
        out.append(f"{i}) {m.get('contract_id')} - Clause {m.get('clause')} ({m.get('heading')}): {body[:600]}")
    return "\n".join(out)

def check_contract_compliance(contract_id: str, contract_type: str = "auto") -> str:
    cid, err = _resolve(contract_id)
    if err:
        return err
    rec = store.load()[cid]
    ctype = rec["type"] if contract_type in ("", "auto", None) else contract_type.lower()
    results = core.run_checklist(rec["clauses"], ctype)
    s = core.summarize(results)
    lines = [f"Contract: {cid} (type: {ctype})",
             f"Overall: {s['level']} ({s['flags']} red flags, {s['missing']} missing clauses, {s['high_severity']} high-severity)"]
    for x in results:
        if x["status"] == "FLAG":
            lines.append(f"FLAG [{x['severity']}] {x['name']} - Clause {x['clause']}: \"{x['evidence']}\" Why it matters: {x['why']}")
    for x in results:
        if x["status"] == "MISSING":
            lines.append(f"MISSING [{x['severity']}] {x['name']} - not found in the contract. Why it matters: {x['why']}")
    passed = [f"{x['name']} (Clause {x['clause']})" if x["clause"] else x["name"] for x in results if x["status"] == "PASS"]
    if passed:
        lines.append("PASS: " + "; ".join(passed))
    lines.append("Note: checks come from a rule list written by the NyayMitra team. Heuristic, not legal advice.")
    return "\n".join(lines)

def extract_key_terms(contract_id: str) -> str:
    cid, err = _resolve(contract_id)
    if err:
        return err
    t = core.extract_terms(store.load()[cid]["clauses"])
    lines = [f"Key terms in {cid} (extracted by pattern matching):"]
    lines.append("Amounts: " + ("; ".join(f"{m['value']} (Clause {m['clause']})" for m in t["money"]) or "none found"))
    lines.append("Periods / notice: " + ("; ".join(f"{p['value']} (Clause {p['clause']}: ...{p['context']}...)" for p in t["periods"]) or "none found"))
    lines.append("Dates: " + ("; ".join(f"{d['value']} (Clause {d['clause']})" for d in t["dates"]) or "none found"))
    return "\n".join(lines)
