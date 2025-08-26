# Issue: カード効果のベクトル検索（LLM活用）

## 再整理タスクプラン（2025-08-25 時点）
本Issue内で重複/分散していたタスクを粒度と優先度で再編成。現状完了済みは Done、着手中は In Progress、直近着手予定は Next、以降は Backlog/Future に分類。

### 1. ゴール / 成功条件（再掲簡略）
1) 日本語効果クエリで Top-10 に関連カード複数出現 (Precision/Recall 指標確立)  
2) zero-hit rate と negative feedback rate を計測し 0件率を段階的に低下  
3) 回帰（既存 pytest）維持 & レイテンシ劣化 ±10% 以内

### 2. ステータスサマリ
| 区分 | 件数 | 備考 |
|------|------|------|
| Done | 多数(+2) | 追加: Zero-hit 回帰テスト(3クエリ) / 精度バッチ評価スクリプト初版 |
| In Progress | 2 | min_score 最適化検証, synonym Precision 影響測定 |
| Next | 3 | Stage3 再試行 / KPIベースライン確定 / ガイド更新 |
| Backlog | 6 | Embedding 強化 / 自動タグ付け 等 |
| Future | 4 | 再ランキング / Hard Negative / アラート |

### 3. 完了 (Done)
- インデクサ作成 + `qa_answer` / `effect_combined` 生成（現在デフォルト combined 有効、`--no-combined` で無効化）
- VectorService: クエリ種別毎 namespace 最適化 (`effect_*` 優先, `effect_combined` 先頭)
- VectorService: タイトル最大スコア集約 & 降順ソート（ランキング一貫性）
- フォールバック実装（2段階）: Stage1 / Stage2 (`effect_combined` 追加, min_score -0.05, top_k拡張)
- 同義語/表記ゆれ軽量展開レイヤー（Embedding: 代表語+原文, DB Keyword: OR 展開）
- 構造化検索ログ (`SEARCH_EVENT`) + top5 スコア出力
- Prometheus カウンタ: feedback / zero_hit
- 効果フィールド走査範囲拡張 (`effect_1..9`) + 回帰テスト
- `min_score` 暫定チューニング (0.4 ベース) / 動的調整ロジック維持
- Zero-hit 回帰テスト (過去 0件 3 クエリ) 追加: `test_hybrid_search_consolidated.py` にパラメトリック実装
- 精度バッチ評価スクリプト初版: `scripts/data-processing/eval_precision_batch.py` + ラベル雛形 `data/eval/relevance_labels.json`
  - 現状: relevant 未入力のため KPI ベースライン数値は未確定（P@10/Recall@10=0.0 仕様上）。

### 4. 進行中 (In Progress)
1. `VectorService.search()` 実測ログを用いた min_score / retry 効果分析（0件率ベースライン確定）
2. 同義語展開の Precision 影響観測 (negative_feedback トークン頻度抽出)

### 5. 直近着手 (Next)
1. 0件再試行 Stage3 実装: synonym 再埋め込み + feature flag (`ENABLE_VECTOR_STAGE3`) + ログ差分 (expanded_terms)
2. KPI ベースライン確定: `data/eval/relevance_labels.json` へ relevant タイトル入力 → `--real` 実行で初回 P@10 / Recall@10 / MRR 算出 & ドキュメント更新
3. ガイド更新: `docs/guides/hybrid_search_guide.md` に retry 段階 (Stage0/1/2), synonym 展開, 評価スクリプト利用手順追記
4. （オプション）評価スクリプト改善: Zero-hit 行抽出 / relevant 未設定クエリの除外オプション (`--skip-unlabeled`) 追加検討

### 6. Backlog（優先度 中）
1. EmbeddingService 軽量正規化強化（助詞/ストップワード削減, 代表動詞強調）
2. インデクサ語彙ブースト（メタタグ付加: バウンス / ランダム / 直接ダメージ など）
3. similarity_thresholds / confidence_adjustments 再学習 (精度バッチ結果反映)
4. Feedback 自動タグ付け (synonym_miss / low_recall / low_score) 初版
5. export_feedback_stats.py 正式版 (期間集計 + トークン頻度)
6. QueryContext 永続化 (インメモリ→Redis) によるセッション跨ぎ分析

### 7. Future（高度化 / 後段）
1. Hard Negative 利用再ランキング (pairwise heuristic)
2. Keyword + Embedding 複合再スコアリング (軽量 BM25 boost)
3. ネガティブ率移動平均監視 & アラート (Prometheus + Alertmanager)
4. A/B テスト基盤 (model_version / threshold バリエーション)

### 8. 指標 (Metrics) 初期セット
| Metric | 目的 | 計算 | 目標 (初期) |
|--------|------|------|-------------|
| zero_hit_rate | Recall 監視 | zero_hit_total / total_queries | < 15% → < 8% |
| negative_rate | 体感品質 | neg_feedback / all_feedback | 改善毎 -10% 相対 |
| P@10 | Precision | relevant@10 / 10 | ベースライン測定後 +5pp |
| Recall@10 | Recall | relevant@10 / total_relevant | +5pp 継続改善 |
| MRR | ランキング品質 | 1/rank_first_relevant | 上昇傾向維持 |

### 9. リスク & 緩和（現行追加観点）
| リスク | 影響 | 緩和 |
|--------|------|------|
| combined 長文優遇 | Precision 低下 | Stage>1 限定 + スコア差分監視 |
| synonym ノイズ | 誤マッチ増 | 展開グループ最小化 + neg率上昇時ロールバック |
| 閾値過剰引下げ | 低品質混入 | 段階的 -0.05 上限 / zero-hit 改善率が閾値 | 
| インデックス肥大 | コスト増 | combined 1件/カード固定 + 冗長タグ実験的導入後評価 |

﻿# Issue: カード効果ベクトル検索最適化（LLM活用）

最終更新: 2025-08-25

本ドキュメントは肥大化した旧 Issue メモを再編し、意思決定と日次運用に必要な最小限の共通認識・優先課題・計測指標を即座に把握できる形へ整理したものです。旧詳細は末尾 Appendix に残し必要時のみ参照します。

---
## 1. ゴール / 成功条件（要約）
1. 日本語の曖昧な効果クエリで Top-10 に関連カード複数（≥3件）を安定表示。
2. zero_hit_rate を <15% → 継続改善で <8% へ段階的低下。
3. negative_rate（ユーザーフィードバック）を施策毎に相対 -10% 以上改善。
4. 既存 pytest 回帰維持 & 検索レイテンシ劣化 ±10% 以内。

---
## 2. 現況ステータス（サマリ）
| 区分 | 状態 | 主内容 |
|------|------|--------|
| Done | ✅ | インデクサ / effect_combined / synonym 軽展開 / structured log / metrics counter / score 集約 / effect_1..9 拡張 |
| In Progress | 🔄 | min_score & retry 効果分析 / synonym Precision 影響測定 |
| Next | ⏭ | 追加 0件回帰テスト / 精度バッチ(P@10,Recall@10,MRR) / Stage3 再試行設計 / ガイド更新 |
| Backlog | 📌 | Embedding 正規化強化 / 自動タグ付け / threshold 再学習 ほか |
| Future | 🧪 | 再ランキング / Hard Negative / Alerting / A/B |

---
## 3. 直近 7 日で必須の優先タスク（集中リスト）
1. Retry Stage3 試験フラグ（synonym 再埋め込み）実装 & ログ計測。
2. ラベル整備: 16 クエリの relevant カード集合作成（ドメイン監修可）→ ベースライン一括計測。
3. ガイド更新 + KPI 表へ初回ベースライン数値挿入。

（完了定義: Stage3 実装 + ベースライン数値反映 + ガイド更新）

---
## 4. 現行アーキ要点（最小説明）
- Index: `index_effects_to_vector.py` が effect_i / qa_question / qa_answer / flavorText / effect_combined を Upstash Vector へ upsert。
- Query Flow: クエリ分類 (ClassificationService) → HybridSearchService (DB + Vector) → VectorService (namespaces 最適化 + フォールバック) → 集約スコアでタイトル出力。
- Synonym: 軽展開（Keyword=OR / Embedding=代表1語追記）で Recall 向上、ノイズ抑制。
- Logging: JSON line `SEARCH_EVENT` に retry_stage / namespaces / min_score / top5_scores / normalized_query。
- Metrics: Prometheus `feedback_total` / `zero_hit_total`。追加予定: recall_batch_gauge（手動集計投入）。

---
## 5. 検索リトライ戦略（現行 → 拡張予定）
| Stage | 条件 | namespaces | min_score | top_k | 目的 |
|-------|------|-----------|----------|-------|------|
| 0 | 初回 | effect_* | base (≈0.4) | 10 | 通常精度 |
| 1 | 0件時 | +effect_combined 先頭 | base-0.05 | 20 | 分散補完 |
| 2 (設計中) | 依然0件 | 同 + synonym 再埋め込み | base-0.05〜0.10 | 20 | 語彙拡張救済 |

Stage2 実装後は zero_hit_rate の減衰度を計測し、恒久的な base 阈値変更ではなく段階的フォールバックで Recall を確保。

---
## 6. 指標 (KPI) 定義 & 初期ターゲット
| Metric | 意味 | 計算 | 初期目標 |
|--------|------|------|-----------|
| zero_hit_rate | 0件発生率 | zero_hit_total / total_queries | <15% → 中期 <8% |
| negative_rate | 体感品質 | neg_feedback / all_feedback | 各施策 -10% 相対改善 |
| P@10 | 精度 | relevant@10 / 10 | ベースライン +5pp |
| Recall@10 | 再現 | relevant@10 / total_relevant | +5pp 継続 |
| MRR | ランキング | 1/rank_first_relevant | 上昇傾向 |

ベースラインは精度バッチ完了後に表内へ数値挿入。

### 🧪 初回ベースライン (2025-08-27 08:41 JST)
eval_precision_batch.py --real 実行 (labels v1 / Top-K=10)

| Metric | Baseline | 備考 |
|--------|----------|------|
| P@10 | 0.0000 | 取得 context 0件 (提案のみ) |
| Recall@10 | 0.0000 | 全16クエリ relevant ラベルありもヒット無し |
| MRR | 0.0000 | |
| zero_hit_rate(計測方法上) | 0.0000 | 実装上 suggestion が1件扱いで0件判定逃れ。実質ヒット0/16 |

注記:
1. VectorService 現行挙動で検索結果 (context) が空のため Precision/Recall が 0。まずはインデックス/namespace/threshold/Stage3 再試行で実ヒットを発生させる必要あり。
2. zero_hit_rate が 0.0 と出力されたのは計測ロジックが suggestion を結果扱いしている可能性。評価スクリプト側で zero-hit 判定を context 件数ベースに修正検討。
3. 次アクション優先度: (a) Stage3 実装 / synonym 再埋め込み (b) min_score 段階的引下げでヒット創出 (c) `effect_combined` namespace 有効化の挙動検証 (d) zero-hit 判定修正。

---
## 7. フィードバック基盤（MVP 要約）
- API: `POST /api/feedback` （rating: -1/1, optional reason）
- 保存: `search_feedback`（query メタ: top_titles, namespaces, min_score, scores, query_type, timestamps）
- メトリクス: rating 単純計数 + negative_rate 定期集計（スクリプト化予定）。
- 活用: negative 上位トークン → synonym 辞書 / threshold 調整材料。

---
## 8. リスク & 緩和（現在有効なもののみ）
| リスク | 影響 | 緩和策 |
|--------|------|--------|
| combined 長文優遇 | Precision 低下 | Stage>0 限定使用 + 差分監視 |
| synonym 過展開 | ノイズ増 | 代表語最少 + Negative率監視でロールバック |
| 閾値過剰引下げ | 低品質混入 | リトライ段階化（-0.05 刻み上限）|
| インデックス肥大 | コスト増 | combined 1件/カード + タグ導入時に差分測定 |
| ログ肥大 | ディスク圧迫 | 日次ローテ + gzip 圧縮スクリプト |

---
## 9. 即時オペレーション手順（最短版）
1. フル再インデックス: `python scripts/data-processing/index_effects_to_vector.py` （不要なら `--no-combined`）
2. 差分監査: `--dry-run` 実行 → JSONL 件数 / namespace 比較
3. 挙動検証: `tail -f logs/* | jq 'select(.event=="SEARCH_EVENT") | {q:.normalized_query, st:.retry_stage, ns:.namespaces, top:.top5_scores}'`
4. zero_hit_rate 上昇時: synonym マップ / min_score 調整を試験ブランチで A/B → 指標比較

---
## 10. Open Questions（決定待ち）
1. Top-K 上限（ユーザ向け API 提供最大値）を 10 or 20 どちらで凍結するか。
2. 英語混在クエリへの最小サポート方針（完全許容 / fallback / ガイド記述）。
3. Index 再構築の運用トリガー（手動デイリー / 変更検知自動）。
4. ベースライン評価用 “正解カード集合” のドメイン監修可能性。
5. UI 表示にスコア/簡易効果抜粋を載せる要否（UX 改善 vs 情報過多）。

---
## 11. 近日ロードマップ（カテゴリ別）
| Category | Item | 目的 | 優先 |
|----------|------|------|------|
| テスト | 0件既知 3 クエリ回帰追加 | Zero-hit 防止 | High |
| 評価 | 精度バッチ (P/R/MRR) | ベースライン確立 | High |
| 検索 | Retry Stage3 | Zero-hit 更削減 | High |
| ドキュメント | ガイド更新 (synonym/retry) | 利用性 | Medium |
| Embedding | 正規化/ストップワード軽除去 | Precision 保持 | Medium |
| 分析 | feedback export v1 | 改善サイクル短縮 | Medium |
| ランキング | Hard Negative 下準備 | 将来改良 | Low |

---
## 12. 受け入れ基準（近接スプリント）
達成条件（最新）:
- Stage3 リトライ実装 & 0件クエリで `retry_stage=2` ログ発火。
- 精度バッチ初回実測 (relevant ラベル投入後) CSV と KPI 表更新。
- ガイドに評価/リトライ/ログ確認手順を反映。

---
## 13. 参考サンプルクエリ（16件セット）
継続ダメージ / 守護無視 / 手札ドロー / 全体強化 / リーダー直接ダメージ / 単体破壊 / 全体ダメージ / 疾走 / 守護付与 / ラストワードでトークン or カード追加 / 進化時トークン生成 / デッキサーチ / 手札を捨てる・入替 / コスト軽減 / カウントダウン進める / 守護を失わせる

---
## 14. 変更履歴（要点）
| 日付 | 種別 | 概要 |
|------|------|------|
| 2025-08-17 | 実装 | effect_combined インデックス追加 |
| 2025-08-18 | 改善 | synonym 軽量展開（Keyword OR / Embedding 代表語）|
| 2025-08-20 | ログ | SEARCH_EVENT 構造化 + retry_stage 追加 |
| 2025-08-22 | 修正 | effect_1..9 走査拡張 / min_score=0.4 調整 |
| 2025-08-25 | 文書 | 本ドキュメント再編（簡潔化） |

---
## 15. Appendix（旧詳細 / 参考用）
旧ファイルに含まれていた詳細仕様・背景・完全タスクリスト・フィードバック設計全文などは履歴で参照可能です。将来必要になった粒度（例: モデル再学習、Hard Negative 再ランキング手法）に達した時点で再インポートしてください。

（削除した主な冗長要素）
- 重複したリスク表（差分のみ維持）
- タスクの多段重複記述（最新優先表に統合）
- 詳細なテーブル定義 / API 仕様（MVP 要約に集約）
- 改善サイクルの逐語説明（要点のみ残存）

---
## 16. 次の一歩（今日着手推奨）
1. テスト 3 クエリ追加 → CI 実行。
2. 精度バッチ雛形 `scripts/data-processing/eval_precision_batch.py` 作成（未存在なら）。
3. Stage3 試験実装ブランチで zero_hit_rate 差分ログ収集。

---
（以上）

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

### 優先タスク再整理（2025-08-23 更新）

検索品質改善と計測基盤を段階的に進めるための最新優先度（依存関係 / 改善レバレッジ / 実装コストのバランス）再整理。

#### Tier 0（計測とデータ蓄積の即時着手）
1. Feedback基盤仕上げ（済）
  - QueryContext に `namespaces` / `min_score` を注入（`search_info` から）
  - フィードバック API の単体 / ルータテスト追加
  - 簡易集計スクリプト（negative_rate, zero_hit_rate の CSV 出力）
2. 構造化ログ統一（済）
  - JSON line: `{"ts", "query_id", "stage", "normalized_query", "namespaces", "min_score", "top5_scores"}`
  - zero hit 時: `retry_stage`=0 を必ず出力
  - 実装状況: `RagService.process_query` で QueryContext 保存後に `GameChatLogger.log_info("search_structured", "SEARCH_EVENT", {...})` を出力。
    - 追加フィールド: `retry_stage`, `zero_hit`（0件検出用）, `top5_scores`(=top5), `stage="search_complete"`
    - `HybridSearchService` で `normalized_query` を `search_info` に注入し構造化ログに含める。
    - `VectorService.last_params` から `used_namespaces`, `min_score`, `final_stage` を取得し `namespaces`, `min_score`, `retry_stage` に反映。
3. Prometheus カウンタ雛形（済）
  - `feedback_total{rating,query_type}` / `zero_hit_total` のスタブ実装完了
    - 実装: `backend/app/core/metrics.py` で Counter 定義 (`FEEDBACK_COUNTER`, `ZERO_HIT_COUNTER`)
    - 連携: `feedback_service.submit_feedback()` で `inc_feedback()`、`rag_service.process_query()` の SEARCH_EVENT 生成時に zero-hit 時 `inc_zero_hit()`
    - 初期化: `main.py` 冒頭で side-effect import により登録
    - 影響範囲: 既存テスト 359 passed (回帰なし)

（理由）改善施策より先に“現状の土台”を観測しベースラインを固定するため。

#### Tier 1（Recall 即効性：Zero-hit 削減）
4. 同義語/表記ゆれ軽量展開レイヤー（済）
  - 実装内容:
    - QueryNormalizationService に synonym グループ + `build_db_keyword_expansion_mapping()` 追加
    - DBフィルタ: キーワード毎に OR パターンへ展開しログ `DBキーワード展開` で `expansion_map` 計測
    - Embedding: 原文 + グループ代表1語のみ（改行区切り）→ `embedding_extra_terms_count` を `search_info` に注入
    - 正規化: NFKC / 余剰空白圧縮 / 長音連続縮約
    - HybridSearchService `_execute_searches` 再構成（インデント/未定義変数バグ修正）
  - ログ観測: `SEARCH_EVENT` に `normalized_query`, `embedding_extra_terms_count` を追加（上位解析用）
  - テスト: 全 359 passed / 20 skipped（回帰なし）
  - 次段階アイデア: synonym YAML 外部化 / 展開ヒット率 Prometheus Histogram
5. `effect_combined` インデックス & フォールバック
  - index スクリプトで combined 生成
  - 0件時 combined 追加 + `min_score -0.05` で再試行
6. VectorService スコア集約の完全化（済）
  - タイトル単位で max(score) 集約 → 降順ソート
  - `search_info` に `used_namespaces`, `threshold`, `retry_stage`

#### Tier 2（動的最適化 & 評価サイクル）
7. 0件リトライポリシー段階化（stage1: combined追加 / stage2: 同義語再埋め込み）
8. サンプル16クエリ用 精度バッチ（P@K / R@K / MRR）
9. Feedback 集計スクリプト正式版（query_type 別 negative_rate, token 頻度）

#### Tier 3（テキスト品質 & 運用性）
10. EmbeddingService 強化（効果キーワード抽出 + 軽ストップワード除去）
11. Feedback 自動タグ付け（synonym_miss / low_recall / low_score）
12. ガイド更新（synonym 展開 / retry 戦略 / feedback 解析手順）

#### Tier 4（高度化 / 後続）
13. Hard Negative 再ランキング（keyword boost + negative feedback 利用）
14. ネガティブ率移動平均監視とアラート

#### 直近 “今日” 推奨 3 ステップ
1. QueryContext enrich（namespaces / min_score 注入）（済）
2. 構造化 JSON ログ出力（top5 & threshold）
3. 同義語マップ初版 + before/after ログ

#### KPI 初期セット
- zero_hit_rate = zero_hit_total / total_queries
- negative_rate = feedback_total{rating=-1} / feedback_total{all}
- improvement 判定: (negative_rate_before - negative_rate_after) / negative_rate_before ≥ 10%

#### リスク & 対応（追加）
| リスク | 新規観点 | 対応 |
|--------|----------|------|
| ログ肥大 | JSON line 増加でディスク圧迫 | 日次ローテ + gzip 圧縮スクリプト |
| 同義語誤適用 | ノイズ語で precision 低下 | マップに信頼度ラベル / A/B 比較ログ |
| combined 過剰マッチ | 長文カードが常に上位独占 | combined は stage>0 のみ使用 |
| retry 濫用 | レイテンシ増大 | stage 回数上限 2 / メトリクス監視 |

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

## 優先着手順（依存関係 × 効果 × 実装コスト）

フィードバック基盤の最小スライス（MVP）

search_feedback テーブル + POST /api/feedback
検索完了時に QueryContext（一時: in-memory dict）へ query_id→メタ保存
👎 評価でサーバ側がメタ再構築して保存 意義: 以降の全改善に客観データを蓄積開始。後回しにすると学習期間が失われる。
ログ/可観測性拡充仕上げ

既存 DEBUG ログから top5 スコア/threshold を構造化 (JSON line) に統一
Prometheus カウンタ追加 (feedback_total, zero_hit_total) 意義: 閾値/namespace チューニングを数値ベースに移行できる。
同義語/表記ゆれ軽量展開レイヤー（サーバ側 Embedding 前処理）

固定マップ + 正規化（全角/半角・長音・余剰空白）
ネガティブ例収集開始後すぐ適用 → 改善差分測定 意義: 0件/低Recall の主因に即効性。
effect_combined インデックス追加 + フォールバック段階組込み

既存 index スクリプトに combined 生成追加
フォールバック第2段で combined を混ぜる 意義: 断片分散によるスコア落ち救済。Synonym 展開との相乗効果。
動的 min_score / 再試行ポリシー

1回目 0件 → threshold -0.05, top_k +10 で再検索
ログに retry_stage フィールド 意義: 過度の恒久閾値引き下げを避けつつ 0件率削減。
評価スクリプト (export_feedback_stats.py)

期間別 negative_rate, トークン頻度, query_type breakdown
CSV/JSON 出力 意義: チューニング効果の週次レビューを自動化。
QA answer / effect_combined 再インデクシング自動フロー

make タスク or scripts ディレクトリに統合
index_version を feedback に記録 意義: 改善施策と品質変動の因果追跡を容易に。
追加ランキング改善（後段）

ベクトル topN に対する簡易再スコア（キーワードヒット + synonym boost）
feedback の negative ケースを Hard Negative として単純重み調整


---
