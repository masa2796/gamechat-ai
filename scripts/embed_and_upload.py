import os
import json
import openai
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path)
openai.api_key = os.getenv("OPENAI_API_KEY")

def build_text(data):
    return data.get('text', '')

def main():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'embedding_data.json')
    with open(data_path, encoding='utf-8') as f:
        data_list = json.load(f)

    out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_data_embedding_list.jsonl')

    for data in data_list:
        text = build_text(data)
        print(f"Embedding対象テキスト: {text}")

        # 新しいopenaiパッケージ用
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