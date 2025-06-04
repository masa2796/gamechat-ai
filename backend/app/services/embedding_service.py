from typing import List
import openai
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class EmbeddingService:
    async def get_embedding(self, query: str) -> List[float]:
        """質問文をOpenAI APIでエンベディングに変換"""
        try:
            response = openai.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "message": f"エンベディング生成に失敗: {str(e)}",
                "code": "EMBEDDING_ERROR"
            })