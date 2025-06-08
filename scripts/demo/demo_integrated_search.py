#!/usr/bin/env python3
"""
ハイブリッド検索システムの統合テスト
"""

import asyncio
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# APIキー不要でテストできるように、分類サービスのモックを作成
from backend.app.models.classification_models import ClassificationResult, QueryType
from backend.app.services.database_service import DatabaseService
from backend.app.services.vector_service import VectorService

class MockClassificationService:
    """テスト用の分類サービス（APIキー不要）"""
    
    async def classify_query(self, request):
        query = request.query.lower()
        
        # 簡単なルールベース分類
        if any(keyword in query for keyword in ["hp", "100以上", "50以上", "タイプ", "炎", "水", "草"]):
            return ClassificationResult(
                query_type=QueryType.FILTERABLE,
                summary=f"フィルター検索: {request.query}",
                confidence=0.9,
                filter_keywords=self._extract_filter_keywords(query),
                search_keywords=[],
                reasoning="数値条件またはタイプ指定を検出"
            )
        elif any(keyword in query for keyword in ["強い", "おすすめ", "人気", "弱い", "使いやすい"]):
            return ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary=f"意味検索: {request.query}",
                confidence=0.8,
                filter_keywords=[],
                search_keywords=[query],
                reasoning="抽象的な評価を検出"
            )
        else:
            return ClassificationResult(
                query_type=QueryType.HYBRID,
                summary=f"ハイブリッド検索: {request.query}",
                confidence=0.7,
                filter_keywords=self._extract_filter_keywords(query),
                search_keywords=[query],
                reasoning="複合条件を検出"
            )
    
    def _extract_filter_keywords(self, query):
        keywords = []
        if "hp" in query or "100以上" in query:
            keywords.extend(["HP", "100以上"])
        if "炎" in query:
            keywords.append("炎")
        if "水" in query:
            keywords.append("水")
        if "草" in query:
            keywords.append("草")
        return keywords
    
    def determine_search_strategy(self, classification):
        from backend.app.services.classification_service import ClassificationService
        real_service = ClassificationService()
        return real_service.determine_search_strategy(classification)

async def test_hybrid_search():
    """ハイブリッド検索の統合テスト"""
    print("=== ハイブリッド検索システム統合テスト ===\n")
    
    # サービスの初期化
    classification_service = MockClassificationService()
    db_service = DatabaseService()
    
    test_cases = [
        {
            "query": "HPが100以上のポケモン",
            "description": "数値フィルター検索"
        },
        {
            "query": "炎タイプのポケモン",
            "description": "タイプフィルター検索"
        },
        {
            "query": "強いポケモンを教えて",
            "description": "意味検索"
        },
        {
            "query": "炎タイプで強いポケモン",
            "description": "ハイブリッド検索"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"テスト {i}: {description}")
        print(f"クエリ: {query}")
        print("-" * 50)
        
        try:
            # Step 1: 分類
            from backend.app.models.classification_models import ClassificationRequest
            request = ClassificationRequest(query=query)
            classification = await classification_service.classify_query(request)
            
            print(f"✅ 分類結果: {classification.query_type}")
            print(f"✅ 要約: {classification.summary}")
            print(f"✅ 信頼度: {classification.confidence}")
            print(f"✅ フィルターキーワード: {classification.filter_keywords}")
            
            # Step 2: 検索戦略
            strategy = classification_service.determine_search_strategy(classification)
            print(f"✅ 検索戦略: DB={strategy.use_db_filter}, Vector={strategy.use_vector_search}")
            
            # Step 3: データベース検索（適用される場合）
            if strategy.use_db_filter and classification.filter_keywords:
                db_results = await db_service.filter_search(classification.filter_keywords, 3)
                print(f"✅ DB検索結果: {len(db_results)}件")
                for j, item in enumerate(db_results, 1):
                    print(f"   {j}. {item.title} (スコア: {item.score:.3f})")
            else:
                print("❌ DB検索をスキップ")
            
            # Step 4: ベクトル検索は実際のAPIキーが必要なのでスキップ
            print("⏭️  ベクトル検索をスキップ（APIキー必要）")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print("=" * 60)
        print()

if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
