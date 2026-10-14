"""NyayMitra legal-aid app (voice-first, Hindi / Gujarati / English).
Run:  python app_nyaya.py            (add --mcp to fetch the contract tools from the MCP server)
Tabs: Tell your problem (voice or text) | Draft a document | Understand a court order | Contract review"""
import sys, tempfile, os
import gradio as gr
from nyaya import kb, advice, drafts, orders, voice, agent as nagent

AGENT = None
AGENT_TRIED = False
LANG_CHOICES = [("Auto-detect / अपने आप / આપોઆપ", ""), ("English", "en"), ("हिन्दी", "hi"), ("ગુજરાતી", "gu")]
MAXF = 12

async def get_agent():
    """Build the LLM agent once. If Ollama / langchain is missing the app still works (deterministic mode)."""
    global AGENT, AGENT_TRIED
    if AGENT is None and not AGENT_TRIED:
        AGENT_TRIED = True
        try:
            AGENT = nagent.build_agent()
        except Exception as e:
            print("LLM agent unavailable, using deterministic mode:", type(e).__name__, e)
    return AGENT

def status_line():
    parts = []
    try:
        import config
        parts.append(config.llm_status())
    except Exception:
        parts.append("LLM not configured - deterministic mode")
    parts.append("voice input: " + ("on" if voice.stt_available() else "off (pip install faster-whisper)"))
    parts.append("read-aloud: " + ("on (needs internet)" if voice.tts_available() else "off (pip install gTTS)"))
    return " | ".join(parts)

# ---------------------------------------------------------------- chat
async def respond(message, history, lang_choice, topic, story, speak):
    history = history or []
    if not (message or "").strip():
        return "", history, topic, story, None
    out = await nagent.aask(await get_agent(), message, topic, lang_choice)
    lang = out.get("lang", "en")
    tools = ", ".join(out.get("tools", [])) or "none"
    mode = " (fallback mode)" if out.get("fallback") else ""
    reply = f"{out['answer']}\n\n<sub>Tools used: {tools}{mode}</sub>"
    history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
    new_topic = out.get("category") or topic
    new_story = message if (not topic or out.get("category")) and len(message) > len(story or "") // 3 else story
    audio = voice.speak(out["answer"], lang) if speak else None
    return "", history, new_topic, new_story, audio

def on_voice(path, lang_choice):
    if not path:
        return gr.update(), "Record something first."
    try:
        text, lang = voice.transcribe(path, lang_choice)
        return text, f"Heard ({kb.LANG_NAMES.get(lang, lang)}): {text}"
    except voice.VoiceUnavailable as e:
        return gr.update(), str(e)
    except Exception as e:
        return gr.update(), f"Could not transcribe: {type(e).__name__}: {e}"

# ---------------------------------------------------------------- drafts
def doc_labels():
    return [(kb.DOC_TYPES[k]["en"] + "  /  " + kb.DOC_TYPES[k]["hi"], k) for k in drafts.BUILD]

def on_doc_change(doc):
    fs = drafts.FIELDS[doc]
    ups = []
    for i in range(MAXF):
        if i < len(fs):
            f = fs[i]
            ups.append(gr.update(visible=True, label=f["label"] + ("" if f["required"] else " (optional)"), placeholder=f["hint"], value="", lines=3 if f["key"] in ("description", "problem", "facts", "info_sought") else 1))
        else:
            ups.append(gr.update(visible=False, value=""))
    return ups

def on_prefill(doc, story):
    pf = drafts.prefill(story or "")
    fs = drafts.FIELDS[doc]
    return [gr.update(value=pf.get(fs[i]["key"], "")) if i < len(fs) and pf.get(fs[i]["key"]) else gr.update() for i in range(MAXF)]

def on_generate(doc, *vals):
    fs = drafts.FIELDS[doc]
    d = drafts.make(doc, {fs[i]["key"]: vals[i] for i in range(len(fs))})
    miss = ("**Still to fill in:** " + "; ".join(d["missing"])) if d["missing"] else "All required details are filled in."
    tmp = tempfile.mkdtemp()
    txt, pdf = os.path.join(tmp, f"{doc}_draft.txt"), os.path.join(tmp, f"{doc}_draft.pdf")
    open(txt, "w", encoding="utf-8").write(d["text"])
    files = [txt]
    try:
        files.append(drafts.to_pdf(d["text"], pdf))
    except Exception:
        pass
    return d["text"], f"{miss}\n\n**Next step:** {d['next']}\n\n> {kb.DISCLAIMER['en']}", files

def pick_doc_for(topic, current):
    if topic in kb.CATS:
        d = kb.CATS[topic]["draft"]
        return gr.update(value=d)
    return gr.update()

# ---------------------------------------------------------------- orders
def explain_order(file, text):
    body = (text or "").strip()
    if file is not None:
        try:
            body = orders.read_pdf(file if isinstance(file, str) else file.name)
        except Exception as e:
            return f"Could not read that PDF: {e}"
    return orders.explain(body)

EXAMPLES = ["My landlord is not returning my Rs 20,000 deposit",
            "मेरे मोबाइल की चोरी हो गई है, पुलिस रिपोर्ट नहीं लिख रही",
            "મારા શેઠે ત્રણ મહિનાનો પગાર આપ્યો નથી",
            "I want to ask my municipal office about my pending application (RTI)"]

def build_ui():
    with gr.Blocks(title="NyayMitra - legal aid in your language") as demo:
        gr.Markdown("# NyayMitra\n**Free legal help in your own language. Speak or type your problem.** "
                    "Know your rights, get the filing steps, and a ready-to-file draft.  \n"
                    "आपके अधिकार, फ़ाइल करने के चरण और तैयार ड्राफ़्ट  |  તમારા અધિકાર, ફાઇલ કરવાના પગલાં અને તૈયાર ડ્રાફ્ટ")
        gr.Markdown(f"> {kb.DISCLAIMER['en']}")
        gr.Markdown(f"<sub>{status_line()}</sub>")
        topic, story = gr.State(""), gr.State("")
        with gr.Tabs():
            with gr.Tab("1. Tell your problem"):
                with gr.Row():
                    with gr.Column(scale=1):
                        lang = gr.Dropdown(LANG_CHOICES, value="", label="Language / भाषा / ભાષા")
                        mic = gr.Audio(sources=["microphone"], type="filepath", label="Speak your problem (🎤)")
                        heard = gr.Markdown()
                        speak = gr.Checkbox(label="Read the answer aloud (needs internet)", value=False)
                        listen = gr.Audio(label="Listen", autoplay=True, interactive=False)
                        gr.Markdown("**Helplines**\n\n" + advice.helplines("en"))
                    with gr.Column(scale=2):
                        chat = gr.Chatbot(height=520, label="NyayMitra")
                        msg = gr.Textbox(label="Or type here", placeholder="Describe what happened, in any language")
                        with gr.Row():
                            for ex in EXAMPLES:
                                gr.Button(ex, size="sm").click(lambda e=ex: e, None, msg)
                        send = gr.Button("Ask", variant="primary")
                ins = [msg, chat, lang, topic, story, speak]
                outs = [msg, chat, topic, story, listen]
                send.click(respond, ins, outs); msg.submit(respond, ins, outs)
                mic.stop_recording(on_voice, [mic, lang], [msg, heard]).then(respond, ins, outs)
            with gr.Tab("2. Draft a document"):
                gr.Markdown("Pick a document, fill the boxes (or press *Fill from my story*), and download a ready-to-file draft. "
                            "Anything missing stays as a **[PLACEHOLDER]** so nothing is invented.")
                doc = gr.Dropdown(doc_labels(), value="rti", label="Document")
                with gr.Row():
                    prefill_btn = gr.Button("Fill from my story")
                    gen = gr.Button("Create draft", variant="primary")
                boxes = [gr.Textbox(visible=(i < len(drafts.FIELDS["rti"])), label=(drafts.FIELDS["rti"][i]["label"] if i < len(drafts.FIELDS["rti"]) else "")) for i in range(MAXF)]
                preview = gr.Textbox(label="Your draft (you can edit it here)", lines=22)
                notes = gr.Markdown()
                files = gr.File(label="Download", file_count="multiple")
                doc.change(on_doc_change, doc, boxes)
                prefill_btn.click(on_prefill, [doc, story], boxes)
                gen.click(on_generate, [doc] + boxes, [preview, notes, files])
                topic.change(pick_doc_for, [topic, doc], doc)
            with gr.Tab("3. Understand a court order"):
                gr.Markdown("Upload the order (text PDF) or paste its text. You get the decision, directions, deadlines and hard words in plain language.")
                of = gr.File(label="Court order (PDF)", file_types=[".pdf"], type="filepath")
                ot = gr.Textbox(label="...or paste the order text", lines=8)
                ob = gr.Button("Explain this order", variant="primary")
                oo = gr.Markdown()
                ob.click(explain_order, [of, ot], oo)
            try:                                       # optional: the original contract-review module
                import app as contract_app
                with gr.Tab("4. Contract review"):
                    contract_app.ingest.ensure_index()
                    up = gr.File(label="Upload contract (PDF)", file_types=[".pdf"], type="filepath")
                    add = gr.Button("Add contract"); st = gr.Markdown()
                    cdd = gr.Dropdown(label="Contract", choices=contract_app.choices(), value=(contract_app.choices() or [None])[0])
                    cchat = gr.Chatbot(height=420); cmsg = gr.Textbox(label="Ask about your contract"); cbtn = gr.Button("Ask", variant="primary")
                    add.click(contract_app.add_contract, up, [st, cdd])
                    for t in (cbtn.click, cmsg.submit):
                        t(contract_app.respond, [cmsg, cchat, cdd], [cmsg, cchat])
            except Exception as e:
                print("Contract tab disabled:", type(e).__name__, e)
    return demo

if __name__ == "__main__":
    share = "--share" in sys.argv   # public gradio.live link for the demo / judges
    port = int(os.environ.get("PORT", 7860))
    build_ui().launch(show_error=True, share=share, server_name="0.0.0.0" if share or os.environ.get("PORT") else "127.0.0.1", server_port=port)
