from fastapi import APIRouter, Depends

from app.api.v1 import avatars, conversations, health, knowledge, projects, render_jobs, tenants
from app.core.security import require_api_key

api_router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(require_api_key)])

api_router.include_router(health.router, tags=["health"])
protected_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
protected_router.include_router(projects.router, prefix="/projects", tags=["projects"])
protected_router.include_router(avatars.router, prefix="/avatars", tags=["avatars"])
protected_router.include_router(knowledge.router, prefix="/knowledge-sources", tags=["knowledge"])
protected_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
protected_router.include_router(render_jobs.router, prefix="/render-jobs", tags=["render-jobs"])

api_router.include_router(protected_router)
