import os
import json
from upstash_vector import Index, Vector
from dotenv import load_dotenv
from pathlib import Path

# backend/.envのみ参照
dotenv_path_global = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path_global)

def upload_embeddings_to_upstash():
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    if not url or not token:
        print("Error: UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN not found.")
        return

    index = Index(url=url, token=token)
    embedding_list_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'embedding_list.jsonl')

    with open(embedding_list_path, encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            namespace = data.get("namespace", "default")
            embedding = data.get("embedding")
            metadata = data.get("metadata", {})
            if embedding is None:
                print(f"Warning: embedding missing for id={data.get('id')}")
                continue
            vector = Vector(
                id=data.get("id"),
                vector=embedding,
                metadata=metadata
            )
            index.upsert(vectors=[vector], namespace=namespace)
            print(f"Upserted vector: {data.get('id')} (namespace: {namespace})")

if __name__ == "__main__":
    upload_embeddings_to_upstash()