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
  - [x] Upstash Vector へ upsert（id: 安定キー、metadata: {title, text, namespace}）。
- [x] 既存データのフル/増分インデクシング運用を README に追記。

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
- [x] `ClassificationService` のプロンプトに効果検索例を追加（「〜な効果」「〜できる」→ SEMANTIC/HYBRID）。
- [x] `HybridSearchService` の重み/しきい値を効果検索に最適化（必要なら）。
  - クエリ種別・confidence に応じてマージ重み/品質しきい値を動的化（SEMANTICはVector重視）。
- [ ] `VectorService.search()` の `min_score` と `namespaces` 最適化確認。

#### 調査: ベクトル検索の精度低下の要因（現状）
1) Namespace が広すぎてノイズが混入
   - 現状は `convert_data.json` から全 namespace を列挙し検索（`effect_*`, `qa_question` 等）。
   - 効果検索(SEMANTIC/HYBRID)でも QA 質問文が混ざり、意味空間がブレる可能性。

2) min_score とスコア集約の挙動
   - 類似度しきい値は `base_threshold * confidence_adjustment`（semantic 基準 0.75）。
   - Namespace 跨ぎで同一タイトルのスコアは最後に上書き（最大化されない）ため、最良スコアが落ちるケースあり。

3) 返却順の一貫性・ランキング品質
   - 非並列の `search()` はタイトル配列を namespace 順に詰めて返却（内部的な最終マージではスコア字典を使用しているが、単独利用やログ可視化で誤解を招く）。

4) クエリ埋め込みテキストの最適性
   - モック環境では summary=原文のままになりがちで、効果語以外（クラス語・数値語）が過度に混ざる場合がある。

5) インデックス側のノイズ
   - `qa_question` のみ取り込みで `qa_answer` 未収録（効果意図と離れる文が増える）。
   - `effect_combined`（同カードの効果文結合）が未活用で、断片 recall が不足する可能性。

#### 対策タスク（追加）
- [x] VectorService: クエリ種別に応じた namespace フィルタを実装
  - SEMANTIC/HYBRID → `effect_*`（＋あれば `effect_combined`）を優先/限定
  - FILTERABLE → 既定のまま or Vectorを補助使用
- [ ] VectorService: タイトル重複時は最大スコアを保持し、グローバルランキングで返却
  - `scores[title] = max(scores.get(title, 0), score)` に変更
  - 返却前にスコア降順で dedupe + sort（単体利用時の一貫性向上）
- [ ] EmbeddingService: 効果中心の埋め込みテキスト生成を強化
  - SEMANTIC/HYBRID 時は効果キーワードを強調し、不要な属性語/助詞を軽く正規化
  - 日本語ストップワード/単純な表記ゆれ（例: 「〜できる」「可能」）の正規化を軽量で追加
- [ ] Indexing: `qa_answer` を取り込み、`effect_combined` を追加生成（任意）
  - combined の利用は設定で切替（効果 recall が要るときに限定）
- [ ] Logging/可観測性: 検索毎に namespace 選択・上位スコア上位5件・しきい値を記録
  - 調整ループを短縮し、誤設定の早期検知に活用
- [ ] Config チューニング: `similarity_thresholds`/`confidence_adjustments` の再学習
  - サンプルクエリで Precision@K/Recall@K を測って再設定


#### 不具合報告（追加）: 特定クエリで検索結果が0件になる

現象:
- 次のクエリで検索結果が0件となる。
  - 「フィールドのカードを手札に戻すカード」
  - 「相手のリーダーにダメージを与えるカード」
  - 「ランダムな相手のフォロワーにダメージを与えるカード」

推定原因（共通）:
1) 誤字・表記ゆれ・語彙差
   - 「フィールド/盤面/ボード/場」, 「顔/フェイス/リーダー」, 「手札に戻す/バウンス/手札に返す」などの同義語未正規化。
2) 検索パラメータの厳しさ
   - `min_score` が高すぎ、Top-K が小さく、effect断片のスコアばらつきで0件に落ちやすい。
   - `effect_combined` を未活用で、断片ごとの分散が大きいクエリでRecall不足。
3) クエリ要約/埋め込みの最適性
   - LLMサマリーが効果語（動詞＋対象）に十分フォーカスせず、ノイズ語（クラス名・数値）が混入。
4) インデックス側の語彙不足
   - 原文が「手札に戻す」でも、ユーザークエリ「バウンス」を拾えない等、語彙橋渡しが不足。

解消タスク（優先度: 高）
- [☓] クエリ正規化レイヤー（展開方式: Synonym/Typo拡張）を追加（HybridSearchService 直前 or EmbeddingService）
  - 方針: 完全な置換ではなく「展開」。原語は残しつつ、同義語・表記ゆれ・タイポ候補を追加して網羅性を高める。
  - 二段構え:
    - Keyword検索（HybridSearchのキーワード側）: 正規化を強めに。各語を OR 展開して確実にヒット（例: フォロワー OR フォロー OR フォロワ）。
    - Embedding検索: 正規化は軽め。原語を主とし、代表同義語のみ少数付加（意味的吸収はEmbeddingに委ねる）。
  - 未知語は残す: マッピングに無い語は削除せず保持。
  - 語彙マップ（初版・展開セット）例:
    - 場所: [フィールド, 盤面, ボード, 場]
    - 対象: [フォロワー, フォロー, フォロワ]
    - リーダー: [リーダー, 顔, フェイス]
    - バウンス: [手札に戻す, 手札に返す, バウンス]
    - ランダム: [ランダム, 無作為]
  - 実装例:
    - 入力: 「フォロー」 → 展開: 「フォロワー OR フォロー OR フォロワ」
  - 正規化前処理: 全角/半角、長音、余分な空白の正規化（語根は保持）。
- [△] Zero-hit リトライ戦略の実装
  - 1回目: namespaces = effect_*、threshold = 既定、top_k = 10
  - 0件時に再試行: namespaces += effect_combined、threshold を -0.05〜-0.1、top_k = 20
  - それでも0件の場合、同義語展開後に再埋め込みして再検索。
- [x] VectorService のタイトル重複スコアを最大値で集約し、降順ソートで返却（dedupe強化）
- [x] EmbeddingService の要約強化（効果キーワード優先の抽出と助詞の軽正規化）
- [ ] インデクサで語彙ブースト（任意）
  - 効果カテゴリ語（例: バウンス/直接ダメージ/ランダム）を `metadata.text` 末尾に付加（軽量タグ）
  - 既存原文は保持したまま、検索時の語彙橋渡しを強化
- [x] ロギングの拡充
  - 正規化前後のクエリ、namespaces、threshold、top_k、上位5件のスコアをDEBUGで出力（`HybridSearchService` と `VectorService` に追加）
- [ ] テスト追加（失敗再現→緑化）
  - `test_hybrid_search_consolidated.py` に以下3件を追加し、Top-10が非空になること:
    - 「フィールドのカードを手札に戻すカード」
    - 「相手のリーダーにダメージを与えるカード」
    - 「ランダムな相手のフォロワーにダメージを与えるカード」


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

---

## 原因分析まとめ（2025-08-22 更新）

### 症状
- 「効果〇〇を持つカード」形式の自然言語クエリで期待カードが返らない、あるいは0件になるケースが散発。
- 特に effect_4 以降 / 複合効果を含むカードがヒットしづらいとの観測。

### 確認した主因
| 区分 | 内容 | 影響 | 優先度 |
|------|------|------|--------|
| データ/判定不整合 | `_match_filterable_llm` が効果判定で `effect_1..3` のみ走査、埋め込み/インデックス側は `effect_1..9` を取り込み | effect_4 以降テキストが検索条件にマッチせず除外 | 高 |
| Namespace 絞り込み | SEMANTIC/HYBRID 時に `effect_*` へ絞る設計。`effect_combined` 未活用時に断片分散で Recall 低下 | 0件フォールバック頻度増 | 中 |
| スコア閾値 | min_score 初期値がやや高め（0.5〜動的調整）。短文効果でスコア分布が低いケースを除外 | 有効候補が落ちる | 中 |
| 同義語未展開 | 「場/盤面/フィールド」「バウンス/手札に戻す」「リーダー/顔」など語彙差でヒット漏れ | Recall 低下 | 中 |
| 埋め込み文脈 | 効果文のみで差異情報（クラス/種別）が希薄、類似度クラスタリングで衝突 | 誤ランク or スコア低下 | 低 |

### 根本原因（最も直接的）
`database_service._match_filterable_llm` 内の効果条件ループが `['effect_1','effect_2','effect_3']` に固定され、インデックス/埋め込みで取り込んだ `effect_4` 以降がフィルタ段階で無視されていた。

### 即時対処（実装済み / 実装中）
- [x] 効果フィールド走査範囲を `effect_1..9` へ拡張。
- [x] 拡張の回帰テスト（`effect_5` のみ保有カードがマッチすることを検証）追加。
- [x] min_score チューニング（暫定: 設定値を 0.4 に設定し再評価中 | 以前: 0.5）
- [ ] 同義語軽展開（Normalization 層追加）
- [ ] `effect_combined` namespace 活用フォールバックの有効化

### 今後の改善優先度リスト
1. 同義語/表記ゆれ展開（Recall 向上）
2. スコア閾値とフォールバック段階の最適化（Precision/Recall バランス）
3. `effect_combined` の導入と適応的 namespace 戦略
4. 埋め込みテキストへの最小メタ（クラス/タイプ）付加検討
5. 評価スクリプトによるバッチ品質測定（Precision@K / Recall@K / MRR）

---

## 追加機能: ユーザー評価（Feedback）収集基盤
検索品質改善に向け、実ユーザーが AI 回答に対して「良い/悪い（または中立）」評価を送信でき、特にマイナス評価時にクエリ・回答・内部メタ情報を蓄積する仕組みを導入する。

### 目的 / ゴール
- どのクエリ・回答ペアで不満足が発生しているか可視化し、検索/分類/埋め込みの改善優先度判断材料とする。
- ネガティブ例を教師データ（失敗ケース集）として再プロンプト設計 / 同義語辞書 / 閾値チューニングに活用。
- 将来的に Online Learning / Active Evaluation（人手確認キュー）への拡張を可能にする。

### スコープ（初期）
- 評価値: `+1` (良い) / `-1` (悪い) / （任意で `0` 中立）
- マイナス評価時: 下記フィールドを保存
  - query_text, answer_text, query_type, classification_summary
  - vector_top_titles (上位N件), min_score, namespaces, top_scores(top5)
  - embedding_version / index_version（将来差分分析用）
  - user_id (任意/匿名化可), session_id, timestamp
  - client_app_version / frontend_build_hash（回帰把握）
  - optional: user_reason (自由記述最大 ~300字)
- 保存先: アプリDB（RDB）新テーブル `search_feedback`
- フロント: 回答表示領域に 👍 / 👎 ボタン（CLI / API クライアントからも送信可能）

### 非スコープ（初期段階で除外）
- 複数段階のラベル（"部分的に正しい" 等の細分類）
- 自動再検索 / リライトの即時トリガー
- 個別ユーザー嗜好学習

### データモデル案
`search_feedback` テーブル（PostgreSQL 想定）:
| 列 | 型 | 説明 |
|----|----|------|
| id | BIGSERIAL PK | |
| created_at | TIMESTAMP WITH TIME ZONE (default now) | |
| user_id | TEXT NULL | 匿名ならNULL / ハッシュ化ID |
| session_id | TEXT NULL | セッション突合せ |
| rating | SMALLINT | -1 / 0 / 1 |
| query_text | TEXT | 入力クエリ原文 |
| answer_text | TEXT | 表示したAI最終回答（要約含む） |
| query_type | TEXT | semantic / hybrid / filterable / greeting |
| classification_summary | TEXT NULL | LLM分類サマリー |
| vector_top_titles | JSONB | 上位タイトルリストとスコア [{t,s}] |
| namespaces | JSONB | 使用 namespace 配列 |
| min_score | REAL | 実際に用いた閾値 |
| top_scores | JSONB | top5スコア詳細 |
| embedding_version | TEXT NULL | 埋め込み/モデルバージョン |
| index_version | TEXT NULL | ベクトルインデックス再構築バージョン |
| user_reason | TEXT NULL | 追加フィードバック |
| processed | BOOLEAN default false | 後続分析/エクスポート済みフラグ |
| tags | JSONB NULL | 手動タグ付け ("synonym_miss", "low_recall" 等) |

インデックス案:
- `CREATE INDEX ON search_feedback (created_at);`
- `CREATE INDEX ON search_feedback (rating);`
- `CREATE INDEX ON search_feedback (query_type);`
- `GIN` インデックス for JSONB (vector_top_titles, namespaces) 需要次第。

### API エンドポイント案
| メソッド | パス | 用途 | 認可 | リクエスト例 |
|----------|------|------|------|--------------|
| POST | `/api/feedback` | 評価送信 | public (CSRF/Rate Limit) | `{ "query_id": "uuid", "query_text": "回復効果...", "answer_text": "...", "rating": -1, "user_reason": "ヒールカードが出ない", "meta": { "vector_top_titles": [...], "namespaces": ["effect_1"], "min_score": 0.4, "top_scores": [...] } }` |

バックエンド側で信頼できるフィールド（namespaces, top_scores 等）は **サーバ内部ログ/Context から再構築** し、クライアント送信の改ざんを避ける。（クライアントは最低限 query_id / rating / user_reason のみでも可）

### 実装タスク
1. モデル/マイグレーション
  - [ ] Alembic などで `search_feedback` テーブル追加
2. ドメイン層
  - [ ] `FeedbackService` (create_feedback, list_recent, aggregate_metrics)
3. ルーター
  - [ ] `routers/feedback.py` POST `/api/feedback` （バリデーション + サーバ側メタ注入）
4. フロントエンド
  - [ ] 回答コンポーネントに 👍 / 👎 ボタン配置
  - [ ] 送信後トースト表示（再投稿防止 state）
  - [ ] ネガティブ時: 任意コメント入力モーダル
5. メタ注入
  - [ ] 検索完了時に QueryContext を一時保存（in-memory LRU / Redis）: key=query_id → スコア/namespace/分類サマリ
6. ロギング/監査
  - [ ] Feedback 保存時に success ログ + 要約（rating, query_type, top1_title）
7. 可観測化 / ダッシュボード
  - [ ] Prometheus カウンタ: `feedback_total{rating,query_type}`
  - [ ] エラー率 / 保存失敗計数
8. 分析補助スクリプト
  - [ ] `scripts/data-processing/export_feedback_stats.py` (期間指定でCSV/集計 JSON 出力)
9. セキュリティ / 品質
  - [ ] Rate Limit (IP or user basis, 例: 1分10件 / 1時間100件)
  - [ ] XSS防止: user_reason をサニタイズ / HTML エスケープ
  - [ ] 個人情報禁止文言フィルタ（簡易正規表現）

### メトリクス / KPI
- ネガティブ率 (negative_feedback / total_feedback) の週次推移
- クエリタイプ別ネガティブ率 (semantic が高い場合 → 同義語 / index 改善重点)
- ネガティブ上位トークン抽出（TF-IDF / 形態素解析）→ 辞書拡張候補
- 改善施策投入前後での ネガティブ率 / Recall 減少比較

### ワークフロー（改善サイクル）
1. ネガティブ収集 (日次)
2. 集計 / 上位問題カテゴリ抽出
3. 対策（辞書追加 / 閾値調整 / インデックス拡張）
4. 再デプロイ・バージョンタグ記録 (embedding_version, index_version)
5. 翌週比較（before/after）

### リスクと緩和
| リスク | 内容 | 緩和策 |
|--------|------|--------|
| スパム | ボット大量投稿 | Rate limit + reCAPTCHA(必要時) |
| プライバシー | 自由記述に個人情報 | 簡易NGワードフィルタ + 後続監査 |
| 改ざん | クライアント改変メタ | サーバ側でメタ再構築 |
| 保存遅延 | 同期I/O によるレスポンス遅延 | 非同期タスクキュー (将来 Celery) / 先行 202 async commit |

### 受け入れ基準（Feedback 機能）
- 👎 を送信するとサーバに行が保存され、API 201 応答。
- DB に rating=-1 行が生成され、`vector_top_titles[0].title` が存在。
- 過剰投稿 (> 制限) で 429 が返る。
- user_reason に危険な HTML を含んでもサニタイズされて保存（script タグ無効化）。

### 将来拡張アイデア（後回し）
- 学習用データ自動抽出（ネガティブ例を含む Hard Negative ペア生成）
- A/B テスト: model_version / threshold バリエーションを query_id に紐づけ比較
- オンライン自動再ランキング（ネガティブ学習: pairwise ranking loss）

---

### リスクと回避
- 走査範囲拡張によりマッチ件数が過剰になる懸念: スコア/重み付け、AND 条件分解で制御。
- 同義語過展開によるノイズ増: Embedding では代表1語のみ、Keyword フィルタで広く展開する二層方式で吸収。

---
