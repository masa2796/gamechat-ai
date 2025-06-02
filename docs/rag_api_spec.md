# RAG API仕様書

## 概要

カードゲームのカード名に関する質問に対して、RAG（検索拡張生成）を用いて関連情報を検索し、LLMによる回答を生成するAPI。

---

## エンドポイント

### POST `/api/rag/query`

カードに関する自然言語の質問を受け取り、RAGによる回答を生成する。

---

## リクエスト形式

### Content-Type: `application/json`

```json
{
  "question": "《ブラック・ロータス》ってどんな効果？",
  "top_k": 3,
  "with_context": true,
  "recaptchaToken": "xxx"
}
```

| パラメータ名           | 型      | 必須 | 説明                               |
| ---------------- | ------ | -- | -------------------------------- |
| `question`       | string | 必須 | 回答対象となる自然言語の質問                   |
| `top_k`          | int    | 任意 | 上位何件の検索結果を利用するか（デフォルト: 3、最大: 10） |
| `with_context`   | bool   | 任意 | 回答に検索結果を含めるか（デフォルト: true、省略時はtrueとして扱う）        |
| `recaptchaToken` | string | 必須 | Google reCAPTCHAのトークン            |

---

## バリデーション仕様

* `question`: 1〜200文字以内、空白のみ不可
* `top_k`: 1〜10の整数（デフォルト: 3、最大: 10。それ以外は400）
* `with_context`: boolean（true/false、省略時はtrue）
* `recaptchaToken`: 非空の文字列

---

## レスポンス形式

### 成功時（HTTP 200）

#### `with_context: true`（省略時もtrueとして扱う）

```json
{
  "answer": "《ブラック・ロータス》はマナ加速カードで...",
  "context": [
    {
      "title": "カード解説 - ブラック・ロータス",
      "text": "ブラック・ロータスはマナを3点追加できる...",
      "score": 0.95
    },
    {
      "title": "カードランキング",
      "text": "レアカードの中でも強力とされる...",
      "score": 0.87
    }
  ]
}
```

- `context`配列の最大件数は`top_k`の値に依存し、最大10件です。

#### `with_context: false`

```json
{
  "answer": "《ブラック・ロータス》はマナ加速カードで..."
}
```

### context配列のtitle仕様

- `title`は検索結果の「情報ソース名」または「カード名＋属性名（例：ブラック・ロータス - 効果説明）」で決定されます。
- フロントエンドはこのtitleを表示用の見出しとして利用してください。

---

### エラー時

#### HTTP 400（バリデーションエラー）

```json
{
  "error": {
    "message": "top_kは1〜10の範囲で指定してください",
    "code": "INVALID_TOP_K"
  }
}
```

#### HTTP 400（reCAPTCHAトークン無効）

```json
{
  "error": {
    "message": "reCAPTCHAトークンが無効です",
    "code": "INVALID_RECAPTCHA"
  }
}
```

#### HTTP 500

```json
{
  "error": {
    "message": "内部エラーが発生しました",
    "code": "INTERNAL_SERVER_ERROR"
  }
}
```

#### HTTP 504

```json
{
  "error": {
    "message": "応答がタイムアウトしました",
    "code": "TIMEOUT"
  }
}
```

| ステータスコード | 意味                     |
| -------- | ---------------------- |
| 200      | 成功（回答を含む）              |
| 400      | 不正な入力（バリデーションエラー・reCAPTCHA無効）      |
| 500      | サーバー内部エラー              |
| 504      | タイムアウト（検索・生成処理が10秒を超過） |

---

## 実装方針

* 非同期処理：検索・LLM呼び出しは `async/await` 対応
* タイムアウト設定：検索と生成の合計で10秒超過時は504エラー返却
* セキュリティ：Cookie識別とreCAPTCHAによる匿名認証を組み合わせた軽量な防御機構
* LLMモデル：現在は gpt-3.5-turbo を使用中。将来的なアップグレード予定あり。

```txt
[Front]             [API Middleware]             [RAG処理]
  └─入力 + reCAPTCHA→ 認証（Cookie）→ レート制限 → バリデーション → 実行 → 応答

【reCAPTCHA】
- 初回 or 疑わしい時のみ実施

【Cookie】
- 匿名ID（user_id）を自動で保存
- 持続期間: 7日 / Secure / HttpOnly / SameSite=Lax

【レート制限】
- user_id + IP の組み合わせで Redis 等で制御
- 例: 1分間に10回まで

【バリデーション】
- Zodなどで入力内容検証（length, 禁止語句など）

【CORS】
- フロントドメインからのアクセスに限定
- 例: `Access-Control-Allow-Origin: https://example.com`
```

---

## 備考

* `context`配列のスコアは検索の関連度スコア（0〜1）
* context配列の最大件数はtop_kの最大値（10件）まで
* 今後の拡張として、カードカテゴリ指定、シリーズ絞り込み等も想定
* CORSはフロントドメインからのアクセスに限定（必要に応じて`Access-Control-Allow-Origin`設定）
* LLMモデルは現状gpt-3.5-turboを利用。今後gpt-4等へのアップグレードも検討

---
