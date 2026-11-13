# ULTRON AI 4.0

A local Flask-based AI assistant using Ollama.

## Requirements

- Python 3.11 or newer
- Ollama installed separately
- The qwen2.5:1.5b model

## Setup on Windows

1. Install Python and Ollama.
2. Open PowerShell in this project folder.
3. Create a virtual environment:

   python -m venv .venv

4. Activate it:

   .venv\Scripts\Activate.ps1

5. Install dependencies:

   python -m pip install -r requirements.txt

6. Download the model:

   ollama pull qwen2.5:1.5b

7. Start Ollama.
8. Start ULTRON:

   python run.py

9. Open http://127.0.0.1:5000

## Notes

- This package does not contain Python's virtual environment.
- Ollama and its model must be installed separately.
- This is a local development project, not a public production deployment.
- Review security, privacy, authentication and rate limiting before any public hosting.
