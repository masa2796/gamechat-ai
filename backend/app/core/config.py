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

    def __init__(self):
        # プロジェクトルート（デバッグ用）
        self.PROJECT_ROOT: Path = PROJECT_ROOT

        # 環境設定
        self.ENVIRONMENT: str = os.getenv("BACKEND_ENVIRONMENT", "development")
        self.BACKEND_ENVIRONMENT: str = os.getenv("BACKEND_ENVIRONMENT", "development")
        self.DEBUG: bool = os.getenv("BACKEND_DEBUG", "true").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("BACKEND_LOG_LEVEL", "INFO")

        # API Keys
        # RECAPTCHAは環境に応じて適切なキーを選択
        self.RECAPTCHA_SECRET: Optional[str] = os.getenv("RECAPTCHA_SECRET_KEY_TEST") if environment != "production" else os.getenv("RECAPTCHA_SECRET_KEY")
        self.RECAPTCHA_SITE: Optional[str] = os.getenv("RECAPTCHA_SITE")

        # OpenAI APIキー（backend/.envから読み込み）
        self.BACKEND_OPENAI_API_KEY: Optional[str] = (
            (v.strip() if v is not None else None)
            for v in [os.getenv("BACKEND_OPENAI_API_KEY")]
        ).__next__()

        # Upstash Vector設定（backend/.envから読み込み）
        self.UPSTASH_VECTOR_REST_URL: Optional[str] = os.getenv("UPSTASH_VECTOR_REST_URL")
        self.UPSTASH_VECTOR_REST_TOKEN: Optional[str] = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

        # CORS設定（デバッグ用に一時的に緩和）
        self.CORS_ORIGINS: List[str] = (
            [
                "https://gamechat-ai.web.app", 
                "https://gamechat-ai.firebaseapp.com",
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ] if environment == "production" 
            else os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        )

        # Security Settings
        self.SECRET_KEY: str = os.getenv("BACKEND_SECRET_KEY", "dev-secret-key-change-in-production")
        self.BCRYPT_ROUNDS: int = int(os.getenv("BACKEND_BCRYPT_ROUNDS", "12"))

        # Rate Limiting Settings
        self.RATE_LIMIT_ENABLED: bool = os.getenv("BACKEND_RATE_LIMIT_ENABLED", "true").lower() == "true"

        # API Authentication Settings
        self.API_KEY_HEADER: str = "X-API-Key"
        self.JWT_ALGORITHM: str = "HS256"
        self.JWT_EXPIRE_MINUTES: int = int(os.getenv("BACKEND_JWT_EXPIRE_MINUTES", "30"))

        # Redis Settings (for rate limiting and caching)
        self.REDIS_URL: Optional[str] = os.getenv("BACKEND_REDIS_URL")
        self.REDIS_HOST: str = os.getenv("BACKEND_REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("BACKEND_REDIS_PORT", "6379"))
        self.REDIS_DB: int = int(os.getenv("BACKEND_REDIS_DB", "0"))
        self.REDIS_PASSWORD: Optional[str] = os.getenv("BACKEND_REDIS_PASSWORD")

        # Database Settings
        self.DB_HOST: str = os.getenv("BACKEND_DB_HOST", "localhost")
        self.DB_PORT: int = int(os.getenv("BACKEND_DB_PORT", "5432"))
        self.DB_NAME: str = os.getenv("BACKEND_DB_NAME", "gamechat_ai")
        self.DB_USER: str = os.getenv("BACKEND_DB_USER", "postgres")
        self.DB_PASSWORD: str = os.getenv("BACKEND_DB_PASSWORD", "")

        # Monitoring and Observability
        self.SENTRY_DSN: Optional[str] = os.getenv("BACKEND_SENTRY_DSN")
        self.MONITORING_ENABLED: bool = os.getenv("MONITORING_ENABLED", "false").lower() == "true"

        # データディレクトリ・ファイルパス
        self.DATA_DIR = _get_data_dir()
        self.DATA_FILE_PATH = os.path.join(self.DATA_DIR, "data.json")
        self.EMBEDDING_FILE_PATH = os.path.join(self.DATA_DIR, "embedding_list.jsonl")
        self.QUERY_DATA_FILE_PATH = os.path.join(self.DATA_DIR, "query_data.json")
        self.CONVERTED_DATA_FILE_PATH = os.path.join(self.DATA_DIR, "convert_data.json")

        # Google Cloud Storage設定
        self.GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "gamechat-ai-data")
        self.GCS_PROJECT_ID: Optional[str] = os.getenv("GCS_PROJECT_ID")
        # 認証はCloud Runのサービスアカウントまたは環境変数GOOGLE_APPLICATION_CREDENTIALSを使用

        # ベクトル検索設定
        self.VECTOR_SEARCH_CONFIG = {
            # 分類タイプ別の類似度閾値
            "similarity_thresholds": {
                # 2025-08-27 tuning: 閾値が高すぎて全件0ヒットだったため全体を引き下げ
                # semantic * high_conf (0.6 * 0.8) ≒ 0.48 まで実効 min_score を緩和
                "semantic": 0.60,
                "hybrid": 0.55,
                "filterable": 0.50
            },
            # 分類タイプ別の検索件数
            "search_limits": {
                "semantic": {"vector": 15, "db": 5},     # セマンティックはベクトル重視
                "hybrid": {"vector": 10, "db": 10},      # ハイブリッドは均等
                "filterable": {"vector": 5, "db": 20}    # フィルタ可能はDB重視
            },
            # 信頼度による調整係数
            "confidence_adjustments": {
                # 閾値緩和に合わせ調整（過剰な信頼度掛け合わせで再び高止まりしないよう抑制）
                "high": 0.8,
                "medium": 0.75,
                "low": 0.7
            },
            # 重み付けマージの係数
            "merge_weights": {
                "db_weight": 0.4,
                "vector_weight": 0.6
            },
            # 最小スコア閾値（これ以下は除外）
            "minimum_score": 0.35,  # 2025-08-27: 全体調整に合わせ暫定的に下げる (再評価後に再調整予定)
            # フォールバック設定
            "fallback_enabled": True,
            "fallback_limit": 3,
            # plateau 検知 & combined 条件付き注入設定
            "plateau": {
                "enable_combined": os.getenv("VECTOR_ENABLE_COMBINED_PLATEAU", "true").lower() == "true",
                # top3 スコアの標準偏差がこの値未満 あるいは spread が下記閾値未満で plateau 扱い
                "stddev": float(os.getenv("COMBINED_PLATEAU_STDDEV", "0.005")),
                "score_spread": float(os.getenv("COMBINED_PLATEAU_SCORE_SPREAD", "0.01")),
                # combined 注入時に適用する base_min_score への加算Δ（Precision 保持）
                "combined_extra_min_score": float(os.getenv("COMBINED_EXTRA_MIN_SCORE", "0.02")),
                # combined 再検索の top_k （過剰取得抑制）
                "combined_top_k": int(os.getenv("COMBINED_PLATEAU_TOP_K", "12"))
            }
        }

    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """
        サービス層やテストから参照される共通APIキーエイリアス
        """
        return self.BACKEND_OPENAI_API_KEY
def _get_data_dir() -> str:
    # Docker環境では必ず /data を使う（.envや環境変数で上書き不可）
    if os.getenv("RUNNING_IN_DOCKER") == "1" or os.path.exists("/.dockerenv") or os.getenv("ENVIRONMENT") in ["production", "development"]:
        return "/data"
    # それ以外は環境変数→.env→ローカルdata
    try:
        from pathlib import Path
        _project_root = Path(__file__).resolve().parent.parent.parent
        return os.getenv("BACKEND_DATA_DIR") or str(_project_root / "data")
    except Exception:
        from pathlib import Path
        _project_root = Path(".")
        return os.getenv("BACKEND_DATA_DIR") or str(_project_root / "data")

settings = Settings()