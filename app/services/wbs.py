from __future__ import annotations
import json
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models as m
from app.schemas import WbsTask, WbsPlanRequest
from app.core.ai import generate_text

SYSTEM = "あなたは実行計画作成の専門家。短く具体的に、実行順に並べる。"

PROMPT_TEMPLATE = """目標: {title}
理由: {why}
KGI: {kgi}
締切: {deadline}

制約:
- 1タスクは30〜60分を目安（最初の2つは5〜10分の導入可）
- 依存関係を考慮して実行順で並べる
- 出力はJSON配列のみ。各要素は {{title, effort_min, impact, due(null可), prereq_ids([]可)}}。
- 日本語で簡潔に。

例:
[
  {{"title":"READMEの章立てだけ書く","effort_min":10,"impact":3,"due":null,"prereq_ids":[]}},
  {{"title":"APIスケルトンを作成","effort_min":45,"impact":5,"due":null,"prereq_ids":[0]}},
  {{"title":"/v1/plan/today 実装","effort_min":60,"impact":5,"due":null,"prereq_ids":[1]}}
]

では、{max_tasks}件以内で出力してください。"""

def _ai_generate(goal: m.Goal, req: WbsPlanRequest) -> Optional[List[WbsTask]]:
    deadline = goal.deadline.isoformat() if goal.deadline else "なし"
    user = PROMPT_TEMPLATE.format(title=goal.title, why=goal.why or "", kgi=goal.kgi or "", deadline=deadline, max_tasks=req.max_tasks)
    raw = generate_text(SYSTEM, user, max_tokens=800)
    if not raw:
        return None
    try:
        start = raw.find("["); end = raw.rfind("]")
        blob = raw[start:end+1] if start != -1 and end != -1 else raw
        data = json.loads(blob)
        items = [WbsTask(**x) for x in data if isinstance(x, dict)]
        return items or None
    except Exception:
        return None

def _rule_generate(goal: m.Goal, req: WbsPlanRequest) -> List[WbsTask]:
    base = [
        WbsTask(title="目的とスコープを1段落で書く", effort_min=10, impact=3),
        WbsTask(title="章立て・ToCを作る", effort_min=20, impact=3),
        WbsTask(title="最小スケルトンを作成", effort_min=40, impact=5),
        WbsTask(title="主要機能Aの雛形を実装", effort_min=60, impact=5),
        WbsTask(title="主要機能Bの雛形を実装", effort_min=60, impact=4),
        WbsTask(title="READMEを更新", effort_min=30, impact=2),
        WbsTask(title="軽いE2E確認＆TODO洗い出し", effort_min=30, impact=3),
    ]
    return base[: req.max_tasks]

def _spread_due(items: List[WbsTask], start: date, end: date) -> None:
    if start > end or not items:
        return
    span = (end - start).days or 1
    n = len(items)
    for i, it in enumerate(items):
        if it.due is not None:
            continue
        pos = int(i * span / max(1, n - 1))
        it.due = start + timedelta(days=pos)

def generate_wbs(db: Session, goal: m.Goal, req: WbsPlanRequest) -> List[WbsTask]:
    items = _ai_generate(goal, req)
    if not items:
        items = _rule_generate(goal, req)
    cleaned: List[WbsTask] = []
    for it in items[: req.max_tasks]:
        eff = min(max(it.effort_min, 5), 120 if it.impact >= 4 else 60)
        imp = min(max(it.impact, 1), 5)
        cleaned.append(WbsTask(title=it.title.strip()[:200], effort_min=eff, impact=imp, due=it.due, prereq_ids=it.prereq_ids or []))
    if goal.deadline and req.spread_until_deadline:
        today = date.today(); start = today; end = goal.deadline
        if end < start:
            for it in cleaned:
                if it.due is None: it.due = today
        else:
            _spread_due(cleaned, start, end)
    return cleaned

def save_wbs_as_tasks(db: Session, goal: m.Goal, items: List[WbsTask]) -> int:
    existing = set(t.title.strip() for t in db.execute(select(m.Task.title).where(m.Task.goal_id == goal.id)).scalars().all())
    count = 0
    for it in items:
        title = it.title.strip()
        if title in existing: continue
        task = m.Task(goal_id=goal.id, title=title, status="pending", impact=it.impact, effort_min=it.effort_min, due=it.due, parent_task_id=None)
        db.add(task); existing.add(title); count += 1
    db.commit()
    return count
