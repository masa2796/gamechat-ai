# Issue: カード効果のベクトル検索（LLM活用）

## 目的
- 「〇〇な効果を持つカード」「〇〇ができるカード」といった曖昧/自然言語の問い合わせに対し、DBの厳密一致・数値条件では拾い切れないカードを検索し、カード名を上位N件で返す。
- LLMでクエリ意図を分類・要約し、ベクトル検索（Upstash Vector）とDB検索をハイブリッドに活用して高再現・高精度を両立。

## 背景/課題
- 現状のDBフィルタ検索は数値・明示的属性には強い一方、「〜できる/〜のような効果」などの抽象/同義表現には弱い。
- 既存コードにベクトル検索（`VectorService`）とハイブリッド検索（`HybridSearchService`）があり、効果文抽出（`extract_embedding_text`）も実装済みだが、カード効果の自然言語検索を主目的とした要件定義・評価・データ整備が不十分。

## 現状調査（抜粋）
- Vector 検索:
  - `backend/app/services/vector_service.py` に Upstash Vector 連携、`extract_embedding_text()` にて `effect_1..n`/`qa`/`flavorText` から埋め込み対象テキストを抽出。
  - `search()`/`search_parallel()` は `metadata.title` をカード名として返却。`convert_data.json` から `namespace` を動的列挙。
- ハイブリッド統合:
  - `backend/app/services/hybrid_search_service.py` が LLM分類→DB/Vector→マージを実施。結果はカード名ベースでマージ、DB詳細は `get_card_details_by_titles()` で取得。
- LLM分類:
  - `ClassificationService` が `FILTERABLE / SEMANTIC / HYBRID / GREETING` を返す。効果系の曖昧クエリは `SEMANTIC` または `HYBRID` に振り分け想定。

結論: 実装の骨格は存在。効果検索特化の精度向上・データ整備・テスト・評価指標の整備が本Issueの主眼。

## スコープ/成果物
- 自然言語（主に日本語）での効果説明クエリに対し、上位N件の「カード名」リストを返却。
- ハイブリッド検索により、必要に応じてDB結果も補完（ただし本Issueの主対象は効果テキストの意味検索）。
- 最低限の提案メッセージ/フォールバック（結果0件時）。

## 成功指標（Acceptance Criteria）
- 検索例（日本語）で意図通りのカード名が上位に出ること。
  - 例: 「継続ダメージを与えるカード」「守護を無視して攻撃できるカード」「ドローできるカード」
- Top-K の初期値 10（調整可）。上位に関連性の高いカードが並ぶ。0件時に提案文を返せる。
- 既存の `pytest` が全て通過し、追加テストが合格。検索レイテンシの劣化が±10%以内。

## 要件（機能仕様）
- 入力: 自然言語のクエリ文字列（日本語/一部英語混在を許容）。
- 出力: 関連カード名のリスト（長さ ≤ Top-K）、および（検索情報/品質）メタ。
- 同義語・言い換え対応: ベクトル検索を前提に、LLM要約でノイズを軽減。
- 名前空間（`namespace`）はデータに応じ自動選択。設定でフィルタ/固定も可能。
- しきい値（`min_score`）により低スコア候補を除外（既定は `settings.VECTOR_SEARCH_CONFIG`）。

## 設計方針
- 埋め込み/インデックス
  - 利用データ: `data/convert_data.json`（効果文・QA・フレーバーを `extract_embedding_text()` で統合）。
  - Upstash Vector の `metadata` には `title`（カード名）, `text`（効果等全文）, `namespace` を格納。
  - 既存の `EmbeddingService` を使用（分類結果に応じたクエリ要約→埋め込み）。
- 検索/統合
  - `HybridSearchService.search()` で、分類結果 `SEMANTIC/HYBRID` 時に `VectorService.search()` を必須実行。
  - マージは既存の加重/優先度ロジックを流用。最終的にカード名リスト→詳細取得（FILTERABLE時はDB全件、その他は上位のみ）。
- LLM分類
  - 「〜な効果」「〜できるカード」「（抽象目的）」等のパターンを SEMANTIC 寄りに分類するようプロンプトを強化。
- 品質と安全
  - `min_score`・`top_k`・`namespaces` の最適化（既存の `_optimize_search_params` を活用）。
  - タイムアウト・例外は既存のハンドラでログ化しフォールバック。

## 実装タスク

### Phase 0: 仕様確定・データ確認（0.5日）
- [x] 検索サンプルの合意（10〜20例）。
- [x] `convert_data.json` の効果テキスト充足度確認、欠落フィールドの洗い出し。

補足（合意内容）
- 検索サンプルセット（16例・日本語、効果表現中心）
  - 継続ダメージを与えるカード（バーン/DoT）
  - 守護を無視して攻撃できるカード（守護貫通/守護無視）
  - 手札をドローできるカード（1ドロー/2ドロー含む）
  - 味方全体を強化する効果を持つカード（全体バフ）
  - 相手リーダーに直接ダメージを与えるカード（顔打点）
  - 相手のフォロワーを破壊するカード（単体除去）
  - 盤面のフォロワー全体にダメージを与えるカード（全体除去/AoE）
  - 疾走を持つカード
  - 守護を付与するカード（自分/味方に守護付与）
  - ラストワードでトークン/カードを手札に加えるカード
  - 進化時にトークンを出すカード
  - デッキからカードを引く/サーチするカード
  - 手札を捨てる/入れ替える効果を持つカード（ディスカード）
  - コストを下げる/軽減する効果を持つカード（コスト軽減）
  - カウントダウンを進めるカード（カウント-1等）
  - 守護を失わせるカード（相手の守護剥がし）

- `convert_data.json` 充足度チェック（現状）
  - 総件数: 398
  - namespace 内訳: effect_1=198, effect_2=118, effect_3=25, effect_4=3, effect_5=1, qa_question=53
  - 確認できた欠落/不足:
    - qa の「answer」が未収録（qa_question のみ）
    - flavorText が未収録
    - title（カード名）が未収録（id の先頭カードIDから data.json 連結で補完予定）
    - effect_4 以降のカバレッジが希薄（長文効果の取りこぼしリスク）
  - 影響/対応:
    - 埋め込み抽出は `effect_1..n`/`qa(question,answer)`/`flavorText` を想定しているため、index時に data.json と結合し、
      - title を metadata.title に補完
      - qa.answer を取り込み
      - flavorText が将来追加される場合も取り込み
    - effect_n は存在する鍵のみ収集（n 上限は現状 5 まで観測、柔軟に 9 まで許容）

### Phase 1: データ抽出・インデクシング（1-2日）
- [x] インデクサ（スクリプト）作成: `scripts/data-processing/index_effects_to_vector.py`
  - [x] `extract_embedding_text()` と同等の抽出で `text` を構築。
  - [ ] Upstash Vector へ upsert（id: 安定キー、metadata: {title, text, namespace}）。
- [ ] 既存データのフル/増分インデクシング運用を README に追記。

出力仕様（index_effects_to_vector.py）
- アウトプット先
  - Primary: Upstash Vector インデックス（REST 経由で upsert）
  - Secondary: 監査用JSONL（ローカル）`data/vector_index_effects.jsonl`（任意、dry-run/差分確認に利用）

- Upsertレコード仕様（1行=1レコード）
  - id: `{card_id}:{source_key}`（例: `10122110:effect_1`, `10012110:qa_answer_1`, `10001120:flavorText`）
  - vector: 埋め込みベクトル（EmbeddingServiceで生成）
  - metadata:
    - title: カード名（`data.json.name`）
    - text: 埋め込み対象テキスト（下記ルールで構築）
    - namespace: `effect_1|effect_2|effect_3|...|qa_question|qa_answer|flavorText`
    - card_id: `data.json.id`
    - source: `effect|qa|flavor|combined` の別（任意、デバッグ用）

- テキスト構築ルール
  - 基本: `EmbeddingService.extract_embedding_text(card)` と同等（effect_1..n, qa.question/qa.answer, flavorText を連結）
  - グラニュラリティ: convert_data.json の namespace と整合させるため、以下の2系統を生成
    1) フラグメント単位（effect_i / qa_question / qa_answer / flavorText）: 各フラグメントの原文を text に設定
    2) 併せて「combined」1件（namespace=`effect_combined`）: 同カード内の全テキストを結合（Recall向上）。
       - 既存の `VectorService._get_all_namespaces()` は convert_data.json を参照するため、combined を利用する場合は将来の最適化対象。
  - テキスト正規化: 不要な全角/半角混在・重複空白・引用符の統一、改行で段落分割。

- 監査用JSONLの1行例（抜粋）
  - `{ "id": "10122110:effect_2", "namespace": "effect_2", "title": "統率のルミナスナイト", "text_len": 28, "upserted": true, "ts": "2025-08-17T09:00:00Z" }`

- 増分更新ポリシー
  - upsert id は安定キーを使用（同一 id は内容変化時のみ差し替え）
  - `--dry-run` でUpstash送信せず監査用JSONLのみ出力
  - 実行後に namespace/件数サマリを標準出力へ（差分の可視化）

- 失敗時の扱い
  - Upstash API 失敗: リトライ（指数バックオフ、最大3回）、最終失敗は監査JSONLに `upserted=false` 記録
  - テキスト空/欠落: スキップし、監査JSONLに `skipped_reason` を記録

### Phase 2: 検索統合/最適化（1-2日）
- [ ] `ClassificationService` のプロンプトに効果検索例を追加（「〜な効果」「〜できる」→ SEMANTIC/HYBRID）。
- [ ] `HybridSearchService` の重み/しきい値を効果検索に最適化（必要なら）。
- [ ] `VectorService.search()` の `min_score` と `namespaces` 最適化確認。

### Phase 3: API/挙動（0.5-1日）
- [ ] 既存 RAG/検索エンドポイントの応答に「カード名上位N件」を含める整合性確認（後方互換）。
- [ ] 結果0件時の提案文（既存 `_generate_search_suggestion`）を効果検索向けに見直し。

### Phase 4: テスト/検証（1-2日）
- [ ] ユニット: `test_vector_service_*` を拡充（最小モックで効果文クエリ→タイトル返却）。
- [ ] 統合: `test_hybrid_search_consolidated.py` に効果検索シナリオを追加。
- [ ] 回帰: 既存 FILTERABLE（数値/集約）テストがパスすることを確認。

### Phase 5: 監視/運用（0.5日）
- [ ] 検索ログ（クエリ種別、namespaces、top_k、min_score、件数、最高スコア）を可観測化。
- [ ] タイムアウト/エラー時のフォールバック動作を明文化。

### Phase 6: ドキュメント（0.5日）
- [ ] `docs/guides/hybrid_search_guide.md` 更新（効果検索の使い方/サンプル）。
- [ ] 運用手順（インデックス再構築、環境変数、制限事項）。

## スケジュール/工数目安
- 合計: 3〜6日（並行作業により短縮可）
  - 仕様/データ確認 0.5日
  - インデクシング 1-2日
  - 統合/最適化 1-2日
  - テスト/監視/ドキュメント 1-1.5日

## 影響範囲
- 既存ファイル
  - `backend/app/services/vector_service.py`（検索/最適化パラメータ）
  - `backend/app/services/hybrid_search_service.py`（マージ/提案/詳細取得）
  - `backend/app/services/classification_service.py`（プロンプト強化）
  - `backend/app/tests/services/*`（テスト追加）
- 新規（想定）
  - `scripts/data-processing/index_effects_to_vector.py`（インデクサ）
  - `docs/guides/hybrid_search_guide.md`（更新）

## リスクと対応
- 効果文のデータ欠落/ノイズ: インデクサでフィルタ・正規化、空レコードをスキップ。
- コスト/レイテンシ: `top_k`/`min_score`/`namespaces` の最適化とタイムアウト制御、キャッシュ検討。
- 過学習/LLMバイアス: テストサンプルを多様化、プロンプトの曖昧性回避を反復調整。

## サンプルクエリ
- 「バーンダメージを与えるカード」
- 「守護を無視して攻撃できるカード」
- 「手札をドローできるカード」
- 「味方全体を強化する効果を持つカード」

## 受け入れテスト（抜粋）
- 上記クエリで、期待する代表的カード3件以上がTop-10に含まれる。
- 0件時に提案文が返り、UIで提示可能。
- 既存 FILTERABLE/集約検索は回帰しない（関連テスト全通過）。

## 参照
- 既存実装: `VectorService`, `HybridSearchService`, `extract_embedding_text()`
- 環境変数例: `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`, `BACKEND_EMBEDDING_FILE_PATH`
- 関連: `docs/guides/hybrid_search_guide.md`（要更新）, `docs/sphinx_docs/services/database_service.rst`

---

## 未確定事項/質問
1. Top-K の既定値（提案: 10）と最大値の上限は？
2. 対応言語は日本語優先でよいか（英語同義も許容？）
3. 既存 Upstash Vector インデックスの再構築可否と運用フロー（自動/手動）
4. 代表的な「正解カード」リスト（ドメイン知識）を提供可能か（精度検証用）
5. フロント表示はカード名のみでOKか（スコア/簡易説明の同時表示は必要？）
