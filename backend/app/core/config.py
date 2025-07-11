import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# プロジェクトルートディレクトリを先に定義
# Cloud Run環境では /app がプロジェクトルートになる
# ローカル環境では親ディレクトリを辿る
if os.getenv("BACKEND_ENVIRONMENT") == "production":
    PROJECT_ROOT = Path("/app")
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# 環境に応じて適切な.envファイルを読み込み（override=Trueで既存の環境変数を上書き）
environment = os.getenv("BACKEND_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
if environment == "production":
    # 本番環境: .env.productionが存在すればそれを読み込む
    prod_env_path = PROJECT_ROOT / "backend" / ".env.production"
    if prod_env_path.exists():
        load_dotenv(prod_env_path, override=True)
    else:
        # .env.productionがなければ.env.ciを利用
        ci_env_path = PROJECT_ROOT / "backend" / ".env.ci"
        if ci_env_path.exists():
            load_dotenv(ci_env_path, override=True)
elif environment == "test":
    # テスト環境: backend/.env.testファイルを優先的に読み込み
    load_dotenv(PROJECT_ROOT / "backend" / ".env.test", override=True)
else:
    # 開発環境: プロジェクトルートの.envファイル
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    # backend/.envファイルも読み込み（優先度高）
    load_dotenv(PROJECT_ROOT / "backend" / ".env", override=True)

class Settings:
    # プロジェクトルート（デバッグ用）
    PROJECT_ROOT: Path = PROJECT_ROOT
    
    # 環境設定
    ENVIRONMENT: str = os.getenv("BACKEND_ENVIRONMENT", "development")
    BACKEND_ENVIRONMENT: str = os.getenv("BACKEND_ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("BACKEND_DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("BACKEND_LOG_LEVEL", "INFO")
    
    # API Keys
    # RECAPTCHAは環境に応じて適切なキーを選択
    RECAPTCHA_SECRET: Optional[str] = os.getenv("RECAPTCHA_SECRET_KEY_TEST") if environment != "production" else os.getenv("RECAPTCHA_SECRET_KEY")
    RECAPTCHA_SITE: Optional[str] = os.getenv("RECAPTCHA_SITE")
    
    # OpenAI APIキー（backend/.envから読み込み）
    BACKEND_OPENAI_API_KEY: Optional[str] = (
        (v.strip() if v is not None else None)
        for v in [os.getenv("BACKEND_OPENAI_API_KEY")]
    ).__next__()
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """
        サービス層やテストから参照される共通APIキーエイリアス
        """
        return self.BACKEND_OPENAI_API_KEY

    # Upstash Vector設定（backend/.envから読み込み）
    UPSTASH_VECTOR_REST_URL: Optional[str] = os.getenv("UPSTASH_VECTOR_REST_URL")
    UPSTASH_VECTOR_REST_TOKEN: Optional[str] = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    # CORS設定（デバッグ用に一時的に緩和）
    CORS_ORIGINS: List[str] = (
        [
            "https://gamechat-ai.web.app", 
            "https://gamechat-ai.firebaseapp.com",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ] if environment == "production" 
        else os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    )
    
    # Security Settings
    SECRET_KEY: str = os.getenv("BACKEND_SECRET_KEY", "dev-secret-key-change-in-production")
    BCRYPT_ROUNDS: int = int(os.getenv("BACKEND_BCRYPT_ROUNDS", "12"))
    
    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = os.getenv("BACKEND_RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    # API Authentication Settings
    API_KEY_HEADER: str = "X-API-Key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("BACKEND_JWT_EXPIRE_MINUTES", "30"))
    
    # Redis Settings (for rate limiting and caching)
    REDIS_URL: Optional[str] = os.getenv("BACKEND_REDIS_URL")
    REDIS_HOST: str = os.getenv("BACKEND_REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("BACKEND_REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("BACKEND_REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("BACKEND_REDIS_PASSWORD")
    
    # Database Settings
    DB_HOST: str = os.getenv("BACKEND_DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("BACKEND_DB_PORT", "5432"))
    DB_NAME: str = os.getenv("BACKEND_DB_NAME", "gamechat_ai")
    DB_USER: str = os.getenv("BACKEND_DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("BACKEND_DB_PASSWORD", "")
    
    # Monitoring and Observability
    SENTRY_DSN: Optional[str] = os.getenv("BACKEND_SENTRY_DSN")
    MONITORING_ENABLED: bool = os.getenv("MONITORING_ENABLED", "false").lower() == "true"
    
    # データファイルパス設定
    # Cloud Run（production）では必ず /tmp/data を使う。環境変数が /data など不正な場合も自動補正。
    _raw_data_dir = os.getenv("BACKEND_DATA_DIR")
    if BACKEND_ENVIRONMENT == "production":
        if _raw_data_dir and not _raw_data_dir.startswith("/tmp"):
            import logging
            logging.warning(f"[config] BACKEND_DATA_DIR='{_raw_data_dir}' はCloud Runでは無効です。/tmp/dataに強制します。")
            DATA_DIR = "/tmp/data"
        else:
            DATA_DIR = _raw_data_dir or "/tmp/data"
    else:
        DATA_DIR = _raw_data_dir or os.path.join(str(PROJECT_ROOT), "data")
    DATA_FILE_PATH = os.path.join(DATA_DIR, "data.json")
    EMBEDDING_FILE_PATH = os.path.join(DATA_DIR, "embedding_list.jsonl")
    QUERY_DATA_FILE_PATH = os.path.join(DATA_DIR, "query_data.json")
    CONVERTED_DATA_FILE_PATH = os.path.join(DATA_DIR, "convert_data.json")
    
    # Google Cloud Storage設定
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "gamechat-ai-data")
    GCS_PROJECT_ID: Optional[str] = os.getenv("GCS_PROJECT_ID")
    # 認証はCloud Runのサービスアカウントまたは環境変数GOOGLE_APPLICATION_CREDENTIALSを使用
    
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