import os
import json
import openai
from dotenv import load_dotenv
from upstash_vector import Index

# 環境変数のロード
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path)

openai.api_key = os.getenv("OPENAI_API_KEY")
upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

def get_query_embedding(query):
    out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'query_data.json')
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if item.get("query") == query and "embedding" in item:
                            print("query_data.jsonのエンベディングを再利用します。")
                            return item["embedding"]
                elif isinstance(data, dict):
                    if data.get("query") == query and "embedding" in data:
                        print("query_data.jsonのエンベディングを再利用します。")
                        return data["embedding"]
            except Exception:
                pass
    response = openai.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    return embedding

def search_vector_db_all_namespaces(query, top_k=3, namespaces=None):
    embedding = get_query_embedding(query)
    index = Index(url=upstash_url, token=upstash_token)

    if namespaces is None:
        namespaces = [
            "summary", "flavor", "attacks", "height", "weight", "evolves",
            "hp", "weakness", "type", "set-info", "releaseDate", "category", "rarity"
        ]

    all_matches = []
    for ns in namespaces:
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_vectors=True,
            include_metadata=True,
            namespace=ns
        )
        matches = results.matches if hasattr(results, "matches") else results
        for hit in matches:
            score = getattr(hit, 'score', None)
            meta = getattr(hit, 'metadata', None)
            text = meta.get('text') if meta else getattr(hit, 'text', None)
            all_matches.append({
                "namespace": ns,
                "id": getattr(hit, 'id', None),
                "score": score,
                "text": text
            })

    if not all_matches:
        return None

    # スコア最大のものを返す
    best = max(all_matches, key=lambda x: x["score"] or 0)
    return best

def generate_llm_answer(query, context_text):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはポケモンカードの専門家です。与えられた情報をもとに、ユーザーの質問に日本語で簡潔かつ正確に答えてください。"},
            {"role": "user", "content": f"質問: {query}\n\n参考情報: {context_text}"}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    user_query = "フシギダネの弱点は？"
    best_match = search_vector_db_all_namespaces(user_query, top_k=3)
    if best_match and best_match["text"]:
        print(f"\n--- ベクトルDBから取得した参考情報 ---\n{best_match['text']}\n")
        answer = generate_llm_answer(user_query, best_match["text"])
        print(f"--- LLMによる回答 ---\n{answer}")
    else:
        print("関連情報が見つかりませんでした。")