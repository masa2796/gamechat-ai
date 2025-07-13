# 進捗まとめ（2025/07/12時点）

- 2025/07/12: 本日進捗なし。フェーズ2以降（embedding対象限定・LLM分岐・フロント対応等）は今後着手予定。
- フェーズ1: バックエンドの詳細jsonリスト返却対応（1〜5）は全て完了
    - DatabaseService/HybridSearchService/RagServiceの改修済み
    - 既存テスト（test_database_service.py, test_hybrid_search_consolidated.py, test_api.py等）も全て新仕様に修正し、全テストパスを確認
- フェーズ2以降（ベクトル検索のembedding対象限定、LLMによる検索分岐、フロントエンド対応等）は今後着手予定
- 旧仕様（title/text/score形式）は廃止、今後は詳細jsonリストのみサポート

---

# 検索結果カード名から構造化DBで詳細データを取得する仕組みへの変更案

## 概要

現状の検索（構造化DB検索・ベクトル検索・ハイブリッド検索）では、検索結果としてカード名や一部の情報のみが返却されています。
今後は、検索で得られたカード名を用いて、構造化DBから該当カードの詳細jsonデータを取得し、APIレスポンスとして返却する仕組みに変更します。

将来的には、取得したjsonデータをフロントエンドで一覧表示できるようにします。

---

## 目的

* 検索結果の情報量を増やし、ユーザー体験を向上させる
* フロントエンドでカード詳細の一覧表示や、さらなるUI拡張を可能にする

---

## フロー図

```
ユーザー入力（自然言語クエリ）
↓
LLMで検索タイプを分顛（構造化 / ベクトル / ハイブリッド）
↓
該当検索手法でカード名を取得
↓
カード名から構造化DBを検索し詳細データを取得
↓
フロントエンドで一覧表示
```

---

## 改修タスク一覧（詳細化）

### ✅ フェーズ 1: 構造化DBの詳細取得基盤（既存コード改修）

1. **構造化DB（data/data.json）をメモリにロードする処理を既存サービスへ追加**
   - 対象: `backend/app/services/database_service.py` の `DatabaseService`
     - data.jsonを読み込み、`title_to_data: dict[str, dict]` を生成・保持するロジックを追加
     - 初期化時または明示的なロードメソッドで実装
   - 必要に応じて `StorageService` も修正
   - **[済] 2025/07/10: `reload_data()` でtitle_to_data構築ロジックを追加し、テストも通過**

2. **既存のカード検索サービスを「カード名リスト返却」へ統一**
   - 対象: 
     - `DatabaseService`（構造化検索）
     - `VectorService`（ベクトル検索, `backend/app/services/vector_service.py`）
     - `HybridSearchService`（ハイブリッド, `backend/app/services/hybrid_search_service.py`）
   - 返却値を「カード名リスト（List[str]）」に統一するよう各メソッドを修正
   - 既存の `ContextItem` 返却箇所をカード名抽出に変更
   - **[済] 2025/07/10: 返却値をList[str]に統一し、ContextItem→カード名リスト化・型チェック・テスト修正も完了。integrationテストも全通過**

3. **カード名リストから詳細jsonリストを取得するメソッドを追加**
   - 対象: `DatabaseService`
     - `get_card_details_by_titles(titles: list[str]) -> list[dict]` を新規実装
   - 既存API/サービス（`HybridSearchService`や`RagService`）でこのメソッドを利用するよう改修
   - **[済] 2025/07/10: DatabaseServiceにメソッド実装、HybridSearchService/RagServiceで詳細jsonリスト返却に統一。**

4. **APIレスポンスを「詳細jsonリスト」へ変更**
   - 対象: 
     - `backend/app/routers/rag.py` の `/rag/query` エンドポイント
     - `RagService` の `process_query` など
   - 返却値を「詳細jsonリスト」に変更し、フロントエンド仕様に合わせる
   - **[済] 2025/07/10: merged_results, context などが詳細jsonリストとなるよう全サービス・APIを修正。**

5. **既存ユニットテストの修正・追加**
   - 対象: 
     - `backend/app/tests/services/test_database_service.py`
     - `backend/app/tests/services/test_hybrid_search_consolidated.py`
     - `backend/app/tests/api/test_api.py`
     - 必要に応じて他のテストも
   - 返却値の仕様変更に合わせてテストを修正
   - `get_card_details_by_titles` のテストも追加
   - **[済] 2025/07/10: すべてのテストを詳細jsonリスト仕様に修正し、全テストパスを確認。**

---

### ✅ embedding_service/vector_serviceの仕様変更に伴うテスト改修

- embedding_service, vector_serviceのAPI例外仕様変更に伴い、関連テスト（test_embedding_consolidated.py等）を修正
- APIキー未設定時の例外をEmbeddingExceptionで検証するよう修正
- 既存テストのアサーション・例外型をサービス実装に合わせて調整
- **[済] 2025/07/11: embedding_serviceのテスト修正・全テストパスを確認**

---

### ✅ フェーズ 2: ベクトル検索実装

6. **description / Q&A / flavorText のみをembedding & vector DBに登録**
   - 6.1 embedding対象フィールドの仕様整理・設計
     - ✅ description/Q&A/flavorTextのみをembedding対象とする仕様を明文化
     - ✅ data.jsonの構造確認・対象フィールドの抽出ロジック設計（effect_1〜n, qa[question/answer], flavorTextを抽出）
   - 6.2 EmbeddingServiceの改修
     - ✅ embedding生成時に対象フィールドのみ抽出する処理を追加
     - ✅ 既存のembedding生成ロジックの分岐・テスト追加
   - 6.3 VectorServiceの改修
     - ✅ ベクトルDB登録時に対象フィールドのみをembedding化
     - ✅ 既存DBの再構築・テスト追加
   - 6.4 既存embeddingデータの再生成・移行
     - ✅ 旧embeddingデータのクリア
     - ✅ 新仕様でembeddingデータを再生成

7. **類似検索からカード名を取得**
   - 7.1 類似検索ロジックの改修
     - ✅ 検索結果からカード名リストのみ返却するよう修正
     - ✅ 既存のContextItem返却箇所をカード名抽出に変更
   - 7.2 API/サービスの返却値統一
     - ✅ 類似検索APIの返却値をカード名リストに統一
     - ✅ 既存テスト（test_vector_service_consolidated.py, test_hybrid_search_consolidated.py, test_api.py等）を現仕様に修正
   - 7.3 integrationテストの追加・修正
     - ✅ embedding対象限定・カード名リスト返却仕様に合わせてintegrationテストを追加・修正
     - ✅ 全テストパスを確認

---

### ✅ フェーズ 3: LLMによる検索分顛

8. **LLMで「構造化 / ベクトル / ハイブリッド」の分顛を実装**

   - 対象: `ClassificationService`, `HybridSearchService`
   - LLMによるクエリタイプ判定・分岐ロジックの実装
   - **やるべきこと（細分化）**
     1. LLMプロンプト設計・分類基準の明文化　→　**[済] 完了**
        - どのようなクエリを「構造化」「ベクトル」「ハイブリッド」と判定するか基準を整理（ドキュメント・README等に反映済み）
        - 例: 数値条件・属性指定→構造化、曖昧/自然文→ベクトル、両方該当→ハイブリッド
     2. `ClassificationService`でのLLMプロンプト・分類ロジック実装　→　**[済] 完了**
        - クエリをLLMに投げて分類結果（query_type, summary, confidence等）を取得する処理を実装済み
        - LLMレスポンスのパース・型チェックも実装済み
     3. クエリタイプ（構造化/ベクトル/ハイブリッド）ごとの分岐ロジック実装　→　**[済] 完了**
        - `HybridSearchService`で分類結果（query_type: filterable/semantic/hybrid）に応じて検索戦略を自動切り替える分岐処理を実装済み
        - 具体方針:
            - 構造化（filterable）→ DB検索のみ実行
            - ベクトル（semantic）→ ベクトル検索のみ実行
            - ハイブリッド（hybrid）→ DB検索＋ベクトル検索を両方実行し、重複除去・優先順位付けしてマージ
        - 実装は`HybridSearchService.search()`内で分類結果を判定し、各検索サービスを呼び分ける形で実現
        - 仕様・実装内容はREADME, guides, API仕様にも反映済み
     4. 分類結果のテストケース作成　→　**[済] 完了**
        - 代表的なクエリ例ごとに分類結果が期待通りになるかユニットテストを追加
        - 境界ケース（曖昧なクエリ等）も含めて検証
     5. API/サービス全体の動作確認・テスト　→　**[済] 完了**
        - `/rag/query`等のAPIで分岐が正しく動作するかintegrationテスト
        - フロントエンドからの利用も想定した動作確認

9. **ハイブリッド検索ロジックを実装**

   - 対象: `HybridSearchService`
   - 構造化・ベクトル両検索の結果を組み合わせるロジックを実装
   - **やるべきこと（細分化）**
     1. マージ戦略の設計・仕様明文化　→　**[済] 完了**
        - DB検索・ベクトル検索の結果をどのように統合するか（重複除去、優先順位、重み付け等）を整理
        - 例: スコア加重、単純結合、クエリタイプごとの分岐など

         ---
         #### 【設計方針ログ】2025/07/13
         - ハイブリッド検索のマージ戦略は以下の観点で設計する：
           1. **重複除去**: DB検索・ベクトル検索の両方に同じカード名が含まれる場合は1件にまとめる。
           2. **優先順位・重み付け**: 
              - それぞれの検索結果に「スコア」情報がある場合は、
                - 両方に存在→スコアを加重平均または最大値/合算などで決定
                - 片方のみ→そのスコアを採用
              - スコアが無い場合は、DB検索優先やベクトル検索優先など、用途に応じてルール化
           3. **単純結合**: スコアや優先度を考慮しない場合は、単純に両リストを結合し重複を除去
           4. **クエリタイプごとの分岐**: クエリ内容や分類結果（filterable/semantic/hybrid）に応じて、
              - DB検索のみ/ベクトル検索のみ/両方の合成を切り替える
           5. **上位N件抽出**: 統合後のリストからtop_k件のみ返却（スコア順やDB優先など）
         - 実装例:
           - DB/ベクトル両方のスコアをdictで管理し、カード名をキーにマージ
           - スコアが両方にある場合は加重平均（例: DB:0.7, ベクトル:0.3）
           - スコアが無い場合はDB→ベクトルの順で採用
           - 重複カードは1件化し、スコア順でソート
         - 今後の実装・テストで最適な重みや優先度を調整予定
         ---
     2. `HybridSearchService`でのマージロジック実装　→　**[済] 完了**
        - 両検索結果を受け取り、仕様に沿ってマージするメソッドを実装
        - 既存の`_merge_results_optimized`や`_weighted_merge`等の見直し・統合
     3. マージ後の結果品質評価・フィルタリング処理の実装　→　**[済] 完了**
        - 統合後のリストから上位N件抽出や品質スコアによるフィルタリングを実装
        - 不足時の補完・提案メッセージ生成も検討
     4. 代表的なパターンのテストケース作成　→　**[済] 完了**
        - DBのみ/ベクトルのみ/両方あり/重複あり/スコア逆転等のケースで期待通りにマージされるかユニットテスト
     5. API/サービス全体の動作確認・テスト　→　**[済] 完了**
        - `/rag/query`等のAPIでハイブリッド検索が正しく動作するかintegrationテスト
        - フロントエンドからの利用も想定した動作確認

---

### ✅ フェーズ 4: フロントエンド対応

10. 返却jsonを一覧表示
   - **やるべきこと（細分化）**
     1. APIレスポンス（詳細jsonリスト）の型定義・型チェック　→　**[済] 完了**
     2. 一覧表示用のUIコンポーネント設計・実装（カード/テーブル等）
     3. 必要な項目（name, type, hp, attacks等）の表示レイアウト決定
     4. サンプルデータでのUI動作確認・調整
     5. バックエンドAPI連携・データ取得処理の実装
     6. UIテスト・表示崩れ/例外ケースの検証

11. ソート・フィルタ対応
   - **やるべきこと（細分化）**
     1. ソート・フィルタ条件（例: HP順/タイプ/名前/攻撃数等）の要件整理
     2. UI上のソート・フィルタ操作部品の設計・実装
     3. ソート・フィルタロジックの実装（フロント/バックエンドどちらで行うか検討）
     4. 条件変更時の再描画・パフォーマンス検証
     5. テストケース追加（各条件での表示確認）

12. 非同期表示の機構化
   - **やるべきこと（細分化）**
     1. ローディング/スケルトンUIの設計・実装
     2. APIリクエストの非同期化・エラーハンドリング実装
     3. 検索中/取得中/エラー時の状態管理・UI反映
     4. ページネーションや無限スクロール等のUX向上施策検討
     5. 非同期処理のテスト・例外ケース検証

---

## API仕様（現状と変更点まとめ）

### 1. 既存API仕様（2025/07/10時点）

#### `/rag/query`（POST）
- 概要: RAG検索（構造化/ベクトル/ハイブリッド）
- リクエストボディ例:
```json
{
  "question": "HP100以上のカード",
  "top_k": 10,
  "with_context": true,
  "recaptchaToken": "..."
}
```
- レスポンス例（従来）:
```json
{
  "answer": "HP100以上のカードは...",
  "context": [
    { "title": "リザードン", "text": "HP:120...", "score": 4.0 },
    { "title": "カメックス", "text": "HP:110...", "score": 3.8 }
  ],
  "classification": { ... },
  "search_info": { ... },
  "performance": { ... }
}
```
- 備考: context配列は「カード名＋一部テキスト」のみ返却

---

### 2. 今回の主な変更点

- 検索で得られた「カード名リスト」から、構造化DB（data/data.json）で詳細データ（json）を取得し、APIレスポンスとして返却
- context配列が「カード詳細jsonリスト」に拡張される
- フロントエンドでそのまま詳細一覧表示が可能に

#### 変更後のレスポンス例
```json
{
  "answer": "HP100以上のカードは...",
  "context": [
    {
      "name": "リザードン",
      "hp": 120,
      "type": "炎",
      "attacks": [...],
      ... // data.jsonの1件分
    },
    {
      "name": "カメックス",
      "hp": 110,
      "type": "水",
      ...
    }
  ],
  "classification": { ... },
  "search_info": { ... },
  "performance": { ... }
}
```
- context配列が「カード詳細jsonリスト」になる点が最大の違い
- 既存のtitle/text/score形式は廃止し、data.jsonの1件分（dict）をそのまま返却

---

### 3. 仕様比較表

| 項目         | 変更前（従来）         | 変更後（本改修）         |
|--------------|------------------------|--------------------------|
| context型    | List[ContextItem]      | List[dict]（詳細json）   |
| context内容  | title, text, score     | data.jsonの1件分         |
| 検索フロー   | 検索→カード名返却      | 検索→カード名→詳細取得   |
| フロント表示 | 一部情報のみ           | 詳細一覧表示が容易        |

---

### 4. 参考: 主要エンドポイント

- `/rag/query` : RAG検索（今回の詳細返却対応）
- `/rag/search-test` : ハイブリッド検索テスト用
- `/chat` : チャット形式（RAG検索ラップ）

---

### 5. 今後の注意点
- 既存のAPI利用クライアントは、contextの型変更に注意
- テスト・フロントエンドも新仕様に合わせて修正が必要
- 旧仕様（title/text/score）での利用は非推奨

---

## API仕様（詳細jsonリスト返却例）

#### `/rag/query`（POST, 2025/07/10以降）
- 概要: RAG検索（構造化/ベクトル/ハイブリッド）
- レスポンス例（抜粋）:
```json
{
  "answer": "...",
  "context": [
    {"name": "ピカチュウ", "type": "電気", "hp": 60, ...},
    {"name": "リザードン", "type": "炎", "hp": 120, ...},
    ...
  ],
  "classification": { ... },
  "search_info": { ... },
  "performance": { ... }
}
```