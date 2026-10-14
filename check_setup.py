"""Run this FIRST on your laptop:  python check_setup.py
It tests every moving part with your real Ollama model and tells you exactly what is broken."""
import asyncio, sys, tempfile, os, traceback

RESULTS = []
def step(name):
    def deco(fn):
        try:
            detail = fn()
            RESULTS.append((name, True, detail or ""))
        except Exception as e:
            RESULTS.append((name, False, f"{type(e).__name__}: {str(e)[:200]}"))
        print(("PASS " if RESULTS[-1][1] else "FAIL ") + name, "-", RESULTS[-1][2][:160])
        return fn
    return deco

@step("1. Python packages import")
def _():
    import langchain, langchain_core, langchain_ollama, langchain_chroma, langchain_text_splitters
    import langchain_community, pypdf, gradio, mcp, langchain_mcp_adapters
    return "all imported"

import config

@step(f"2. Ollama running and model '{config.MODEL_NAME}' pulled")
def _():
    import ollama
    ollama.show(config.MODEL_NAME)
    return "ok  (if this fails: start Ollama, then  ollama pull " + config.MODEL_NAME + ")"

@step("3. LLM answers a basic .invoke()")
def _():
    r = config.get_llm().invoke("Reply with the single word: OK")
    return r.content.replace("\n", " ")[:80]

@step("4. LLM can do TOOL CALLING (needed for the agent)")
def _():
    from langchain_core.tools import tool
    @tool
    def ping(text: str) -> str:
        """Echo the given text back."""
        return text
    r = config.get_llm().bind_tools([ping]).invoke("Call the ping tool with text='hello'.")
    if not r.tool_calls:
        raise RuntimeError("model did not call the tool. Try a bigger model: set MODEL_NAME=qwen3:4b in .env "
                           "(the app still works via its fallback router)")
    return f"called {r.tool_calls[0]['name']}"

@step("5. Embeddings load")
def _():
    return f"backend = {config.embeddings_name()}" + ("  (hf = BAAI/bge-small-en-v1.5)" if config.embeddings_name() == "hf" else "  (NOT hf: install langchain-huggingface + sentence-transformers and check internet)")

@step("6. Ingest sample contracts + retrieval")
def _():
    import ingest, toolbox
    config.STORE_DIR = type(config.STORE_DIR)(tempfile.mkdtemp(prefix="nyay_check_"))
    config.CHROMA_DIR = config.STORE_DIR / "chroma"; config.CLAUSES_JSON = config.STORE_DIR / "contracts.json"
    res = ingest.ingest_folder()
    out = toolbox.retrieve_contract_text("security deposit refund", "rental")
    assert "Clause 3" in out, out
    return f"{len(res)} contracts, retrieval ok"

@step("7. Deterministic checklist")
def _():
    import toolbox
    out = toolbox.check_contract_compliance("rental_agreement_sample")
    assert "HIGH RISK" in out
    return "rental sample flagged HIGH RISK as expected"

@step("8. End-to-end agent with the REAL model")
def _():
    import agent as A
    ag = A.build_agent()
    r = asyncio.run(A.aask(ag, "Is this contract safe to sign?", "rental_agreement_sample"))
    mode = "FALLBACK mode (model did not use tools)" if r["fallback"] else "agent used tools itself"
    return f"tools={r['tools']} | {mode}"

@step("9. MCP server module loads")
def _():
    import mcp_server
    return "FastMCP server defined (run: python mcp_server.py)"

print("\n==== SUMMARY ====")
bad = [n for n, ok, _ in RESULTS if not ok]
print("ALL GOOD - run: python app.py" if not bad else "Fix these first: " + "; ".join(bad))
sys.exit(1 if bad else 0)
