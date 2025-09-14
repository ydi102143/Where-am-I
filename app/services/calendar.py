from __future__ import annotations
import requests
from datetime import datetime, date, time
from typing import List, Tuple
from ics import Calendar
from dateutil.tz import gettz

JST = gettz("Asia/Tokyo")

def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m), tzinfo=JST)

def fetch_events_yyyymmdd(ics_url: str, target: date) -> List[Tuple[datetime, datetime]]:
    r = requests.get(ics_url, timeout=10)
    r.raise_for_status()
    cal = Calendar(r.text)
    day_start = datetime.combine(target, time(0,0,tzinfo=JST))
    day_end   = datetime.combine(target, time(23,59,tzinfo=JST))
    spans: List[Tuple[datetime, datetime]] = []
    for e in cal.events:
        start = e.begin.astimezone(JST).datetime
        end   = e.end.astimezone(JST).datetime
        if end < day_start or start > day_end: continue
        s = max(start, day_start); t = min(end, day_end)
        if s < t: spans.append((s, t))
    spans.sort(key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    for s, t in spans:
        if not merged or s > merged[-1][1]:
            merged.append((s, t))
        else:
            ps, pt = merged[-1]; merged[-1] = (ps, max(pt, t))
    return merged

def free_minutes_between(ics_url: str, target: date, work_start: str, work_end: str, min_block: int = 15) -> int:
    spans = fetch_events_yyyymmdd(ics_url, target)
    ws = datetime.combine(target, _parse_hhmm(work_start))
    we = datetime.combine(target, _parse_hhmm(work_end))
    if we <= ws: return 0
    busy = []
    for s, t in spans:
        if t <= ws or s >= we: continue
        busy.append((max(s, ws), min(t, we)))
    busy.sort(key=lambda x: x[0])
    merged = []
    for s, t in busy:
        if not merged or s > merged[-1][1]: merged.append((s, t))
        else:
            ps, pt = merged[-1]; merged[-1] = (ps, max(pt, t))
    total = int((we - ws).total_seconds() // 60)
    busy_sum = sum(int((t - s).total_seconds() // 60) for s, t in merged)
    free = max(0, total - busy_sum)
    free = (free // min_block) * min_block
    return free
