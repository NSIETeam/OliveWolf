def run_training_job(job_id: str) -> None:
    """Training/build worker entrypoint placeholder.

    In OliveWolf, customer-facing "training" means building a deployable digital-human asset:
    - validate uploaded portrait/full-body source image
    - preprocess avatar assets
    - optionally build LHM full-body 3D cache
    - optionally prepare LivePortrait source cache
    - register output artifact URI

    Production deployments should run this inside a GPU worker container.
    """
    raise NotImplementedError("training worker integration is planned for the GPU worker milestone")
