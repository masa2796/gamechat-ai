import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    RECAPTCHA_SECRET: str = os.getenv("RECAPTCHA_SECRET_TEST")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    UPSTASH_VECTOR_REST_URL: str = os.getenv("UPSTASH_VECTOR_REST_URL")
    UPSTASH_VECTOR_REST_TOKEN: str = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    # ベクトル検索設定
    VECTOR_SEARCH_CONFIG = {
        # 分類タイプ別の類似度閾値
        "similarity_thresholds": {
            "semantic": 0.75,      # セマンティック検索は高い閾値
            "hybrid": 0.70,        # ハイブリッドは中程度
            "filterable": 0.65     # フィルタ可能は低めに設定
        },
        
        # 分類タイプ別の検索件数
        "search_limits": {
            "semantic": {"vector": 15, "db": 5},     # セマンティックはベクトル重視
            "hybrid": {"vector": 10, "db": 10},      # ハイブリッドは均等
            "filterable": {"vector": 5, "db": 20}    # フィルタ可能はDB重視
        },
        
        # 信頼度による調整係数
        "confidence_adjustments": {
            "high": 0.9,      # 0.8以上の信頼度
            "medium": 0.8,    # 0.5-0.8の信頼度
            "low": 0.7        # 0.5未満の信頼度
        },
        
        # 重み付けマージの係数
        "merge_weights": {
            "db_weight": 0.4,
            "vector_weight": 0.6
        },
        
        # 最小スコア閾値（これ以下は除外）
        "minimum_score": 0.5,
        
        # フォールバック設定
        "fallback_enabled": True,
        "fallback_limit": 3
    }

settings = Settings()