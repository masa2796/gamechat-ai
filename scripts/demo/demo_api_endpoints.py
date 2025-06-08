#!/usr/bin/env python3
"""
ハイブリッド検索APIエンドポイントのテスト
"""

import asyncio
import aiohttp
import json
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

async def test_search_test_endpoint():
    """新しい/rag/search-testエンドポイントをテスト"""
    print("=== ハイブリッド検索APIエンドポイントテスト ===\n")
    
    test_queries = [
        {
            "query": "HPが100以上のポケモンを教えて",
            "description": "HP数値フィルター検索"
        },
        {
            "query": "炎タイプのポケモンは？",
            "description": "タイプフィルター検索"
        },
        {
            "query": "強いポケモンを教えて",
            "description": "意味検索（ベクトル検索）"
        },
        {
            "query": "フシギダネについて教えて",
            "description": "特定ポケモンの意味検索"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"テスト {i}: {description}")
            print(f"クエリ: {query}")
            print("-" * 50)
            
            try:
                # POSTリクエストでハイブリッド検索をテスト
                payload = {
                    "query": query,
                    "top_k": 3
                }
                
                async with session.post(
                    f"{BASE_URL}/rag/search-test",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print(f"✅ ステータス: {response.status}")
                        print(f"✅ 分類タイプ: {result['classification']['query_type']}")
                        print(f"✅ 要約: {result['classification']['summary']}")
                        print(f"✅ 信頼度: {result['classification']['confidence']}")
                        print(f"✅ DB検索結果: {len(result['db_results'])}件")
                        print(f"✅ ベクトル検索結果: {len(result['vector_results'])}件")
                        print(f"✅ 最終マージ結果: {len(result['merged_results'])}件")
                        
                        if result['merged_results']:
                            print("\n📋 マージ結果の詳細:")
                            for j, item in enumerate(result['merged_results'][:2], 1):
                                print(f"  {j}. {item['title']} (スコア: {item['score']:.3f})")
                                if len(item['text']) > 100:
                                    print(f"     {item['text'][:100]}...")
                                else:
                                    print(f"     {item['text']}")
                    else:
                        error_text = await response.text()
                        print(f"❌ ステータス: {response.status}")
                        print(f"❌ エラー: {error_text}")
                
            except aiohttp.ClientConnectorError:
                print("❌ サーバーに接続できません。サーバーが起動しているか確認してください。")
                print("   起動コマンド: cd backend && uvicorn app.main:app --reload --port 8000")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")
            
            print("=" * 60)
            print()

async def test_original_rag_endpoint():
    """元の/ragエンドポイントもテスト"""
    print("=== 元のRAGエンドポイントテスト ===\n")
    
    query = "フシギダネについて教えて"
    
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "query": query,
                "top_k": 3
            }
            
            async with session.post(
                f"{BASE_URL}/rag",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"✅ ステータス: {response.status}")
                    print(f"✅ 質問: {result['question']}")
                    print(f"✅ 回答: {result['answer'][:200]}...")
                    if 'classification' in result:
                        print(f"✅ 分類情報: {result['classification']}")
                else:
                    error_text = await response.text()
                    print(f"❌ ステータス: {response.status}")
                    print(f"❌ エラー: {error_text}")
                    
        except aiohttp.ClientConnectorError:
            print("❌ サーバーに接続できません。")
        except Exception as e:
            print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("ハイブリッド検索APIのテストを開始します...")
    print("注意: このテストはサーバーが起動している必要があります。")
    print("起動コマンド: cd backend && uvicorn app.main:app --reload --port 8000\n")
    
    asyncio.run(test_search_test_endpoint())
    asyncio.run(test_original_rag_endpoint())
