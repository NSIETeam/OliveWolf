from fastapi import APIRouter

from app.api.v1 import avatars, conversations, health, knowledge, projects, render_jobs, tenants

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(avatars.router, prefix="/avatars", tags=["avatars"])
api_router.include_router(knowledge.router, prefix="/knowledge-sources", tags=["knowledge"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(render_jobs.router, prefix="/render-jobs", tags=["render-jobs"])
