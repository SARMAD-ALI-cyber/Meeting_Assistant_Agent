"""Optional one-off LLM smoke test (requires GROQ_API_KEY in .env)."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python scripts/groq_smoke.py` from repo root without PYTHONPATH / editable install.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import get_settings


def main() -> None:
    load_dotenv()
    s = get_settings()
    llm = ChatGroq(
        model=s.groq_model,
        temperature=0,
        max_retries=2,
        api_key=s.groq_api_key,
    )
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Reply with exactly: ok"),
    ]
    print(llm.invoke(messages).content)


if __name__ == "__main__":
    main()
