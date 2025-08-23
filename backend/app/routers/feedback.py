from fastapi import APIRouter, Body, HTTPException, Depends
from ..models.feedback_models import FeedbackCreate
from ..services.feedback_service import feedback_service
from ..core.auth import require_read_permission

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(fb: FeedbackCreate = Body(...), auth_info: dict = Depends(require_read_permission)):
    try:
        stored = feedback_service.submit_feedback(fb)
        return {"status": "ok", "data": stored.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/recent")
async def list_recent(limit: int = 50, auth_info: dict = Depends(require_read_permission)):
    items = feedback_service.list_recent(limit)
    return {"items": [i.model_dump() for i in items]}
