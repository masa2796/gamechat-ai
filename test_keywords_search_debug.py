#!/usr/bin/env python3
"""keywords検索機能のテスト用スクリプト"""

import sys
import os
sys.path.append('backend')
os.environ["BACKEND_TESTING"] = "true"
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"

from backend.app.services.database_service import DatabaseService

def test_keywords_search():
    """keywords検索のテスト"""
    print("=== keywords検索機能テスト ===")
    
    # DatabaseServiceを初期化
    db_service = DatabaseService()
    print('DatabaseService初期化完了')
    
    # データをロード
    db_service.reload_data()
    print(f'データ件数: {len(db_service.data_cache)}')
    
    # keywordsフィールドがあるカードをいくつか確認
    print('\n=== keywordsフィールドを持つカードのサンプル ===')
    sample_count = 0
    keywords_summary = {}
    
    for item in db_service.data_cache:
        keywords = item.get('keywords', [])
        if keywords and isinstance(keywords, list) and len(keywords) > 0:
            if sample_count < 5:
                print(f'カード名: {item.get("name", "")}')
                print(f'keywords: {keywords}')
                print(f'クラス: {item.get("class", "")}')
                print('---')
                sample_count += 1
            
            # 各キーワードの使用回数をカウント
            for keyword in keywords:
                if keyword in keywords_summary:
                    keywords_summary[keyword] += 1
                else:
                    keywords_summary[keyword] = 1
    
    print(f'\n=== 使用可能なkeywords一覧 (全{len(keywords_summary)}種類) ===')
    for keyword, count in sorted(keywords_summary.items(), key=lambda x: x[1], reverse=True):
        print(f'{keyword}: {count}件')
    
    print('\n=== keywords検索テスト ===')
    
    # テスト1: ファンファーレで検索
    print('テスト1: 「ファンファーレ」で検索')
    try:
        result = db_service.filter_search(['ファンファーレ'], top_k=3)
        print(f'結果: {result}')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
    
    # テスト2: ラストワードで検索
    print('\nテスト2: 「ラストワード」で検索')
    try:
        result = db_service.filter_search(['ラストワード'], top_k=3)
        print(f'結果: {result}')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
    
    # テスト3: コンボで検索
    print('\nテスト3: 「コンボ」で検索')
    try:
        result = db_service.filter_search(['コンボ'], top_k=3)
        print(f'結果: {result}')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
    
    # テスト4: 疾走で検索
    print('\nテスト4: 「疾走」で検索')
    try:
        result = db_service.filter_search(['疾走'], top_k=3)
        print(f'結果: {result}')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
    
    # テスト5: LLMベース検索のテスト
    print('\n=== LLMベース検索テスト ===')
    
    # テスト5-1: ファンファーレ効果を持つカードで検索
    print('テスト5-1: 「ファンファーレ効果を持つカード」で検索')
    try:
        result = db_service.filter_search_llm('ファンファーレ効果を持つカード', top_k=3)
        print(f'結果: {result}')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()
    
    # テスト5-2: ファンファーレエルフで検索
    print('\nテスト5-2: 「ファンファーレ効果を持つエルフカード」で検索')
    try:
        result = db_service.filter_search_llm('ファンファーレ効果を持つエルフカード', top_k=3)
        print(f'結果: {result}')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_keywords_search()
