def run_render_job(job_id: str) -> None:
    """Worker entrypoint placeholder.

    Production flow:
    - Load RenderJob from DB.
    - Resolve avatar and project configuration.
    - For realtime/portrait: call OliveWolf Core LivePortrait backend.
    - For offline/3D: call OliveWolf Core LHM backend.
    - Store output in object storage.
    - Update job status and output_uri.
    """
    raise NotImplementedError("render worker integration is planned for the next milestone")
