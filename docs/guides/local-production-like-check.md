# ローカルで本番環境と同じ状態で動作確認する手順（APIキー漏洩リスク最小化版）

## 目的
本番環境と同じ環境変数・設定でローカル開発サーバーを起動し、APIキー等の漏洩リスクを最小限に抑えつつ動作確認を行う方法をまとめます。

---

## 1. 本番用.envファイルの管理
- **APIキーやシークレットは絶対にリポジトリにコミットしない**
- `.env.production` など本番用envファイルは、**.gitignore** で除外し、必要な場合のみ安全な手段でローカルに配布
- 例: Google Drive, 1Password, SlackのDM等で個別共有

---

## 2. ローカルで本番用envを使って起動する方法

### 2-1. Next.jsフロントエンド
1. `frontend/.env.production` をローカルに配置
2. `frontend` ディレクトリで以下コマンドを実行

```sh
cp .env.production .env.local
npm run dev
```

- `.env.local` はNext.jsが優先的に読み込むため、本番と同じ環境変数で開発サーバーが起動します
- **APIキーが含まれるため、.env.localも.gitignore必須**

#### ワンライナー例
```sh
cd frontend && cp .env.production .env.local && npm run dev
```


### 2-2. Backend（FastAPI等）本番同等ローカル起動
1. `backend/.env.production` を安全な手段でローカルに取得し、`backend/` 配下に配置
2. `.env.production` を `.env` にコピー（FastAPIやuvicornは`.env`を自動で読み込むことが多い）

```sh
cd backend
cp .env.production .env
# 開発サーバー起動例（uvicornの場合）
uvicorn app.main:app --reload
```

- `.env` も **.gitignore** で除外必須
- APIキーやシークレットは絶対にリポジトリに含めない

#### Docker Composeで本番同等起動（フロント・バックエンド同時）
- プロジェクトルートで `.env.production` を `.env` にコピー
- `docker-compose.prod.yml` を使って起動

```sh
cp .env.production .env
cp frontend/.env.production frontend/.env.local
cp backend/.env.production backend/.env
# 本番用docker compose起動
docker-compose -f docker-compose.prod.yml up --build
```

---

## 3. セキュリティ対策
- **APIキー/シークレットは絶対に公開リポジトリやパブリックな場所に置かない**
- `.env*` ファイルは全て `.gitignore` で除外
- コミット前に `scripts/utilities/check-env-security.sh` で漏洩チェック推奨

```sh
./scripts/utilities/check-env-security.sh
```

---

## 4. よくあるトラブル
- **APIキーが読み込まれない**: .envファイルのパス・ファイル名を再確認
- **環境変数の反映がうまくいかない**: サーバー再起動、キャッシュクリア
- **APIキー漏洩**: 万一漏洩した場合は即時ローテーション

---

## 5. 参考
- [Next.js公式: 環境変数の管理](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
- [Docker Compose: envファイルの使い方](https://docs.docker.com/compose/environment-variables/)
- `scripts/utilities/check-env-security.sh` で安全性チェック

---

## まとめ
- 本番用envファイルは厳重に管理し、ローカル確認時のみ一時的に利用
- `.env.local`/`.env`は**絶対にコミットしない**
- セキュリティスクリプトで漏洩リスクを最小化

---

## 検索精度改善のための改修方針・手順

### 1. database_service.py のフィルタ条件ロジック見直し
- **現状の課題**: キーワードの部分一致や数値条件（例:「7以上」「PP回復」など）の判定が甘く、意図したカードがヒットしない場合がある。
- **改修ポイント例**:
    - 数値条件（「7以上」「100以上」など）を正規表現で抽出し、カードデータの該当属性（cost, hp, attack など）と比較するロジックを強化
    - 「PP回復」や「疾走」など、効果文やキーワードに現れるワードの柔軟な判定（部分一致・正規化）
    - 複数条件（例:「コスト7以上 かつ PP回復」）のAND検索を厳密に
    - テストデータを追加し、意図した条件で正しくヒットするか確認

#### 具体的な改修手順例
1. `database_service.py` の `_calculate_filter_score` 内で、
    - 数値条件抽出用の関数（例: extract_numeric_condition）を実装
    - 効果文やattacks配列のテキストも正規表現で柔軟に判定
2. テスト（`test_database_service.py`）に「コスト7以上」「PP回復」などの複合条件ケースを追加
3. 実データでのヒット率を確認し、必要に応じて閾値やスコア計算を調整

### 2. classification_service.py の分類ロジック見直し
- **現状の課題**: クエリ分類が「semantic」や「filterable」に正しく分かれず、意図した検索戦略が選ばれない場合がある。
- **改修ポイント例**:
    - システムプロンプトの例・指示をより具体的に（例:「コスト7以上でPP回復するドラゴン」→ filterable）
    - LLMの出力JSONの一貫性担保（例: 必ず filter_keywords, search_keywords を返すように）
    - クエリ例を増やし、分類の精度を上げる
    - モック環境の簡易分類ロジックも、より現実的な条件分岐に

#### 具体的な改修手順例
1. `classification_service.py` の system_prompt を見直し、具体例・指示を追加
2. クエリ例を増やし、filterable/semantic/hybrid の分類基準を明確化
3. テストケース（`test_classification_service.py` など）で分類結果の妥当性を検証
4. 必要に応じて LLMのパラメータ（temperature, max_tokens など）も調整

---

### 改修の進め方まとめ
1. まずは **database_service.py** のフィルタ条件ロジックを強化し、テストで意図通りのカードがヒットするか確認
2. 次に **classification_service.py** の分類プロンプト・ロジックを見直し、クエリ分類の精度を上げる
3. テストを充実させ、実データ・実クエリでの動作確認を徹底
4. 改修後は必ずローカルで本番同等の環境変数・データで動作確認

