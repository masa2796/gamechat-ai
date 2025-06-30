import os
import json
import openai
from dotenv import load_dotenv
from pathlib import Path

# プロジェクトルートディレクトリを取得
project_root = Path(__file__).parent.parent
dotenv_path = project_root / 'backend' / '.env'  # backend/.envのみ参照
load_dotenv(dotenv_path=dotenv_path)
openai.api_key = os.getenv("BACKEND_OPENAI_API_KEY")

def build_text(data):
    return data.get('text', '')

def main():
    # 環境変数からパスを取得、なければデフォルトパスを使用
    data_path = os.getenv("CONVERTED_DATA_FILE_PATH", str(project_root / 'data' / 'convert_data.json'))
    out_path = os.getenv("EMBEDDING_FILE_PATH", str(project_root / 'data' / 'embedding_list.jsonl'))
    
    with open(data_path, encoding='utf-8') as f:
        data_list = json.load(f)

    for data in data_list:
        text = build_text(data)
        print(f"Embedding対象テキスト: {text}")

        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding

        with open(out_path, 'a', encoding='utf-8') as f_out:
            f_out.write(json.dumps({
                "id": data.get("id"),  
                "namespace": data.get("namespace"),
                "text": text,
                "embedding": embedding
            }, ensure_ascii=False) + '\n')

        print(f"ベクトルを {out_path} に追記しました。")

if __name__ == "__main__":
    main()