from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantRead

router = APIRouter()


@router.post("", response_model=TenantRead)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    existing = db.query(Tenant).filter(Tenant.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="tenant slug already exists")
    obj = Tenant(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{tenant_id}", response_model=TenantRead)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    obj = db.get(Tenant, tenant_id)
    if not obj:
        raise HTTPException(status_code=404, detail="tenant not found")
    return obj
