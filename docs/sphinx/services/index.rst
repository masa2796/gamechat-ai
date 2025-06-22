サービス層API
=============

GameChat AIのサービス層には、各機能を担当する専門的なサービスクラスが配置されています。

.. toctree::
   :maxdepth: 2

   hybrid_search_service
   classification_service
   database_service
   vector_service
   embedding_service
   llm_service
   rag_service

概要
----

各サービスは単一責任の原則に基づいて設計されており、以下のような役割分担となっています:

* **HybridSearchService**: 統合検索の制御とコーディネート
* **ClassificationService**: LLMによるクエリ分類と要約
* **DatabaseService**: 構造化データに対するフィルタ検索
* **VectorService**: Upstash Vectorを使用したセマンティック検索
* **EmbeddingService**: OpenAI APIによる埋め込み生成
* **LLMService**: OpenAI GPTによる回答生成
* **RagService**: RAGシステム全体の統合制御
