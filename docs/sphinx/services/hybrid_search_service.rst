ハイブリッド検索サービス
========================

.. automodule:: services.hybrid_search_service
   :members:
   :undoc-members:
   :show-inheritance:

クラス詳細
----------

.. autoclass:: services.hybrid_search_service.HybridSearchService
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

主要メソッド
------------

search()
~~~~~~~~

.. automethod:: services.hybrid_search_service.HybridSearchService.search

検索戦略の決定
~~~~~~~~~~~~~~

このサービスは以下の戦略でクエリを処理します:

1. **LLMによる分類**: クエリをGREETING, FILTERABLE, SEMANTIC, HYBRIDに分類
2. **検索戦略の選択**: 分類結果に基づいて最適な検索方法を決定
3. **並列検索実行**: データベース検索とベクトル検索を効率的に実行
4. **結果のマージ**: 品質スコアに基づいて結果を統合

使用例
------

基本的な使用方法::

    service = HybridSearchService()
    result = await service.search("HP100以上のカード", top_k=5)
    
    # 結果の確認
    print(f"分類タイプ: {result['classification'].query_type}")
    print(f"取得件数: {len(result['merged_results'])}")
    for item in result['merged_results']:
        print(f"- {item.title}: {item.score}")

複合条件での検索::

    result = await service.search("炎タイプで強いカード")
    # HYBRIDタイプとして分類され、DB検索とベクトル検索が併用される
