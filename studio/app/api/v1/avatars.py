from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Avatar
from app.schemas import AvatarCreate, AvatarRead
from app.services.object_store import ObjectStore

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


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


@router.post("/{avatar_id}/upload", response_model=AvatarRead)
async def upload_avatar_asset(avatar_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    obj = db.get(Avatar, avatar_id)
    if not obj:
        raise HTTPException(status_code=404, detail="avatar not found")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="only jpeg/png/webp avatar images are supported")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"file too large; max {settings.max_upload_mb}MB")

    suffix = ALLOWED_IMAGE_TYPES[file.content_type]
    uri = ObjectStore().put_bytes(obj.tenant_id, data, suffix)
    obj.source_asset_uri = uri
    obj.status = "ready"
    db.commit()
    db.refresh(obj)
    return obj
