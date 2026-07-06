from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import KnowledgeSource
from app.schemas import KnowledgeSourceCreate, KnowledgeSourceRead

router = APIRouter()


@router.post("", response_model=KnowledgeSourceRead)
def create_knowledge_source(payload: KnowledgeSourceCreate, db: Session = Depends(get_db)):
    obj = KnowledgeSource(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[KnowledgeSourceRead])
def list_knowledge_sources(tenant_id: str = Query(...), project_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(KnowledgeSource).filter(KnowledgeSource.tenant_id == tenant_id)
    if project_id:
        q = q.filter(KnowledgeSource.project_id == project_id)
    return q.order_by(KnowledgeSource.created_at.desc()).all()


@router.post("/{source_id}/ingest", response_model=KnowledgeSourceRead)
def ingest_knowledge_source(source_id: str, db: Session = Depends(get_db)):
    obj = db.get(KnowledgeSource, source_id)
    if not obj:
        raise HTTPException(status_code=404, detail="knowledge source not found")
    # Placeholder: production worker should chunk, embed, index and validate source.
    obj.status = "indexed"
    db.commit()
    db.refresh(obj)
    return obj
