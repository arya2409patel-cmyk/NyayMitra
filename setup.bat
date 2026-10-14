@echo off
REM One-time setup. Run from inside the NyayMitra folder.
python -m venv .venv
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen3:0.6b
ollama pull nomic-embed-text
if not exist .env copy .env.example .env
call .venv\Scripts\python.exe check_setup.py
pause
