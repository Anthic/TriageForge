# Backend (FastAPI + LangGraph + Gemini)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # then fill GEMINI_API_KEY and GEMINI_MODEL
uvicorn app.main:app --reload --port 8000
pytest
```
Docs at http://localhost:8000/docs
