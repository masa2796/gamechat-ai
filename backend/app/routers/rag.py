from fastapi import APIRouter, Request, Response, Body, Cookie, HTTPException
from typing import Optional
from app.models.rag_models import RagRequest
from app.services.rag_service import RagService
from app.services.auth_service import AuthService

router = APIRouter()
rag_service = RagService()
auth_service = AuthService()

@router.post("/rag/query")
async def rag_query(
    request: Request,
    response: Response,
    rag_req: RagRequest = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None)
):
    recaptcha_status = await auth_service.verify_request(
        request, response, rag_req.recaptchaToken, recaptcha_passed
    )
    if not recaptcha_status:
        raise HTTPException(status_code=401, detail="認証に失敗しました")
      
    result = await rag_service.process_query(rag_req)
    
    return result