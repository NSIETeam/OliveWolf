from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead

router = APIRouter()


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    obj = Project(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[ProjectRead])
def list_projects(tenant_id: str = Query(...), db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.tenant_id == tenant_id).order_by(Project.created_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    obj = db.get(Project, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="project not found")
    return obj
