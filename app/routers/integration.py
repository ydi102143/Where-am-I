from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app import models as m
from app.schemas import IntegrationSet, IntegrationOut
from app.services.plan import get_or_create_demo_user

router = APIRouter(prefix="/v1", tags=["v1"])

@router.post("/integration", response_model=IntegrationOut)
def set_integration(payload: IntegrationSet, db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    stmt = select(m.Integration).where(m.Integration.user_id == user.id, m.Integration.kind == payload.kind, m.Integration.key == "default")
    row = db.execute(stmt).scalars().first()
    if row:
        row.value = payload.value
        db.add(row); db.commit(); db.refresh(row)
        return row
    row = m.Integration(user_id=user.id, kind=payload.kind, key="default", value=payload.value)
    db.add(row); db.commit(); db.refresh(row)
    return row

@router.get("/integration", response_model=IntegrationOut | None)
def get_integration(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    stmt = select(m.Integration).where(m.Integration.user_id == user.id, m.Integration.kind == "gcal_ics", m.Integration.key == "default")
    return db.execute(stmt).scalars().first()
