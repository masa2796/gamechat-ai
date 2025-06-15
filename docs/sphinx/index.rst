GameChat AI ドキュメント
========================

AIチャット型ゲーム攻略アシスタントの包括的技術ドキュメント

.. toctree::
   :maxdepth: 3
   :caption: メインコンテンツ:

   services/index
   models/index
   core/index
   api/index
   deployment/index

.. toctree::
   :maxdepth: 2
   :caption: 開発者ガイド:

   guides/development
   guides/testing
   guides/deployment

概要
----

GameChat AIは、カードゲームなどの戦略ゲーム攻略をサポートする高度なAIアシスタントです。
最新のRAG（Retrieval-Augmented Generation）技術を用いて、ハイブリッド検索システム（データベース検索 + ベクトル検索）とLLMを組み合わせ、
ユーザーの質問に対して正確で実用的な回答を提供します。

技術的特徴
----------

**アーキテクチャ設計**
  * マイクロサービス指向の設計
  * 非同期処理による高性能
  * スケーラブルなベクトル検索基盤
  * 本番環境対応のセキュリティ設計

**AI・ML技術**
  * OpenAI GPT-4を活用した自然言語処理
  * Sentence-BERTによる高精度な意味ベクトル化
  * 動的な検索戦略選択アルゴリズム
  * コンテキスト品質評価システム

**パフォーマンス最適化**
  * 挨拶検出による早期応答（87%の応答時間短縮）
  * 分類ベース検索最適化
  * 適応的な検索パラメータ調整
  * 効率的なデータキャッシュ戦略

主要機能
--------

* **分類ベース検索最適化**: LLMによるクエリ分類で最適な検索戦略を選択
* **ハイブリッド検索**: 構造化データ検索とセマンティック検索の組み合わせ
* **動的応答生成**: コンテキスト品質に基づく回答戦略の調整
* **挨拶検出**: 早期応答による高速化（87%の応答時間短縮）

アーキテクチャ
--------------

システムは以下の主要コンポーネントで構成されています:

1. **分類サービス** (:py:class:`~services.classification_service.ClassificationService`)
2. **データベースサービス** (:py:class:`~services.database_service.DatabaseService`)
3. **ベクトルサービス** (:py:class:`~services.vector_service.VectorService`)
4. **埋め込みサービス** (:py:class:`~services.embedding_service.EmbeddingService`)
5. **LLMサービス** (:py:class:`~services.llm_service.LLMService`)
6. **ハイブリッド検索サービス** (:py:class:`~services.hybrid_search_service.HybridSearchService`)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
