# Backend (FastAPI + LangGraph + Groq)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # then fill GROQ_API_KEY (server-side only)
uvicorn app.main:app --reload --port 8000
pytest
```
Docs at http://localhost:8000/docs

The default model is `openai/gpt-oss-20b`, selected for low-latency inference and
support for tool calling and structured output. Set `GROQ_MODEL` to change it;
`LLM_FALLBACK_MODEL` is an optional fallback. Keep `GROQ_API_KEY` only in
`backend/.env`; never expose it through frontend environment variables.
