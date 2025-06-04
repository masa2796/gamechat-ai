from typing import List
from upstash_vector import Index
from app.models.rag_models import ContextItem
import os
from dotenv import load_dotenv
load_dotenv()

class VectorService:
    def __init__(self):
        upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
        upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        self.vector_index = Index(url=upstash_url, token=upstash_token)
    
    async def search(self, query_embedding: List[float], top_k: int = 3, namespaces: List[str] = None) -> List[ContextItem]:
        try:
            if namespaces is None:
                namespaces = [
                    "summary", "flavor", "attacks", "height", "weight", "evolves",
                    "hp", "weakness", "type", "set-info", "releaseDate", "category", "rarity"
                ]
            
            all_results = []
            print("=== ベクトル検索開始 ===")
            print(f"検索対象ネームスペース: {namespaces}")
            print(f"クエリベクトル次元数: {len(query_embedding)}")
            print(f"クエリベクトル先頭5要素: {query_embedding[:5]}")
            
            for namespace in namespaces:
                try:
                    print(f"\n--- Namespace: {namespace} での検索中 ---")
                    results = self.vector_index.query(
                        vector=query_embedding,
                        top_k=top_k,
                        namespace=namespace,
                        include_metadata=True,
                        include_vectors=True
                    )
                    
                    matches = results.matches if hasattr(results, "matches") else results
                    print(f"  検索結果件数: {len(matches)}")
                    
                    for i, match in enumerate(matches):
                        score = getattr(match, 'score', None) or float(match.score) if hasattr(match, 'score') else 0
                        meta = getattr(match, 'metadata', None)
                        text = meta.get('text') if meta else getattr(match, 'text', None)
                        title = meta.get('title', f"{namespace} - 情報") if meta else f"{namespace} - 情報"
                        
                        print(f"    [{i+1}] ID: {getattr(match, 'id', 'N/A')}")
                        print(f"        Score: {score:.4f}")
                        print(f"        Title: {title}")
                        print(f"        Text: {text[:100] if text else 'N/A'}{'...' if text and len(text) > 100 else ''}")
                        
                        if text:
                            all_results.append({
                                "title": title,
                                "text": text,
                                "score": score,
                                "namespace": namespace,
                                "id": getattr(match, 'id', None)
                            })
                            
                except Exception as ns_error:
                    print(f"  ❌ Namespace {namespace} での検索エラー: {ns_error}")
                    continue
            
            print("\n=== 全体検索結果サマリー ===")
            print(f"総ヒット件数: {len(all_results)}")
            
            if all_results:
                all_results.sort(key=lambda x: x["score"] or 0, reverse=True)
                
                print(f"トップ{min(top_k, len(all_results))}件:")
                for i, result in enumerate(all_results[:top_k]):
                    print(f"  {i+1}. [{result['namespace']}] {result['title']} (Score: {result['score']:.4f})")                
                best_match = max(all_results, key=lambda x: x["score"] or 0)
                print(f"\n最高スコア: {best_match['score']:.4f} (namespace: {best_match['namespace']})")
                
                return [
                    ContextItem(
                        title=result["title"],
                        text=result["text"],
                        score=result["score"]
                    )
                    for result in all_results[:top_k]
                ]
            else:
                print("❌ 検索結果なし - ダミーデータを返却")
                return [
                    ContextItem(
                        title="カード解説 - フシギダネ",
                        text="フシギダネは草タイプのたねポケモンです...",
                        score=0.95
                    )
                ]
            
        except Exception as e:
            print(f"❌ ベクトル検索エラー: {e}")
            return [
                ContextItem(
                    title="カード解説 - フシギダネ",
                    text="フシギダネは草タイプのたねポケモンです...",
                    score=0.95
                )
            ]