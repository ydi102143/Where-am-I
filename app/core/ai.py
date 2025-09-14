from __future__ import annotations
import os

AI_ENABLED = os.getenv("AI_ENABLED", "false").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def dummy_generate(system: str, user: str, max_tokens: int = 160) -> str:
    hint = "まず2分だけ、見出しを書き出そう。"
    if "要約" in user or "summary" in user.lower():
        return "直近の学び: 小さく始めると進む。次は粒度を30分に。改善: 朝に5分で着手タスクを作る。"
    return hint

def _openai_generate(system: str, user: str, max_tokens: int = 160) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)  # type: ignore
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": system},{"role": "user", "content": user}],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()

def generate_text(system: str, user: str, max_tokens: int = 160) -> str:
    if not AI_ENABLED:
        return dummy_generate(system, user, max_tokens)
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            return dummy_generate(system, user, max_tokens)
        try:
            return _openai_generate(system, user, max_tokens)
        except Exception:
            return dummy_generate(system, user, max_tokens)
    return dummy_generate(system, user, max_tokens)
