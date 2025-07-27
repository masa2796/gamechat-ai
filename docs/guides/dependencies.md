# 依存関係と開発ガイド

## 概要

このプロジェクトでは、開発環境と本番環境の両方で動作する単一の`requirements.txt`ファイルを使用した統一された依存関係管理アプローチを採用しています。

## 統一された依存関係管理

`requirements.txt`ファイルには以下が含まれています：

- **コア依存関係**: 基本機能に必要不可欠なパッケージ
- **認証機能**: JWT認証とパスワードハッシュ化（python-jose、passlib）
- **レート制限**: Redisとslowapiによるレート制限機能
- **本番サーバー**: 本番デプロイメント用のGunicorn
- **開発ツール**: テスト、リンティング、ドキュメント生成ツール

## 開発環境

すべての依存関係がデフォルトでインストールされます。コードにはオプション機能に対する適切なフォールバック処理が含まれています：

### 主な機能：
- **JWT認証**: `python-jose[cryptography]`と`passlib[bcrypt]`を使用
- **Redisレート制限**: `redis`パッケージを使用し、インメモリフォールバック付き
- **本番サーバー**: uvicornワーカーを使用した`gunicorn`

### 開発環境のセットアップ：

```bash
# すべての依存関係をインストール
pip install -r requirements.txt

# 開発サーバーを起動
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 本番環境

本番環境でもDockerを通じて同じ`requirements.txt`を使用します。すべての機能が利用可能です：

```bash
# 本番デプロイメント
./scripts/prod-deploy.sh
```

## VSCode統合

すべての依存関係がインストールされている状態では、VSCodeでのインポート警告は表示されません。コードには依存関係が不足している場合の適切なエラーハンドリングが含まれており、堅牢な動作を保証します。

## オプション依存関係

最小限の依存関係で開発したい場合は、選択的にインストールできます：

```bash
# コアのみ（一部機能が無効になります）
pip install fastapi uvicorn python-dotenv openai upstash-vector

# 認証機能を追加
pip install python-jose[cryptography] passlib[bcrypt]

# Redisレート制限を追加
pip install redis
```

## 型チェック

すべての依存関係はmypyによる型チェックをサポートしています。型チェックの実行：

```bash
mypy backend/app
```

## 依存関係の詳細

### 🔧 コア依存関係
- **FastAPI**: 高性能なWebフレームワーク
- **Uvicorn**: ASGI サーバー
- **Python-dotenv**: 環境変数管理
- **OpenAI**: OpenAI API クライアント
- **Upstash-vector**: ベクトルデータベースクライアント

### 🔐 セキュリティ・認証
- **python-jose[cryptography]**: JWT トークン処理
- **passlib[bcrypt]**: パスワードハッシュ化
- **slowapi**: FastAPI用レート制限

### 🚀 本番環境
- **Gunicorn**: WSGI/ASGI サーバー
- **Redis**: レート制限・キャッシュ用

### 🧪 開発・テスト
- **pytest**: テストフレームワーク
- **pytest-asyncio**: 非同期テスト
- **httpx**: HTTP クライアント（テスト用）
- **mypy**: 静的型チェック

## トラブルシューティング

### VSCodeでインポート警告が表示される場合
1. 仮想環境が正しく選択されているか確認
2. 依存関係が完全にインストールされているか確認：
   ```bash
   pip install -r requirements.txt
   ```

### レート制限が動作しない場合
- Redisが利用できない場合、自動的にインメモリフォールバックに切り替わります
- 本番環境ではRedisの設定を確認してください

### 認証機能でエラーが発生する場合
- `SECRET_KEY`環境変数が設定されているか確認
- JWT依存関係が正しくインストールされているか確認

## 参考リンク

- [環境設定ガイド](environment-setup.md)
- [本番デプロイメントガイド](../deployment/deployment-guide.md)
- [API仕様書](../api/rag_api_spec.md)

---

## 運用ルール・開発フロー

> 以下は現状の運用ルールのドラフトです。

### ブランチ戦略
- `main`: 本番環境用。リリース済み安定版のみマージ可
- `develop`: 開発統合ブランチ。日常的な開発はここにマージ
- `feature/*`: 新機能・改修ごとに作成（例: `feature/llm-response-enhance`）
- `hotfix/*`: 緊急修正用。バグ修正や障害対応時のみ

### レビュー手順
- **Pull Request作成時**: タイトル・説明・関連Issueを明記
- **レビュー観点**: コード品質、テストカバレッジ、セキュリティ、UI/UX
- **マージ条件**: 原則2名以上のApprove、CIテスト通過必須

### テスト観点
- **ユニットテスト**: Jest（FE）/pytest（BE）で主要ロジックを網羅
- **統合テスト**: Playwright（E2E）/FastAPI TestClient
- **カバレッジ目標**: 80%以上（未達時は理由をPRに記載）

---

## UI設計・アーキテクチャ判断

### Assistant UI 廃止について

**2025年6月24日決定**: @assistant-ui/reactコンポーネントを完全削除し、React標準のuseStateベースの自作チャットUIに移行

#### 理由
- **複雑性の削減**: シンプルで理解しやすい実装
- **デバッグ性向上**: 問題の追跡・修正が容易
- **互換性問題回避**: ストリーム処理の互換性問題を完全回避
- **カスタマイズ自由度**: 機能追加・UI変更の柔軟性向上

#### 削除した依存関係
- @assistant-ui/react: ^0.10.9
- @assistant-ui/react-ai-sdk: ^0.10.9  
- @assistant-ui/react-markdown: ^0.10.3
- @ai-sdk/openai, ai, remark-gfm

#### 新アーキテクチャ
- React標準のuseStateベースの自作チャットUI実装
- FastAPIを通常のJSONレスポンス形式に変更
- shadcn/uiベースのサイドバーレイアウトは維持
