# データ処理スクリプト

ゲームデータの変換・埋め込み生成・アップロードに使用するスクリプト集です。

## 📊 スクリプト一覧

### [`convert_to_format.py`](./convert_to_format.py) - データ変換
**用途**: 生データから検索用フォーマットへの変換
- JSON形式の正規化とバリデーション
- 埋め込み用テキストの前処理

```bash
python convert_to_format.py --input raw_data.json --output formatted_data.json
```

### [`embedding.py`](./embedding.py) - 埋め込み生成
**用途**: OpenAI APIを使用した埋め込みベクトル生成
- バッチ処理による効率的な処理
- JSONL形式での出力

```bash
python embedding.py --input data.json --output embedding_list.jsonl
```

### [`upstash_connection.py`](./upstash_connection.py) - Vector DBアップロード
**用途**: 埋め込みベクトルのUpstash Vector DBへのアップロード
- ネームスペース設定
- バッチアップロード機能

```bash
python upstash_connection.py
```

## 🔄 データ処理フロー

1. **データ変換**: `convert_to_format.py`で生データを変換
2. **埋め込み生成**: `embedding.py`でベクトル化
3. **DBアップロード**: `upstash_connection.py`でVector DBに保存

## 📋 前提条件

- Python 3.8以上
- 必要な環境変数の設定（BACKEND_OPENAI_API_KEY, UPSTASH_VECTOR_*）
- データファイルの準備

## ⚠️ 注意事項

- OpenAI APIの使用量制限に注意
- 大容量データの処理時はバッチサイズを調整
- 本番データの処理は十分注意して実行

---
**最終更新**: 2025年6月17日
