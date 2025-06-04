from typing import List
import openai
from app.models.rag_models import ContextItem
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class LLMService:
    async def generate_answer(self, query: str, context_items: List[ContextItem]) -> str:
        """検索結果を元にLLMで回答を生成"""
        try:
            context_text = "\n\n".join([
                f"【{item.title}】\n{item.text}"
                for item in context_items
            ])
            
            system_prompt = """あなたはカードゲームの専門アシスタントです。
提供された参考情報をもとに、簡潔かつ正確に日本語で回答してください。
挨拶や雑談には簡単な返答をしてください。
カードやゲームに関する情報が見つからない場合は「情報がありません」とだけ返してください。"""
            
            user_prompt = f"""質問: {query}

参考情報:
{context_text}

上記の参考情報を基に、質問に対する回答をお願いします。"""

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM回答生成エラー: {e}")
            return f"申し訳ありませんが、「{query}」に関する回答の生成中にエラーが発生しました。"