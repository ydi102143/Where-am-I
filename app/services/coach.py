from __future__ import annotations
from typing import List, Dict, Any
from app.core.ai import generate_text

SYSTEM_COACH = "あなたは優秀なパーソナルプロダクティビティコーチ。短く実行的に話す。"
SYSTEM_SUMMARY = "あなたは簡潔で実用的なレビュー編集者。要約は箇条書き、改善案は動詞から始める。"

def coach_line_for_task(title: str, effort_min: int, context: dict | None = None) -> str:
    user = (f"タスク: {title}\n"
            f"想定時間: {effort_min}分\n"
            "出力: 20字以内の日本語で『今すぐ始められる一言』を1つ。句読点は1つまで。")
    text = generate_text(SYSTEM_COACH, user, max_tokens=50)
    return (text or "まず2分だけ、見出しを書こう。").strip()

def summarize_reflections(items: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
    join_text = "\n".join([f"- {it['date']} (mood={it.get('mood','-')}) {(it.get('text') or '')[:240]}" for it in items])
    user = (f"直近{days}日のメモ:\n{join_text}\n\n"
            "出力: 1) 要約（80字以内, 箇条書き2点まで） 2) 改善案3つ（各15字以内, 動詞始まり）")
    raw = generate_text(SYSTEM_SUMMARY, user, max_tokens=180)
    summary = []; improvements = []
    if raw:
        lines = [x.strip("-・* \n") for x in raw.splitlines() if x.strip()]
        mode = "summary"
        for ln in lines:
            if any(k in ln for k in ["改善", "改善案", "次の"]):
                mode = "improve"; continue
            if mode == "summary": summary.append(ln)
            else: improvements.append(ln)
    summary = [s for s in summary if s][:2] or ["小さく始めて前進。粒度は30分に調整。"]
    improvements = [i for i in improvements if i][:3] or ["朝に5分着手","粒度を30分に","締切前倒し"]
    return {"summary": " / ".join(summary[:2]), "improvements": improvements[:3]}
