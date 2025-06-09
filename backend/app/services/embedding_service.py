from typing import List
import openai
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

class EmbeddingService:
    def __init__(self):
        # OpenAI クライアントを初期化（環境変数からAPIキーを取得）
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    async def get_embedding(self, query: str) -> List[float]:
        """質問文をOpenAI APIでエンベディングに変換"""
        if not self.client:
            raise HTTPException(status_code=500, detail={
                "message": "OpenAI APIキーが設定されていません",
                "code": "API_KEY_NOT_SET"
            })
        
        try:
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "message": f"エンベディング生成に失敗: {str(e)}",
                "code": "EMBEDDING_ERROR"
            })