# ユーティリティスクリプト

このディレクトリには、GameChat AIの開発・運用で使用するユーティリティスクリプトが含まれています。

## 🛠️ スクリプト一覧

### 📊 データ処理スクリプト

#### [`convert_to_format.py`](./convert_to_format.py)
**データ形式変換スクリプト**
- 生データから検索用フォーマットへの変換
- JSON形式の正規化とバリデーション
- 埋め込み用データの前処理

```bash
# 使用方法
python convert_to_format.py --input raw_data.json --output formatted_data.json
```

#### [`embedding.py`](./embedding.py)
**埋め込み生成スクリプト**
- OpenAI APIを使用した埋め込みベクトル生成
- バッチ処理による効率的な埋め込み作成
- 生成済み埋め込みのJSONL形式出力

```bash
# 使用方法
python embedding.py --input data.json --output embedding_list.jsonl
```

### 🔗 外部サービス連携

#### [`upstash_connection.py`](./upstash_connection.py)
**Upstash Vector接続スクリプト**
- 埋め込みデータのUpstash Vectorへのアップロード
- ネームスペース別のデータ管理
- バッチアップロードとエラーハンドリング

```bash
# 使用方法
python upstash_connection.py --file embedding_list.jsonl --namespace default
```

### 🧪 テスト・デバッグスクリプト

#### [`test_greeting_detection.py`](./test_greeting_detection.py)
**挨拶検出テストスクリプト**
- 挨拶検出機能の統合テスト
- 早期応答システムの動作確認
- パフォーマンス測定と精度評価

```bash
# 使用方法
python test_greeting_detection.py
```

#### [`test_performance.py`](./test_performance.py)
**パフォーマンステストスクリプト**
- システム全体のパフォーマンス測定
- 応答時間・メモリ使用量の計測
- 検索精度の統計的評価

```bash
# 使用方法
python test_performance.py --iterations 100 --output results.json
```

## 🚀 使用方法

### 初回セットアップ
```bash
# 必要なパッケージのインストール
pip install -r ../../requirements.txt

# 環境変数の設定（.envファイルの作成）
cp ../../.env.example ../../.env
# .envファイルを編集してAPIキーを設定
```

### データ処理フロー
```bash
# 1. データ形式変換
python convert_to_format.py --input raw_card_data.json --output formatted_data.json

# 2. 埋め込み生成
python embedding.py --input formatted_data.json --output embedding_list.jsonl

# 3. ベクトルDBへアップロード
python upstash_connection.py --file embedding_list.jsonl --namespace game_cards
```

### テスト・検証フロー
```bash
# 1. 挨拶検出テスト
python test_greeting_detection.py

# 2. パフォーマンステスト
python test_performance.py --iterations 50

# 3. 結果の確認
cat ../performance/performance_results.json
```

## ⚙️ スクリプト設定

### 共通環境変数
```bash
# .envファイルに設定が必要な項目
OPENAI_API_KEY=your_openai_api_key
UPSTASH_VECTOR_REST_URL=your_upstash_url
UPSTASH_VECTOR_REST_TOKEN=your_upstash_token
```

### スクリプト固有設定

#### embedding.py
```python
# 設定可能なパラメータ
BATCH_SIZE = 100          # バッチサイズ
MAX_RETRIES = 3          # 再試行回数
EMBEDDING_MODEL = "text-embedding-3-small"  # 埋め込みモデル
```

#### test_performance.py
```python
# テスト設定
TEST_ITERATIONS = 100    # テスト回数
TIMEOUT_SECONDS = 30     # タイムアウト時間
WARMUP_ITERATIONS = 5    # ウォームアップ回数
```

## 🔧 カスタマイズ方法

### 新しいスクリプトの追加
1. **スクリプトファイルの作成**
   ```python
   #!/usr/bin/env python3
   """
   新しいユーティリティスクリプトの説明
   """
   # スクリプトの実装
   ```

2. **READMEの更新**
   - 本ファイルにスクリプトの説明を追加
   - 使用方法とオプションを記載

3. **権限設定**
   ```bash
   chmod +x new_script.py
   ```

### 既存スクリプトの拡張
1. **機能追加時**
   - 既存のコード構造を維持
   - コマンドライン引数の追加
   - 適切なエラーハンドリング

2. **設定項目追加時**
   - 環境変数または設定ファイルを使用
   - デフォルト値の提供
   - バリデーション機能の実装

## 🐛 トラブルシューティング

### よくある問題

#### APIキーエラー
```
Error: OpenAI API key not found
```
**解決方法**: `.env`ファイルにAPIキーが正しく設定されているか確認

#### Upstash接続エラー
```
Error: Failed to connect to Upstash Vector
```
**解決方法**: ネットワーク接続とUpstash認証情報を確認

#### メモリ不足エラー
```
Error: Out of memory during embedding generation
```
**解決方法**: バッチサイズを小さくして再実行

### デバッグ方法
```bash
# 詳細ログの有効化
export PYTHONPATH=../..
export LOG_LEVEL=DEBUG
python script_name.py --verbose
```

## 📊 監視・ログ

### ログファイル
- **実行ログ**: `logs/script_execution.log`
- **エラーログ**: `logs/error.log`
- **パフォーマンスログ**: `logs/performance.log`

### 監視項目
- スクリプト実行時間
- API呼び出し回数
- メモリ使用量
- エラー発生率

## 🔄 定期実行設定

### cron設定例
```bash
# 毎日午前2時にパフォーマンステストを実行
0 2 * * * cd /path/to/docs/scripts && python test_performance.py

# 週次でデータ更新
0 3 * * 0 cd /path/to/docs/scripts && python embedding.py --update
```