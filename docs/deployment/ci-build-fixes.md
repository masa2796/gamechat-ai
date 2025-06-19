# CI環境ビルド修正ガイド

## 問題の概要
Firebase認証の初期化がCI環境でのビルド時にエラーを引き起こしていました。

## 修正内容

### 1. Firebase初期化の安全化
- クライアントサイドでのみFirebaseを初期化
- CI環境では初期化をスキップ
- 無効なAPIキーでの初期化を防止

### 2. 環境変数の設定
- CI環境用のダミー値を設定
- `next.config.js`で環境変数のデフォルト値を定義

### 3. ビルドスクリプトの追加
- `build:ci`スクリプトを追加
- CI環境フラグを明示的に設定

## CI環境でのビルド方法

```bash
# CI環境でのビルド
cd frontend
npm run build:ci

# または環境変数を直接指定
CI=true NODE_ENV=production npm run build
```

## ローカル開発環境への影響
この修正はローカル開発環境には影響しません。Firebase認証が必要な場合は、適切な環境変数を設定してください。

## Firebase Hosting用ビルド
Firebase Hostingへのデプロイ時は、従来通り以下のコマンドを使用：

```bash
npm run build:firebase
```

## トラブルシューティング

### Firebase初期化エラーが発生する場合
1. `.env.ci`ファイルの内容を確認
2. `next.config.js`の環境変数設定を確認
3. `assistant.tsx`のFirebase初期化ロジックを確認

### CI環境で異なるエラーが発生する場合
環境変数`CI=true`が設定されていることを確認してください。
