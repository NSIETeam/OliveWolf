import json
import time
from pathlib import Path

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.models import Avatar, RenderJob, TrainingJob
from app.services.object_store import ObjectStore


def _write_artifact(tenant_id: str, name: str, payload: dict) -> str:
    store = ObjectStore()
    key = f"{tenant_id}/artifacts/{name}.json"
    path = store.root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"local://{key}"


def process_training_job(db, job: TrainingJob) -> None:
    job.status = "running"
    job.progress = "20"
    db.commit()

    avatar = db.get(Avatar, job.avatar_id)
    if not avatar or not avatar.source_asset_uri:
        job.status = "failed"
        job.error_message = "avatar source image is missing"
        db.commit()
        return

    job.progress = "70"
    db.commit()

    artifact = {
        "kind": "olivewolf_avatar_artifact",
        "training_job_id": job.id,
        "tenant_id": job.tenant_id,
        "project_id": job.project_id,
        "avatar_id": job.avatar_id,
        "training_preset": job.training_preset,
        "source_asset_uri": avatar.source_asset_uri,
        "status": "ready_for_gpu_render_worker",
        "note": "This local worker creates a deployable asset manifest. GPU workers can consume this artifact to build LivePortrait/LHM caches.",
    }
    job.output_uri = _write_artifact(job.tenant_id, f"training-{job.id}", artifact)
    job.progress = "100"
    job.status = "succeeded"
    db.commit()


def process_render_job(db, job: RenderJob) -> None:
    job.status = "running"
    db.commit()
    artifact = {
        "kind": "olivewolf_render_placeholder",
        "render_job_id": job.id,
        "tenant_id": job.tenant_id,
        "project_id": job.project_id,
        "avatar_id": job.avatar_id,
        "scene": job.scene,
        "input_text": job.input_text,
        "status": "ready_for_gpu_renderer",
    }
    job.output_uri = _write_artifact(job.tenant_id, f"render-{job.id}", artifact)
    job.status = "succeeded"
    db.commit()


def run_once() -> None:
    init_db()
    db = SessionLocal()
    try:
        training_job = db.query(TrainingJob).filter(TrainingJob.status == "queued").order_by(TrainingJob.created_at.asc()).first()
        if training_job:
            process_training_job(db, training_job)
            return
        render_job = db.query(RenderJob).filter(RenderJob.status == "queued").order_by(RenderJob.created_at.asc()).first()
        if render_job:
            process_render_job(db, render_job)
    finally:
        db.close()


def main() -> None:
    print("OliveWolf Studio worker started")
    while True:
        run_once()
        time.sleep(2)


if __name__ == "__main__":
    main()
