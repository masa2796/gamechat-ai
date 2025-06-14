# モックオブジェクト整理 - 使用ガイド

## 概要

issue #59の対応として、テスト用のモックオブジェクトを統合・整理しました。従来の冗長なモック作成を排除し、再利用可能なファクトリーパターンを採用しています。

## 新しいモックシステムの構成

### 1. ディレクトリ構造

```
backend/app/tests/mocks/
├── __init__.py          # モジュールエクスポート
├── service_mocks.py     # サービス用モッククラス
└── factories.py         # ファクトリーパターン実装
```

### 2. 主要コンポーネント

#### service_mocks.py
- `MockUpstashResult`: Upstash検索結果のモック
- `MockClassificationResult`: 分類結果生成のモッククラス  
- `MockOpenAIResponse`: OpenAI APIレスポンスのモック
- `MockDatabaseConnection`: データベース接続のモック

#### factories.py
- `ContextItemFactory`: ContextItemのファクトリー
- `ClassificationResultFactory`: ClassificationResultのファクトリー
- `TestScenarioFactory`: 複合テストシナリオのファクトリー

## 使用方法

### Before（従来の冗長な方法）

```python
# 従来: 毎回手動でモックを作成
mock_client = MagicMock()
mock_response = MagicMock()
mock_response.choices = [MagicMock()]
mock_response.choices[0].message.content = """{
    "query_type": "semantic",
    "summary": "強いポケモンの検索",
    "confidence": 0.8,
    "filter_keywords": [],
    "search_keywords": ["強い", "ポケモン"],
    "reasoning": "セマンティック検索として分類"
}"""
mock_client.chat.completions.create.return_value = mock_response
```

### After（新しいモックシステム）

```python
from backend.app.tests.mocks import MockOpenAIResponse

# 新しい方法: ファクトリーを使用
mock_response = MockOpenAIResponse.create_classification_response(
    query_type="semantic",
    summary="強いポケモンの検索",
    confidence=0.8,
    search_keywords=["強い", "ポケモン"],
    filter_keywords=[]
)

mock_client = MagicMock()
mock_client.chat.completions.create.return_value = mock_response
```

### 実践例

#### 1. ContextItemの生成

```python
from backend.app.tests.mocks import ContextItemFactory

# 高品質アイテムを3つ生成
high_quality_items = ContextItemFactory.create_high_score_items(count=3, base_score=0.9)

# ポケモン関連アイテムを生成
pokemon_items = ContextItemFactory.create_pokemon_items(count=5)

# 混在品質アイテムを生成
mixed_items = ContextItemFactory.create_mixed_quality_items(high_count=2, low_count=3)
```

#### 2. 分類結果の生成

```python
from backend.app.tests.mocks import MockClassificationResult

# セマンティック分類
semantic = MockClassificationResult.create_semantic(confidence=0.85)

# フィルター分類  
filterable = MockClassificationResult.create_filterable(confidence=0.9)

# 挨拶分類
greeting = MockClassificationResult.create_greeting()
```

#### 3. 検索結果の生成

```python
from backend.app.tests.mocks import MockUpstashResult

# ポケモン検索結果
pokemon_results = MockUpstashResult.create_pokemon_results(count=3)

# 高スコア検索結果
high_score_results = MockUpstashResult.create_high_score_results(count=3, base_score=0.9)

# 空の検索結果
empty_results = MockUpstashResult.create_empty_result()
```

#### 4. 複合シナリオの生成

```python
from backend.app.tests.mocks import TestScenarioFactory

# 成功する検索シナリオ
success_scenario = TestScenarioFactory.create_successful_pokemon_search()
query = success_scenario["query"]
classification = success_scenario["classification"] 
context_items = success_scenario["context_items"]

# 挨拶シナリオ
greeting_scenario = TestScenarioFactory.create_greeting_scenario()

# エラーシナリオ
error_scenario = TestScenarioFactory.create_low_quality_scenario()
```

## 効果と改善

### 1. コード重複の削除
- 従来: 20回以上の`mock_response.choices`重複
- 改善後: 1回のファクトリー呼び出し

### 2. テストの可読性向上
- 意図が明確な関数名（`create_high_score_items`など）
- 複雑なモック設定の隠蔽

### 3. メンテナンス性向上
- モック変更時の影響範囲を限定
- 一元的なモック管理

### 4. 型安全性の向上
- 適切な型ヒント付き
- IDEでの補完サポート

## 移行ガイド

既存テストのリファクタリング手順：

1. `from backend.app.tests.mocks import ...` をインポート
2. 冗長なモック作成をファクトリー呼び出しに置換
3. テスト実行で動作確認
4. 不要なモック作成コードを削除

## 参考

- 実装例: `backend/app/tests/test_mock_system_examples.py`
- リファクタリング例: `backend/app/tests/services/test_classification_consolidated.py`
- フィクスチャー: `backend/app/tests/conftest.py`
