# バックエンドデプロイできない原因まとめ

## 概要

GameChat AIプロジェクトのバックエンドをGoogle Cloud Runにデプロイする際に発生した主要な問題とその原因を体系的にまとめたドキュメントです。今後の参考資料として活用してください。

## 🚨 主な失敗原因カテゴリ

### 1. Google Cloud サービス設定不備

#### 1.1 API未有効化
**問題**: 必要なGoogle Cloud APIが有効化されていない
- Secret Manager API
- Cloud Build API  
- Cloud Run API
- Container Registry API

**症状**:
```
API [secretmanager.googleapis.com] not enabled on project [gamechat-ai-production]
```

**原因**: 新規プロジェクトや初回デプロイ時に必要なAPIの有効化を忘れる

**解決策**:
```bash
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 1.2 IAM権限不足
**問題**: サービスアカウントに適切な権限が付与されていない

**症状**:
```
Permission 'secretmanager.versions.access' denied
```

**原因**: 
- Cloud BuildサービスアカウントがSecret Managerにアクセスできない
- Cloud RunサービスアカウントがSecret Managerを読み取れない
- 最小権限の原則を適用しすぎて必要な権限まで制限

**解決策**:
```bash
# Cloud Buildサービスアカウントに権限付与
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

# Cloud Runサービスアカウントに権限付与  
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 2. 環境変数設定の問題

#### 2.1 特殊文字エスケープエラー
**問題**: URL等の特殊文字を含む環境変数が正しく解析されない

**症状**:
```
Bad syntax for dict arg: [https://gamechat-ai.firebaseapp.com]
```

**原因**:
- `--set-env-vars`でURL（コロン、スラッシュ等）を直接指定
- カンマ区切りで複数の環境変数を指定した際の構文解析エラー
- 引用符やエスケープ処理の不備

**NG例**:
```yaml
'--set-env-vars', 'CORS_ORIGINS=https://app1.com,https://app2.com'
```

**解決策**:
```yaml
# 方法1: 個別指定
'--set-env-vars', 'CORS_ORIGINS=https://app1.com,https://app2.com'

# 方法2: YAMLファイル使用（推奨）
'--env-vars-file', 'cloud-run-env.yaml'
```

#### 2.2 環境変数ファイル形式エラー
**問題**: `--env-vars-file`に渡すファイルの形式が間違っている

**症状**:
```
Invalid YAML/JSON data in [cloud-run-env.yaml], expected map-like data
```

**原因**:
- key=value形式のテキストファイルをYAMLファイルとして指定
- YAML構文の不備（インデント、引用符等）

**NG例**:
```ini
ENVIRONMENT=production
CORS_ORIGINS=https://app.com
```

**正しい形式**:
```yaml
ENVIRONMENT: production
CORS_ORIGINS: "https://app.com"
```

### 3. ビルド最適化の問題

#### 3.1 ビルドアーカイブサイズ過大
**問題**: 不要なファイルがビルドアーカイブに含まれてビルド時間が長くなる

**症状**:
```
Creating temporary archive of 23034 file(s) totalling 335.3 MiB
```

**原因**:
- `.gcloudignore`ファイルが存在しない
- node_modules、.git、ビルド成果物等の大容量ファイルが含まれる

**解決策**: `.gcloudignore`ファイルを作成
```gitignore
.git/
frontend/node_modules/
backend/__pycache__/
logs/
.env*
```

#### 3.2 Dockerビルドの最適化不足
**問題**: Dockerイメージサイズが大きい、ビルド時間が長い

**原因**:
- マルチステージビルドの未使用
- 不要なパッケージやファイルがイメージに含まれる
- レイヤーキャッシュの活用不足

### 4. Secret Manager関連の問題

#### 4.1 シークレット値の不備
**問題**: 保存されたシークレット値が正しくない

**原因**:
- API キーのコピー&ペースト時の改行文字混入
- 特殊文字を含むシークレットの不適切なエンコーディング
- 環境ごとのシークレット値の混在

**診断方法**:
```bash
# シークレット値の確認（本番環境では注意）
gcloud secrets versions access latest --secret="SECRET_NAME"
```

#### 4.2 シークレットバージョン管理
**問題**: 古いバージョンのシークレットを参照している

**原因**:
- シークレット更新後にバージョン指定が更新されていない
- `latest`指定の落とし穴（削除されたバージョンを参照）

### 5. ネットワーク・セキュリティの問題

#### 5.1 CORS設定エラー
**問題**: フロントエンドからのAPIアクセスが拒否される

**症状**:
```
Access to XMLHttpRequest blocked by CORS policy
```

**原因**:
- CORS_ORIGINSの設定漏れや間違ったURL
- プロトコル（https/http）の不一致
- ポート番号の不一致

#### 5.2 認証・認可の問題
**問題**: Cloud Runサービスへのアクセスが拒否される

**原因**:
- `--allow-unauthenticated`フラグの設定漏れ
- IAMポリシーの設定不備
- サービスアカウントキーの設定問題

### 6. 設定ファイル管理の問題

#### 6.1 環境変数の環境間混在
**問題**: 開発環境と本番環境の設定が混在する

**原因**:
- 環境ごとの設定ファイル分離不足
- 環境変数の上書き順序の理解不足
- デフォルト値の不適切な設定

#### 6.2 設定値の同期不備
**問題**: 複数の設定ファイル間で値が不整合

**原因**:
- cloudbuild.yaml、Dockerfile、docker-compose.yml間の設定不整合
- Secret Managerとローカル環境変数の不一致

## 🛠 予防策とベストプラクティス

### 1. 事前チェックリストの活用
- API有効化チェック
- 権限設定チェック
- 設定ファイル形式チェック
- シークレット値チェック

### 2. 段階的デプロイメント
1. ローカル環境でのテスト
2. 開発環境でのビルドテスト  
3. ステージング環境での統合テスト
4. 本番環境デプロイ

### 3. ログとモニタリング
```bash
# Cloud Buildログの確認
gcloud builds log BUILD_ID

# Cloud Runサービスログの確認
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# ヘルスチェック
curl -f "https://SERVICE_URL/health"
```

### 4. 設定の自動化
- Infrastructure as Code（Terraform等）の活用
- CI/CDパイプラインでの自動チェック
- 設定テンプレートの活用

### 5. セキュリティの強化
- 最小権限の原則の適用
- シークレットローテーションの実装
- セキュリティスキャンの自動化

## 📋 緊急時対応フロー

### 1. デプロイ失敗時
1. **ログの確認**: Cloud Build、Cloud Runログをチェック
2. **設定の確認**: 環境変数、シークレット、権限を確認
3. **ロールバック**: 前回成功したビルドに戻す
4. **段階的修正**: 小さな変更から順次適用

### 2. サービス停止時
1. **ヘルスチェック**: サービスの生存確認
2. **ログ分析**: エラーログの詳細確認
3. **リソース確認**: CPU、メモリ使用量チェック
4. **緊急修正**: 最小限の修正でサービス復旧

### 3. セキュリティインシデント時
1. **アクセス制限**: 問題のあるサービスへのアクセス停止
2. **シークレットローテーション**: 漏洩の可能性があるキーの変更
3. **監査ログ確認**: アクセスログの詳細分析
4. **報告書作成**: インシデント対応記録の作成

## 🔗 関連ドキュメント

- [Cloud Run トラブルシューティングガイド](./cloud-run-troubleshooting.md)
- [デプロイメント チェックリスト](./cloud-run-deployment-checklist.md)
- [OpenAI API キー設定ガイド](./cloud-run-openai-setup.md)
- [本番環境デプロイメント手順](./production-deployment.md)

## 📝 更新履歴

- 2024-12-20: 初版作成
- 環境変数設定問題、権限エラー、ビルド最適化問題を体系化
- 予防策とベストプラクティスを追加
- 緊急時対応フローを整備

---

このドキュメントは実際のデプロイメント過程で発生した問題を基に作成されています。  
新しい問題が発生した場合は、随時このドキュメントを更新してください。
