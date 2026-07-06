from dataclasses import dataclass


@dataclass
class QueuedTask:
    task_id: str
    status: str = "queued"


class RenderQueue:
    """Queue abstraction. Current implementation is a placeholder for Redis/RQ/Celery."""

    def enqueue_render_job(self, job_id: str) -> QueuedTask:
        return QueuedTask(task_id=job_id)
