import os
import json
import openai
from dotenv import load_dotenv
from pathlib import Path

# プロジェクトルートディレクトリを取得
project_root = Path(__file__).resolve().parent.parent.parent
backend_env_path = project_root / 'backend' / '.env'
load_dotenv(dotenv_path=backend_env_path)
openai_api_key = os.getenv("BACKEND_OPENAI_API_KEY")
openai.api_key = openai_api_key

def main():
    # 相対パスでデータファイルを指定
    data_path = project_root / 'data' / 'convert_data.json'
    out_path = project_root / 'data' / 'embedding_list.jsonl'

    if not data_path.exists():
        print(f"Error: 入力ファイルが存在しません: {data_path}")
        return

    with open(data_path, encoding='utf-8') as f:
        data_list = json.load(f)

    for data in data_list:
        text = data.get('text', '')
        namespace = data.get('namespace', 'default')
        print(f"Embedding対象テキスト: {text}")

        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding

        with open(out_path, 'a', encoding='utf-8') as f_out:
            f_out.write(json.dumps({
                "id": data.get("id"),  
                "namespace": namespace,
                "embedding": embedding,
                "metadata": {namespace: text}
            }, ensure_ascii=False) + '\n')

        print(f"ベクトルを {out_path} に追記しました。")

if __name__ == "__main__":
    main()