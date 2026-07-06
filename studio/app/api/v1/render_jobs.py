from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import RenderJob
from app.schemas import RenderJobCreate, RenderJobRead

router = APIRouter()


@router.post("", response_model=RenderJobRead)
def create_render_job(payload: RenderJobCreate, db: Session = Depends(get_db)):
    obj = RenderJob(**payload.model_dump(), status="queued")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Production: enqueue job id to Redis/RQ/Celery here.
    return obj


@router.get("/{job_id}", response_model=RenderJobRead)
def get_render_job(job_id: str, db: Session = Depends(get_db)):
    obj = db.get(RenderJob, job_id)
    if not obj:
        raise HTTPException(status_code=404, detail="render job not found")
    return obj
