# GameChat AI 検索システム：ユーザークエリからDB検索までの流れまとめ

## 1. システム全体フロー
- ユーザーがチャットでクエリを送信
- API（例: `/rag/search-test`）でクエリを受信
- クエリ分類・検索戦略決定 → DB/ベクトル/ハイブリッド検索
- 検索結果を統合し、最終回答を生成
- APIレスポンスとして返却

## 2. 検索タイプの自動分類
- **LLM（GPT-4等）**がクエリを自動分類
    - FILTERABLE（構造化DB検索）
    - SEMANTIC（ベクトル検索）
    - HYBRID（両方並列）

## 3. 構造化DB検索の流れ
- API受信
    - `/rag/search-test` などのエンドポイントでクエリを受信
- ハイブリッド検索サービス
    - `search()`でクエリ分類 → 検索戦略決定
- クエリ分類サービス
    - `classify_query()`でクエリタイプ判定
- DB検索サービス
    - `filter_search()` などが呼ばれる
    - `data_cache`（`data.json`等）を走査し、キーワードごとに`_match_filterable()`で条件判定
    - スコア計算系メソッド（`_calculate_hp_score`, `_calculate_damage_score`, `_calculate_type_score`, `_calculate_text_score`）で条件マッチを判定
    - マッチしたデータを返却
- 結果マージ・回答生成
    - 検索結果を統合し、最終回答を生成
    - APIレスポンス返却

## 4. 主要関数の呼び出し関係（DB検索）
- `filter_search()`（public, 非同期/同期両対応）
    - → `filter_search_titles_async()`（asyncラッパー）
    - → `_filter_search_titles()`（実体）
    - → `_match_filterable()`（各itemとキーワードのマッチ判定）
    - → `_normalize_keyword()`（前処理）
    - → `_split_keywords()`（分割処理）
- `_search_filterable()`（詳細な条件検索・デバッグ用出力あり）
    - → `_match_filterable()`（属性・数値条件判定）
    - スコア計算は `_calculate_hp_score` などで個別に実装

## 5. データの流れ（例）
- ユーザー：「コスト1のカードを出力」
- クエリ分類：FILTERABLE
- DB検索サービスで `filter_search()` → `_match_filterable()` で「コスト1」条件判定
- マッチしたカード名リスト or 詳細データを返却

## 6. 参考ドキュメント
- `hybrid_search_guide.md`
- `search_flow_diagram.md`
- `structured_search_investigation.md`
- `database_service.rst`

## 備考
- 検索条件の正規化・分割処理は限定的。表記揺れや曖昧な条件はヒットしない場合があるため、今後の改善ポイント。
- デバッグ時は`_search_filterable()`のprint出力で内部状態を確認可能。
- 検索エントリーポイントは`filter_search()`または`_search_filterable()`。
