"""
MVP向けの最小conftest
- レガシー分類/ハイブリッド関連のモジュールやモックは読み込まない
- 必要最低限の環境変数とロギングのみ
"""
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from app.core.logging import GameChatLogger


# 環境変数（テスト用）
os.environ.setdefault("BACKEND_ENVIRONMENT", "test")
os.environ.setdefault("BACKEND_LOG_LEVEL", "CRITICAL")
os.environ.setdefault("BACKEND_TESTING", "true")
os.environ.setdefault("BACKEND_MOCK_EXTERNAL_SERVICES", "true")

# .env のロード（存在すれば）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=True)

# ロギング設定
GameChatLogger.configure_logging()


@pytest.fixture(autouse=True)
def _sanitize_openai_env(monkeypatch):
    """外部APIキーが参照されないように無効化"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("BACKEND_OPENAI_API_KEY", "")
    # settings経由の値もNoneに
    try:
        monkeypatch.setattr("app.core.config.settings.BACKEND_OPENAI_API_KEY", None, raising=False)
    except Exception:
        pass

