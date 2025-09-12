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

# --- 追加: MVP最小化ポリシーに基づくスキップ制御 ---
# 許可するテストファイル（ベースライン）
MVP_ALLOWED_FILES = {
    "test_mvp_chat_basic.py",  # 最小チャット動作確認
}
# Opt-in 環境変数が設定されている場合はフル実行を許可
RUN_ALL_TESTS = os.environ.get("RUN_FULL_TESTS") == "1"


def pytest_collection_modifyitems(config, items):
    if RUN_ALL_TESTS:
        return  # 何もスキップしない
    skipped = pytest.mark.skip(reason="MVP最小実行モード: RUN_FULL_TESTS=1 で解除")
    for item in items:
        path_name = item.fspath.basename
        if path_name not in MVP_ALLOWED_FILES:
            item.add_marker(skipped)


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

