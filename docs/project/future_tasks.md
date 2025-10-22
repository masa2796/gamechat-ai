# 🚀 GameChat AI - 今後やるべきことタスク一覧

**最終更新**: 2025年10月21日  
**ブランチ**: `release-mvp-120`  
**プロジェクト状況**: MVPモード（最小価値検証）

## 📋 概要

このドキュメントは、GameChat AIプロジェクトの今後やるべきタスクを優先度別に整理したものです。現在はMVPモードで運用中のため、最小機能での安定運用を最優先としています。

## 🔥 最優先タスク（P0）- 即座に対応

### 1. MVPデプロイメント完了 🚨
**期限**: 即座  
**担当**: DevOps  

- [ ] **バックエンドのCloud Runデプロイ**
  - `backend/Dockerfile`を使用してCloud Runへデプロイ
  - 必須環境変数の設定（`UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`）
  - `POST /chat`エンドポイントの動作確認（200レスポンス）
  - `scripts/deployment/deploy_cloud_run_mvp.sh`の実行権限確認と実行

- [ ] **フロントエンドのFirebase Hostingデプロイ**  
  - `NEXT_PUBLIC_MVP_MODE=true`でビルド
  - `firebase.json`のrewrite設定確認
  - `scripts/deployment/deploy_firebase_hosting_mvp.sh`の実行
  - `/chat`エンドポイントの利用確認

- [ ] **Upstash Vectorデータ投入**
  - `scripts/data-processing/`のデータ投入スクリプト作成
  - `data/convert_data.json`からカードデータをアップサート
  - デフォルトnamespaceへの投入実行
  - `/chat`の`retrieved_titles`への反映確認

### 2. 環境変数・設定ファイル整備 📝
**期限**: 即座  
**担当**: Backend

- [x] **`.env.prod.example`の追加**
  - 推奨キー: `BACKEND_ENVIRONMENT=production`, `BACKEND_LOG_LEVEL=INFO`
  - Upstash設定: `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`
  - 任意: `BACKEND_OPENAI_API_KEY`

- [x] **`.firebaseignore`の追加**
  - 除外対象: `htmlcov/`, `logs/`, `backend/`, `scripts/`
  - 不要ファイルのHosting除外

- [x] **CORS設定の最終確認**
  - `settings.CORS_ORIGINS`の設定（Firebaseドメイン + localhost）
  - 本番環境での`BACKEND_ENVIRONMENT=production`設定

## 🔴 高優先タスク（P1）- 1-2週間以内

### 3. ドキュメント整備 📚
**期限**: 2週間以内  
**担当**: Documentation

- [ ] **README.md更新**
  - MVP構成での利用方法を冒頭に追記
  - `/chat`エンドポイントの使用方法
  - 環境変数設定手順
  - クイックスタートガイドの充実

- [ ] **デプロイガイド更新**
  - `docs/deployment/cloud_run_firebase_mvp.md`の最新化
  - Cloud Run + Firebase Hostingの手順詳細化
  - 環境変数設定の具体例

- [ ] **環境変数ガイド更新**
  - `docs/project/env_mvp.md`の最新化
  - フォールバック挙動の詳細説明
  - トラブルシューティング追加

### 4. チャット履歴機能の修正 🐛
**期限**: 1週間以内  
**担当**: Frontend

- [ ] **緊急バグ修正（Phase 2b）**
  - チャット切り替え機能の修復
  - 新規チャット作成機能の修復
  - メッセージ描画機能の修復
  - エラーハンドリングの追加

- [ ] **動作確認テスト**
  - 手動テスト: 各機能の基本動作確認
  - ブラウザコンソールでのエラー確認
  - LocalStorageの状態確認
  - ネットワークタブでのAPI通信確認

### 5. テスト・品質保証 🧪
**期限**: 2週間以内  
**担当**: QA/Testing

- [ ] **backend pytestの維持**
  - `pytest backend/app/tests/ -q`がPASSすることを確認
  - 新機能追加時のテストカバレッジ維持

- [ ] **手動テスト実行**
  - `/chat`エンドポイントの各種パターンテスト
  - with_context true/falseの両方での動作確認
  - フォールバック機能の動作確認

## 🟡 中優先タスク（P2）- 1ヶ月以内

### 6. 運用・監視体制の強化 📊
**期限**: 1ヶ月以内  
**担当**: DevOps

- [ ] **ログ・監視の改善**
  - 構造化ログの実装
  - パフォーマンスメトリクス収集
  - アラート機能の設定

- [ ] **セキュリティ強化**
  - CORS設定の厳密化
  - Rate limitingの実装
  - セキュリティヘッダーの完全実装

- [ ] **CI/CD改善**
  - 自動テストの実装
  - デプロイメント自動化
  - ロールバック手順の整備

### 7. パフォーマンス最適化 ⚡
**期限**: 1ヶ月以内  
**担当**: Backend/DevOps

- [ ] **レスポンス時間最適化**
  - 目標: 全クエリ5秒以内の応答
  - Vector検索最適化（top_k制限、タイムアウト制御）
  - Cloud Runインスタンス設定最適化

- [ ] **リソース使用量最適化**
  - CPU/メモリ配分の調整
  - 不要な処理の削除
  - キャッシュ機構の検討

### 8. UX/UI改善 🎨
**期限**: 1ヶ月以内  
**担当**: Frontend

- [ ] **チャット履歴UI改善（Phase 3）**
  - タイトル自動生成機能
  - アニメーション・トランジション追加
  - レスポンシブ対応の改善

- [ ] **エラーハンドリング強化**
  - ユーザーフレンドリーなエラーメッセージ
  - ローディング状態の改善
  - オフライン対応の検討

## 🔵 低優先タスク（P3）- 将来的に検討

### 9. 機能拡張（非MVP機能の復活） 🔮
**期限**: 長期計画  
**担当**: Development Team

- [ ] **LLMクエリ分類機能**
  - 過去commitからの復元
  - requirements.txtへのhttpx等の再追加
  - テストケースの復活

- [ ] **ハイブリッド検索機能**
  - Database複合フィルタの復活
  - DynamicThresholdManagerの復元
  - Hybrid マージ機能の実装

- [ ] **認証システム強化**
  - AuthService(reCAPTCHA)の復活
  - APIキーローテーション自動化
  - ユーザー管理機能の追加

### 10. 新機能開発 ✨
**期限**: 長期計画  
**担当**: Product Team

- [ ] **新しいゲームデータ追加**
  - データ収集・整理
  - ベクトル化・投入
  - 検索精度向上

- [ ] **多言語対応**
  - i18n実装
  - 多言語データの準備
  - UI/UXの国際化

- [ ] **モバイルアプリ開発**
  - React Native検討
  - PWA対応強化
  - ネイティブ機能活用

## 📊 進捗管理・KPI

### 重要指標
- **API応答時間**: 平均3秒以下、最大5秒以内
- **可用性**: 99.9%以上
- **エラー率**: 1%未満
- **デプロイ成功率**: 100%

### マイルストーン
1. **Week 1**: MVPデプロイメント完了
2. **Week 2**: ドキュメント整備完了
3. **Week 4**: チャット履歴機能修正完了
4. **Month 1**: 運用・監視体制完成
5. **Month 3**: パフォーマンス最適化完了

## 🔗 関連リソース

- [Release MVP タスク](./release_mvp.md)
- [環境変数一覧](./env_mvp.md)
- [プロジェクト状況](./project-status.md)
- [チャット履歴管理機能](../issues/chat-history.md)
- [デプロイメントガイド](../deployment/cloud_run_firebase_mvp.md)

## 📞 エスカレーション・連絡体制

### 問題発生時の対応
1. **軽微な問題**: 通常の開発フローで対応
2. **重大な問題**: 即座にチーム相談
3. **本番影響**: 緊急対応チーム招集

### 報告・共有
- **週次進捗報告**: 毎週金曜日
- **マイルストーン報告**: 各マイルストーン完了時
- **問題発生時**: 即座にチーム共有

---

**Note**: このドキュメントは定期的に更新され、プロジェクトの進捗に応じてタスクの優先度や内容が変更される可能性があります。最新の状況は関連リソースも併せて確認してください。