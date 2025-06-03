from fastapi import FastAPI, Request, HTTPException, Response, Cookie, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import httpx
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError


app = FastAPI()

# CORS設定（必要に応じてドメインを変更）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番はフロントのドメインに変更
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET_TEST")
print("RECAPTCHA_SECRET:", RECAPTCHA_SECRET)

class ContextItem(BaseModel):
    title: str
    text: str
    score: float

class RagRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)
    top_k: Optional[int] = 3
    with_context: Optional[bool] = True
    recaptchaToken: Optional[str] = None

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v):
        if not v.strip():
            raise ValueError("questionは空白のみ不可")
        return v

    @field_validator("top_k")
    @classmethod
    def top_k_range(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("top_kは1〜10の範囲で指定してください")
        return v

class RagResponse(BaseModel):
    answer: str
    context: Optional[List[ContextItem]]

class RagResponseNoContext(BaseModel):
    answer: str

async def verify_recaptcha(token: str) -> bool:
    """
    Google reCAPTCHA v2/v3の検証
    """
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": RECAPTCHA_SECRET,
        "response": token,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data, timeout=5)
        if resp.status_code != 200:
            return False
        result = resp.json()
        return result.get("success", False)

def is_suspicious(request: Request, user_ip: str) -> bool:
    # ここにレート制限や異常検出ロジックを実装（例: RedisでIPごとの回数カウント）
    # 今回はダミーで常にFalse
    return False

@app.post("/api/rag/query")
async def rag_query(
    request: Request,
    response: Response,
    rag_req: RagRequest = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None)
):
    # 受信したリクエストボディ全体をログに出力
    try:
        raw_body = await request.body()
        print("=== 受信リクエスト ===")
        print(raw_body.decode("utf-8"))
    except Exception as e:
        print(f"リクエストボディの表示に失敗: {e}")

    user_ip = request.client.host

    
    # ① Cookieがなければ初回認証
    if not recaptcha_passed:
        recaptcha_result = await verify_recaptcha(rag_req.recaptchaToken)
        if not rag_req.recaptchaToken or not recaptcha_result:
            raise HTTPException(status_code=400, detail={
                "message": f"reCAPTCHAトークンが無効です（検証結果: {recaptcha_result}）",
                "code": "INVALID_RECAPTCHA"
            })
        # 認証成功→Cookieセット
        response.set_cookie(
            key="recaptcha_passed",
            value="true",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60*60*24*7  # 7日
        )
        recaptcha_status = "認証: 初回reCAPTCHA検証OK"
    else:
        # ② Cookieあり→異常検出時のみ再認証
        if is_suspicious(request, user_ip):
            recaptcha_result = await verify_recaptcha(rag_req.recaptchaToken)
            if not rag_req.recaptchaToken or not recaptcha_result:
                raise HTTPException(status_code=400, detail={
                    "message": f"reCAPTCHAトークンが無効です（検証結果: {recaptcha_result}）",
                    "code": "INVALID_RECAPTCHA"
                })
            # 再認証成功→Cookie再セット
            response.set_cookie(
                key="recaptcha_passed",
                value="true",
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=60*60*24*7
            )
            recaptcha_status = "認証: 再認証reCAPTCHA検証OK"
        else:
            recaptcha_status = "認証: Cookieのみで通過"

    # ダミーコンテキスト
    dummy_context = [
        ContextItem(
            title="カード解説 - ブラック・ロータス",
            text="ブラック・ロータスはマナを3点追加できる...",
            score=0.95
        ),
        ContextItem(
            title="カードランキング",
            text="レアカードの中でも強力とされる...",
            score=0.87
        )
    ][:rag_req.top_k]

    answer = "《ブラック・ロータス》はマナ加速カードで、相手に大ダメージを与える。"

    # StreamingResponseではなく、通常のJSONで返す
    if rag_req.with_context:
        return {
            "answer": answer,
            "context": [c.model_dump() for c in dummy_context]
        }
    else:
        return {"answer": answer}

# --- エラーハンドラ ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    # バリデーションエラーをAPI仕様書の形式で返す
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": exc.errors()[0]["msg"],
                "code": "VALIDATION_ERROR"
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # HTTPExceptionのdetailがdictならそのまま返す
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(status_code=exc.status_code, content={"error": {"message": str(exc.detail), "code": "HTTP_ERROR"}})