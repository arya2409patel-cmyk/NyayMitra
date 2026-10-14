"""Gradio UI. Run:  python app.py            (tools imported directly)
                    python app.py --mcp      (bonus: tools fetched from the MCP server)"""
import sys
import gradio as gr
import config, store, ingest, agent as agent_mod

USE_MCP = "--mcp" in sys.argv
AGENT = None          # built lazily; tests can inject a scripted agent here

async def get_agent():
    global AGENT
    if AGENT is None:
        if USE_MCP:                      # bonus: tools are fetched from the MCP server at runtime
            from mcp_tools import fetch_tools_async
            AGENT = agent_mod.build_agent(tools=await fetch_tools_async())
        else:
            AGENT = agent_mod.build_agent()
    return AGENT

def choices():
    return list(store.load().keys())

def add_contract(file):
    if file is None:
        return "Choose a PDF first.", gr.update()
    try:
        info = ingest.ingest_pdf(file if isinstance(file, str) else file.name)
    except Exception as e:
        return f"Could not read that file: {e}", gr.update()
    return (f"Added **{info['contract_id']}** (type: {info['type']}, {info['clauses']} clauses).",
            gr.update(choices=choices(), value=info["contract_id"]))

async def respond(message, history, contract_id):
    history = history or []
    if not message.strip():
        return "", history
    out = await agent_mod.aask(await get_agent(), message, contract_id or "")
    tools = ", ".join(out["tools"]) or "none"
    mode = " (fallback mode)" if out["fallback"] else ""
    ev = ""
    if out.get("evidence") and not out["fallback"]:
        ev = "\n\n<details><summary>Evidence (raw tool output)</summary>\n\n```\n" + "\n\n".join(out["evidence"])[:3000] + "\n```\n</details>"
    reply = f"{out['answer']}{ev}\n\n<sub>Tools used: {tools}{mode}</sub>"
    history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
    return "", history

EXAMPLES = ["Is this contract safe to sign?", "What is the notice period?",
            "What does it say about the security deposit or payment?", "Which clauses are missing?"]

def build_ui():
    ingest.ensure_index()
    with gr.Blocks(title="NyayMitra - Contract Review") as demo:
        gr.Markdown("# NyayMitra\n**Contract review for people who cannot afford a lawyer.** "
                    "Upload a rental agreement, job offer, freelance contract or NDA, then ask questions.")
        gr.Markdown(f"> {config.DISCLAIMER}")
        gr.Markdown(f"<sub>{config.llm_status()} | embeddings: `{config.embeddings_name()}`</sub>")
        with gr.Row():
            with gr.Column(scale=1):
                up = gr.File(label="Upload contract (PDF)", file_types=[".pdf"], type="filepath")
                add = gr.Button("Add contract")
                status = gr.Markdown()
                contract = gr.Dropdown(label="Contract to review", choices=choices(),
                                       value=(choices() or [None])[0])
            with gr.Column(scale=2):
                chat = gr.Chatbot(height=460, label="NyayMitra")
                msg = gr.Textbox(label="Ask about your contract", placeholder="e.g. Is this contract safe to sign?")
                with gr.Row():
                    for ex in EXAMPLES:
                        gr.Button(ex, size="sm").click(lambda e=ex: e, None, msg)
                send = gr.Button("Ask", variant="primary")
        add.click(add_contract, up, [status, contract])
        for trigger in (send.click, msg.submit):
            trigger(respond, [msg, chat, contract], [msg, chat])
    return demo

if __name__ == "__main__":
    build_ui().launch(show_error=True)
