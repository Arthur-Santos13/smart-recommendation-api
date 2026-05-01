from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.jobs.retrain_job import retrain_models

router = APIRouter()


@router.post(
    "/retrain",
    summary="Trigger immediate model retraining",
    response_description="Retraining started synchronously",
)
def trigger_retrain():
    """
    Immediately retrain both ML models and refresh the in-memory registry.

    This endpoint runs the same job that APScheduler executes on its
    interval, but on demand. Useful after bulk data imports or when you
    want to force a cache refresh without waiting for the next scheduled
    run.

    The call is **synchronous** — it blocks until training is complete
    (typically a few seconds on seeded data).
    """
    retrain_models()
    return JSONResponse(
        status_code=200,
        content={"detail": "Model retraining completed successfully."},
    )
