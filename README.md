# NyayMitra - AI Legal-Aid Copilot for the Common Citizen
*Speak your problem. Know your rights. Get a ready-to-file letter.* Not legal advice.

**Team:** [NAME 1], [NAME 2], [NAME 3] - GTU-ITR Mevad, Mehsana
**Demo video:** [link]  |  **Live app:** [link]

## 1. Problem
Millions of Indians cannot afford a lawyer, cannot read legal language, and do not know their rights or which authority/form applies. Free legal aid (NALSA 15100) exists but few know it.

## 2. Team
| Name | Year / Branch | Role |
|---|---|---|
| [NAME 1] | | Product & pitch |
| [NAME 2] | | Agent & backend |
| [NAME 3] | | UI & demo |

## 3. Solution + Demo
Voice-first, trilingual (English / हिन्दी / ગુજરાતી), built on Indian law:
1. **Tell your problem** (voice or text) -> legal category (RTI, FIR, consumer, domestic violence, cyber, tenancy, wages), rights, authority, step-by-step filing, helplines.
2. **Draft a document** -> RTI / FIR / consumer complaint / demand letter with visible `[PLACEHOLDERS]`, PDF download.
3. **Understand a court order** -> parties, outcome, deadlines, next hearing, jargon glossary.
4. **Contract review** (rental, job, NDA) -> clause-cited answers + red-flag checklist.

Run the demo: see [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). Pitch: [docs/PITCH_SCRIPT.md](docs/PITCH_SCRIPT.md).

## 4. How we built it
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the diagram.
- LangChain `create_agent` + `ChatOllama(qwen3:0.6b)`, 5 legal-aid tools + 4 contract tools.
- Curated trilingual knowledge base; deterministic classifier, drafts and order explainer; LLM only for follow-ups, with deterministic fallback.
- Contract mode: PyPDFLoader, clause-aware splitting, `BAAI/bge-small-en-v1.5` -> Chroma, retriever k=3.
- **MCP bonus:** all tools served by FastMCP on :8001/mcp and fetched at runtime via `MultiServerMCPClient`.
- Gradio UI, disclaimer appended by code, 55 tests.

### Run it (Windows)
```
setup.bat            # venv, packages, ollama pull qwen3:0.6b
python check_setup.py
run_app.bat          # python app_nyaya.py
run_share.bat        # same, with a public link (python app_nyaya.py --share)
python -m pytest tests -q
```
MCP: `run_mcp_demo.bat` (or `python mcp_server.py` + `python app.py --mcp`).
Optional voice: `pip install faster-whisper gTTS` (speech-to-text offline, read-aloud needs internet).

### Deploy
Ollama cannot run on free hosts. Options: (a) `--share` from the demo laptop; (b) Hugging Face Space (Gradio) – the fast path, drafts and order explainer work with no LLM, the agent falls back to deterministic mode; set `EMBEDDINGS_BACKEND=hash` there.

## 5. Close
**Who:** people who cannot afford a lawyer, starting with Gujarat. **Who pays:** NGOs, legal-services authorities, CSR programs; free for citizens. **Next:** scanned-order OCR, state-specific fees/forms verified with legal-aid clinics, WhatsApp channel.

## Honest limits
- General information, not legal advice. Fees, forms and authorities vary by state and must be verified.
- Hindi/Gujarati text needs native-speaker review.
- Court orders: text PDFs only (no OCR). Drafts are in English.
- Voice, live Ollama and real bge embeddings are optional paths; automated tests use offline fallbacks.

MIT licensed.
