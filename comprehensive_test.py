#!/usr/bin/env python3
"""修正後の包括的テスト"""

import sys
import os
sys.path.append('backend')
os.environ["BACKEND_TESTING"] = "true"
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"

from backend.app.services.database_service import DatabaseService

def comprehensive_test():
    """修正後の包括的テスト"""
    
    db_service = DatabaseService()
    db_service.reload_data()
    
    print("=== 包括的修正テスト ===")
    
    test_cases = [
        # keywords検索
        "ファンファーレを持つカード",
        "ラストワードを持つカード", 
        "疾走を持つカード",
        "守護を持つカード",
        "突進を持つカード",
        "必殺を持つカード",
        
        # 単一キーワード
        "ファンファーレ",
        "ラストワード",
        "疾走",
        "守護",
        "突進",
        "必殺",
        
        # 複合条件
        "ファンファーレ効果を持つエルフカード",
        "疾走効果を持つロイヤルカード",
        "守護効果を持つ3コストカード",
        
        # 他の検索（影響ないことを確認）
        "3コストカード",
        "エルフカード",
        "HP100以上のカード"
    ]
    
    for query in test_cases:
        print(f"\n【{query}】")
        try:
            result = db_service.filter_search_llm(query, top_k=2)
            print(f"結果: {result}")
        except Exception as e:
            print(f"エラー: {e}")
    
    print("\n=== テスト完了 ===")

if __name__ == '__main__':
    comprehensive_test()
