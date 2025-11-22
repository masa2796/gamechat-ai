import os

# 環境変数を未設定にして VectorService が Upstash を利用できない状態を作る
os.environ.pop("UPSTASH_VECTOR_REST_URL", None)
os.environ.pop("UPSTASH_VECTOR_REST_TOKEN", None)
os.environ.setdefault("BACKEND_TESTING", "true")
os.environ.setdefault("BACKEND_MOCK_EXTERNAL_SERVICES", "true")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_vector_fallback_generates_dummy_titles():
    resp = client.post("/chat", json={"message": "フォールバック確認テスト", "top_k": 4, "with_context": False})
    assert resp.status_code == 200
    data = resp.json()
    assert "retrieved_titles" in data
    titles = data["retrieved_titles"]
    assert isinstance(titles, list)
    # Upstash未設定のためフォールバックダミータイトル（"カード123" 形式）が生成される想定
    # 件数は top_k 以下
    assert len(titles) <= 4
    # 少なくとも1件は生成される期待（embedding擬似値→sha1ベース）
    assert len(titles) >= 1
    assert all(t.startswith("カード") for t in titles)
