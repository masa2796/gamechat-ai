from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class ContextItem(BaseModel):
    title: str
    text: str
    score: float

class RagRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)
    top_k: Optional[int] = 50
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
        if v is not None and (v < 1 or v > 100):
            raise ValueError("top_kは1〜100の範囲で指定してください")
        return v

class RagResponse(BaseModel):
    answer: str
    context: Optional[List[ContextItem]]

class RagResponseNoContext(BaseModel):
    answer: str