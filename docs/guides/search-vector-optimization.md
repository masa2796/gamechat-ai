# ベクトルDB検索実装ガイド

> **ARCHIVE_CANDIDATE**: ハイブリッド検索や動的閾値などMVPで無効化した機能の手引きです。

## 実装された機能

### 1. 分類ベース検索パラメータ

#### **動的閾値設定**
```python
# 分類タイプ別の類似度閾値
"similarity_thresholds": {
    "semantic": 0.75,      # セマンティック検索は高い閾値
    "hybrid": 0.70,        # ハイブリッドは中程度
    "filterable": 0.65     # フィルタ可能は低めに設定
}
```

#### **信頼度による調整**
- **高信頼度** (0.8以上): 検索件数を120%に増加、閾値を90%に調整
- **中信頼度** (0.5-0.8): 標準設定を使用、閾値を80%に調整  
- **低信頼度** (0.5未満): 検索件数を80%に削減、閾値を70%に調整

### 2. ネームスペース最適化

#### **分類タイプ別優先順位**

**セマンティック検索** (意味的検索重視):
```python
["summary", "flavor", "attacks", "evolves", "type", "category", ...]
```

**フィルタ可能検索** (具体的属性重視):
```python
["hp", "type", "weakness", "category", "rarity", "attacks", ...]
```

**ハイブリッド検索** (バランス重視):
```python
["summary", "hp", "type", "attacks", "flavor", "weakness", ...]
```

### 3. 検索品質評価システム

#### **品質指標**
- `overall_score`: 総合品質スコア
- `has_high_confidence_results`: 高信頼度結果の有無
- `avg_score`: 平均スコア
- `result_count`: 結果件数

#### **品質に基づく適応的マージ**
- **高品質** (overall_score > 0.8): 標準マージを実行
- **低品質** (overall_score < 0.5): 包括的マージで結果を増強

### 4. エラーハンドリング・フォールバック

#### **段階的フォールバック戦略**
1. **ネームスペース単位のエラー**: 他のネームスペースで継続
2. **結果なし**: 分類に基づく検索提案を生成
3. **全体エラー**: ユーザーフレンドリーなエラーメッセージ

#### **分類別検索提案**
```python
# セマンティック検索の提案例
"• より具体的なカード名やゲーム名で検索"
"• 「技」「HP」「タイプ」などの具体的な属性を含めた検索"

# フィルタ可能検索の提案例  
"• 数値条件を調整（例：HP100以上 → HP80以上）"
"• 複数条件を単一条件に簡素化"
```

## 設定項目詳細

### `backend/app/core/config.py`

```python
VECTOR_SEARCH_CONFIG = {
    # 分類タイプ別の類似度閾値
    "similarity_thresholds": {
        "semantic": 0.75,
        "hybrid": 0.70, 
        "filterable": 0.65
    },
    
    # 分類タイプ別の検索件数
    "search_limits": {
        "semantic": {"vector": 15, "db": 5},
        "hybrid": {"vector": 10, "db": 10},
        "filterable": {"vector": 5, "db": 20}
    },
    
    # 信頼度による調整係数
    "confidence_adjustments": {
        "high": 0.9,    # 0.8以上
        "medium": 0.8,  # 0.5-0.8
        "low": 0.7      # 0.5未満
    },
    
    # 重み付けマージの係数
    "merge_weights": {
        "db_weight": 0.4,
        "vector_weight": 0.6
    },
    
    # 最小スコア閾値
    "minimum_score": 0.5,
    
    # フォールバック設定
    "fallback_enabled": True,
    "fallback_limit": 3
}
```

## API応答の変更点

### 新しいレスポンス項目

```json
{
    "classification": {...},
    "search_strategy": {...},
    "db_results": [...],
    "vector_results": [...],
    "merged_results": [...],
    
    // 新規追加項目
    "search_quality": {
        "overall_score": 0.85,
        "db_quality": 0.82,
        "vector_quality": 0.88,
        "result_count": 5,
        "has_high_confidence_results": true,
        "avg_score": 0.85
    },
    "optimization_applied": true
}
```

## パフォーマンス向上

### **検索精度の向上**
- 分類タイプに適した閾値設定により、関連性の低い結果を除外
- ネームスペース優先順位により、重要な情報を優先的に検索

### **レスポンス時間の最適化**  
- 信頼度に基づく検索件数調整により、不要な検索を削減
- 品質評価による適応的マージで、低品質時のみ包括的処理を実行

### **ユーザビリティの向上**
- 結果なし時の建設的な提案により、ユーザーの再検索をサポート
- エラー時の分かりやすいメッセージで、技術的問題を隠蔽

## 下位互換性

既存のAPI呼び出しは引き続き動作します：

```python
# 既存の呼び出し（最適化なし）
await vector_service.search(embedding, top_k=10)

# 新しい呼び出し（最適化あり）  
await vector_service.search(
    embedding, 
    top_k=10,
    classification=classification_result
)
```

## 監視・デバッグ

### **ログ出力の強化**
```
=== 最適化されたベクトル検索開始 ===
検索対象ネームスペース: ['summary', 'flavor', ...]
最大取得件数: 15
最小スコア閾値: 0.675
分類タイプ: QueryType.SEMANTIC
信頼度: 0.85

[VectorService] パラメータ最適化完了:
  top_k: 15, min_score: 0.675
  信頼度レベル: high
```

### **品質メトリクスの追跡**
- 検索品質スコアによる継続的な性能監視
- 分類タイプ別の成功率測定
- フォールバック発生率の監視

## 今後の拡張可能性

### **機械学習による最適化**
- 検索履歴に基づく閾値の動的調整
- ユーザー行動データを活用した個人化

### **マルチモーダル対応**
- 画像埋め込みとの統合
- 音声検索クエリの対応

### **リアルタイム最適化**
- A/Bテストによるパラメータ調整
- リアルタイム品質フィードバック

---

この実装により、ベクトルDB検索の精度と効率性が大幅に向上し、ユーザーにとってより価値のある検索体験を提供できるようになりました。
