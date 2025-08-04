データベースサービス
====================

.. automodule:: services.database_service
   :members:
   :undoc-members:
   :show-inheritance:

クラス詳細
----------

.. autoclass:: services.database_service.DatabaseService
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

主要メソッド
------------

filter_search()
~~~~~~~~~~~~~~~

.. automethod:: services.database_service.DatabaseService.filter_search

_calculate_filter_score()
~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: services.database_service.DatabaseService._calculate_filter_score

スコア計算の仕組み
------------------

データベースサービスでは、以下の要素を組み合わせてマッチスコアを計算します:

HP条件のマッチング
~~~~~~~~~~~~~~~~~~

* "HP"キーワード + 数値条件("40以上", "100以上"など)の組み合わせを検出
* 条件を満たす場合は2.0ポイントを付与

ダメージ条件のマッチング
~~~~~~~~~~~~~~~~~~~~~~~~

* "ダメージ"/"技"/"攻撃"キーワード + 数値条件の組み合わせを検出
* 技データから条件に合致するダメージ値をチェック
* 条件を満たす場合は2.0ポイントを付与

タイプマッチング
~~~~~~~~~~~~~~~~

* "炎", "水", "草"などのタイプキーワードを検出
* タイプ情報と照合
* 完全一致の場合は2.0ポイントを付与

複合条件ボーナス
~~~~~~~~~~~~~~~~

* 複数の条件が同時に満たされる場合、追加ボーナスを付与
* 例: 炎タイプ + HP100以上 → 基本4.0 + ボーナス

使用例
------

HP条件での検索::

    service = DatabaseService()
    results = await service.filter_search(["HP", "100以上"], top_k=10)
    
    for result in results:
        print(f"{result.title}: スコア {result.score}")

複合条件での検索::

    # 炎タイプでダメージ40以上の技を持つカード
    results = await service.filter_search([
        "炎", "タイプ", "ダメージ", "40以上", "技"
    ], top_k=5)
