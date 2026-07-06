from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Avatar, TrainingJob
from app.schemas import TrainingJobCreate, TrainingJobRead

router = APIRouter()


@router.post("", response_model=TrainingJobRead)
def create_training_job(payload: TrainingJobCreate, db: Session = Depends(get_db)):
    avatar = db.get(Avatar, payload.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="avatar not found")
    if not avatar.source_asset_uri:
        raise HTTPException(status_code=400, detail="avatar image must be uploaded before training")

    obj = TrainingJob(**payload.model_dump(), status="queued", progress="0")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Production: enqueue job id to Redis/RQ/Celery here.
    return obj


@router.get("/{job_id}", response_model=TrainingJobRead)
def get_training_job(job_id: str, db: Session = Depends(get_db)):
    obj = db.get(TrainingJob, job_id)
    if not obj:
        raise HTTPException(status_code=404, detail="training job not found")
    return obj
