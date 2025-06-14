GameChat AI ドキュメント
=======================

AIチャット型ゲーム攻略アシスタントの技術ドキュメント

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   services/index
   models/index
   core/index
   api/index

概要
----

GameChat AIは、カードゲームなどのカードゲーム攻略をサポートするAIアシスタントです。
ハイブリッド検索システム（データベース検索 + ベクトル検索）とLLMを組み合わせて、
ユーザーの質問に対して的確な回答を提供します。

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
