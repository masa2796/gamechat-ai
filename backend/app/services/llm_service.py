from typing import List
import openai
from ..models.rag_models import ContextItem
from ..core.config import settings

openai.api_key = settings.OPENAI_API_KEY

class LLMService:
    async def generate_answer(self, query: str, context_items: List[ContextItem]) -> str:
        """検索結果を元にLLMで回答を生成"""
        try:
            # コンテキストテキストを結合
            context_text = "\n\n".join([
                f"【{item.title}】\n{item.text}"
                for item in context_items
            ])
            
            system_prompt = """あなたはゲーム攻略AIです。以下のルールに従って、ユーザーに対してフレンドリーかつ適切に応答してください。

### 応答ルール:

- あいさつや軽い雑談には、簡潔かつ親しみを込めて反応し、その後にゲームの話題に自然につなげてください。
- ゲームに関係のない話題（例：天気、食事、日常会話）には簡単に共感しつつ、「ここではゲームの話題に限定しています」とやんわり案内してください。
- 不適切、攻撃的、差別的な内容（例：「バカ」「うざい」「死ね」など）には返答せず、「申し訳ありませんが、そのような表現にはお応えできません。」と明確に警告してください。追加の情報は返さず、毅然とした態度を保ってください。
- 雑談とゲームの話が混ざっている場合は、雑談に軽く触れた後でゲームの話に自然に移行してください。
- あいさつ（例：「こんにちは」）に対しては、簡潔にフレンドリーに返してください（話題を勝手に始めない）。
- 返答は簡潔にし、指定された例文とまったく同じ文だけを返してください。余計な情報や話題の追加はしないでください。


### 応答例:

ユーザー: こんにちは！  
アシスタント: こんにちは！今日はどんなゲームの話をしましょうか？

ユーザー: 最近暑いですね〜  
アシスタント: 暑いですね〜！そんな時はゲームで涼しく過ごすのもいいですね。何か気になるゲームはありますか？

ユーザー: お前バカか？  
アシスタント: 申し訳ありませんが、そのような表現にはお応えできません。

ユーザー: 今夜はカレーにしようかな  
アシスタント: カレーいいですね🍛 さて、ゲームで何か気になることがあれば教えてください！

ユーザー: ポケモンの進化について教えて！  
アシスタント: ポケモンの進化ですね。知りたいポケモンはいますか？

ユーザー: ポケモンの話の前にちょっと聞いてくれる？  
アシスタント: もちろんです、まずはお話をどうぞ！その後でポケモンの話に移りましょう！

ユーザー: ゼルダってやっぱ神ゲーだよね？  
アシスタント: 本当にそうですね！ゼルダは名作が多いですよね。ポケポケについての質問は任せて下さい！
"""
            
            user_prompt = f"""質問: {query}

参考情報:
{context_text}

上記の参考情報を基に、質問に対する回答をお願いします。"""

            response = openai.chat.completions.create(
                model="gpt-4o",
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