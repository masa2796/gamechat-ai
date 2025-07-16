# 構造化データ検索不具合 調査ログ
## 調査日

---


## 🔍 検索精度改善のための追加調査タスク

- [ ] 1. スコア計算メソッド（_calculate_hp_score, _calculate_damage_score, _calculate_type_score, _calculate_text_score）のロジックが要件・期待仕様に合致しているか精査する
- [ ] 2. 検索キーワード（keywords）の前処理・解釈（正規化や分割）が適切か確認する
    - 調査結果: DatabaseServiceのfilterable検索では、キーワードはそのまま _match_filterable に渡されている。_match_filterable内で属性名や数値条件の判定ロジックがあるが、キーワードの正規化（例: 全角・半角変換、ひらがな・カタカナ統一、英字大文字小文字変換等）や不要な空白除去、複合条件の分割などの前処理は実装されていない。
    - クエリ分類（ClassificationService）でfilter_keywordsとsearch_keywordsに分割されるが、その後の正規化・分割処理は限定的。たとえば「コスト1以下」「エルフ」などの条件が複数ワードに分割されているか、曖昧な表現が正しくfilterable条件に変換されているかは要追加検証。
    - 改善案: キーワードの正規化・分割処理を追加し、属性名や数値条件の表記揺れ・曖昧さを吸収できるようにすることで、filterable検索の精度向上が期待できる。
- [ ] 3. data_cache内のデータ構造や値が正しく、検索条件にマッチする内容になっているか確認する
- [ ] 4. テストケースを作成し、期待する検索結果と実際の結果を比較・検証する
- [ ] 5. 必要に応じてスコア計算式や閾値、キーワードマッチ条件を調整・改善する

# 🆕 検索結果が正しくない場合の追加調査タスク

- [ ] 6. filterableクエリ時のフィルタ条件（例: クラス名・コスト等）が正しく判定されているか確認する
- [ ] 7. フィルタ条件の判定ロジック（_match_filterable等）がデータ仕様・要件に合致しているか精査する
- [ ] 8. クエリ分類（query_type判定）が正しく行われているか、filterable/semantic/hybridの判定精度を確認する
- [ ] 9. 検索結果の件数・内容が期待通りか、実データと照合して検証する
- [ ] 10. 検索APIのリクエスト・レスポンスログを確認し、パラメータや分類情報が正しく伝搬しているか調査する

## 現象
- 構造化データによる検索ができていない。

## 初期調査ポイント
- DatabaseServiceクラス内のスコア計算系メソッド（_calculate_hp_score, _calculate_damage_score, _calculate_type_score, _calculate_text_score）やデータロード部分を確認。

## 主な確認内容
- reload_data()でdata.jsonをロードし、self.data_cacheとself.title_to_dataを構築している。
- _load_data()はstorage_service.load_json_data()経由でデータを取得し、list[dict]でなければ空リストを返す。
- HP/ダメージ/タイプ/テキストの各スコア計算は個別に実装されている。
- 検索条件（keywords）に応じてスコアを計算する設計。

## 問題点の仮説
- 検索のエントリーポイントとなるメソッド（例: filter/search/structured_search等）がDatabaseService内に見当たらない。
- スコア計算メソッドは存在するが、実際にそれらを組み合わせて検索結果を返すロジックが未実装、または呼び出されていない可能性。
- _calculate_combo_bonus()はスコアを返していない（return文がない）。
- self.storage_serviceの初期化が__init__で行われていないため、_load_data()でAttributeErrorとなる可能性。


## 🔍 構造化検索不具合 調査タスク（チェックリスト）

- [x] 1. DatabaseService内に「検索」や「filter」等のpublicメソッド（エントリーポイント）が存在するか確認する
    - 調査結果: DatabaseService内には「検索」や「filter」等のpublicメソッド（例: structured_search, filter_cards, search など）は実装されていません。存在するpublicメソッドはget_card_details_by_titlesのみで、これはカード名リストから詳細データを取得する用途です。スコア計算系メソッドはすべてprivate（_calculate_...）であり、検索エントリーポイントとなるpublicメソッドは未実装です。
- [ ] 2. スコア計算メソッド（_calculate_hp_score等）がどのように使われているか、実際に呼び出されているか調査する
- [ ] 3. self.storage_serviceの初期化が__init__で正しく行われているか確認する
- [ ] 4. _calculate_combo_bonusにreturn文があるか、スコア加算が正しく行われているか確認する
- [ ] 5. 検索APIや外部（HybridSearchService, RagService, ルーター等）からDatabaseServiceの検索系メソッドがどのように呼ばれているか調査する
- [ ] 6. テストコード（test_database_service.py等）でfilter_search等のpublicメソッドがテストされているか確認する
- [ ] 7. 必要に応じて、publicメソッドや初期化処理の修正・追加を検討する

---

## 追加調査・原因まとめ（2025-07-16追記）

### 1. 検索エントリーポイントの不在
- DatabaseService内に「検索」や「filter」等のpublicメソッドが見当たらず、スコア計算系メソッドが直接使われていない。
- 構造化検索のための一括評価・フィルタ処理が未実装、または外部から呼ばれていない可能性が高い。

### 2. combo_bonusのreturn漏れ
- _calculate_combo_bonusはスコアを返すべきだが、return文がないためスコア加算が機能しない。

### 3. storage_service未初期化
- self.storage_serviceの初期化が__init__で行われていないため、_load_data実行時にAttributeErrorとなる可能性がある。

### 4. 外部呼び出し経路の確認
- 検索APIやルーター、サービス層からDatabaseServiceの検索系メソッドがどのように呼ばれているか要確認。

---

## 次のアクション（追加分）
- 検索用publicメソッド（例: structured_search, filter_cards等）の有無を再確認し、なければ新規実装を検討。
- _calculate_combo_bonusにreturn文を追加し、スコア加算が正しく行われるよう修正。
- self.storage_serviceの初期化を__init__で必ず行うよう修正。
- 検索APIや外部呼び出し元の実装・ルーティングを調査し、DatabaseServiceの利用状況を把握。
