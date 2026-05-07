"""Pattern detection stub — full implementation in Week 3."""
from celery_app import celery_app


@celery_app.task(name="tasks.patterns.detect_patterns", bind=True)
def detect_patterns(self, user_id: str) -> dict:
    """
    Stub: will run all pattern detectors over the user's full mistake history.
    Detectors implemented in Week 3:
      - HangingPieceOnSquare
      - OpeningPlanFailure
      - RecurringMotifMiss
    """
    return {"user_id": user_id, "status": "patterns_not_yet_implemented"}
