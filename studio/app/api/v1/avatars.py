from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Avatar
from app.schemas import AvatarCreate, AvatarRead

router = APIRouter()


@router.post("", response_model=AvatarRead)
def create_avatar(payload: AvatarCreate, db: Session = Depends(get_db)):
    obj = Avatar(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[AvatarRead])
def list_avatars(tenant_id: str = Query(...), project_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Avatar).filter(Avatar.tenant_id == tenant_id)
    if project_id:
        q = q.filter(Avatar.project_id == project_id)
    return q.order_by(Avatar.created_at.desc()).all()


@router.post("/{avatar_id}/assets", response_model=AvatarRead)
def attach_avatar_asset(avatar_id: str, asset_uri: str, db: Session = Depends(get_db)):
    obj = db.get(Avatar, avatar_id)
    if not obj:
        raise HTTPException(status_code=404, detail="avatar not found")
    obj.source_asset_uri = asset_uri
    obj.status = "ready"
    db.commit()
    db.refresh(obj)
    return obj
