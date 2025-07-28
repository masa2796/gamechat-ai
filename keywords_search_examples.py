#!/usr/bin/env python3
"""keywords検索の使用例とベストプラクティス"""

import sys
import os
sys.path.append('backend')
os.environ["BACKEND_TESTING"] = "true"
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"

from backend.app.services.database_service import DatabaseService

def demonstrate_keywords_search():
    """keywords検索の使用例を実演"""
    
    db_service = DatabaseService()
    db_service.reload_data()
    
    print("=== keywords検索の使用例 ===")
    
    # 例1: 特定の効果キーワードで検索
    examples = [
        "ファンファーレ",
        "ラストワード", 
        "疾走",
        "守護",
        "進化時",
        "コンボ",
        "スペルブースト時",
        "ネクロマンス",
        "アクト"
    ]
    
    for keyword in examples:
        result = db_service.filter_search([keyword], top_k=2)
        print(f"【{keyword}】: {result}")
    
    print("\n=== 複合条件検索（keywords + クラス）===")
    
    # 例2: LLMベースでの複合条件検索
    complex_queries = [
        "ファンファーレ効果を持つエルフカード",
        "疾走効果を持つロイヤルカード", 
        "守護効果を持つドラゴンカード",
        "ラストワード効果を持つネクロマンサーカード"
    ]
    
    for query in complex_queries:
        result = db_service.filter_search_llm(query, top_k=2)
        print(f"【{query}】: {result}")
    
    print("\n=== keywords + 数値条件の複合検索 ===")
    
    # 例3: より複雑な複合条件
    advanced_queries = [
        "ファンファーレ効果を持つ3コストカード",
        "疾走効果を持つ攻撃力3以上のカード",
        "守護効果を持つHP5以上のカード"
    ]
    
    for query in advanced_queries:
        result = db_service.filter_search_llm(query, top_k=2)
        print(f"【{query}】: {result}")

if __name__ == '__main__':
    demonstrate_keywords_search()
