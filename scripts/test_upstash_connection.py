import os
from upstash_vector import Index, Vector
from dotenv import load_dotenv
dotenv_path_global = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path_global)
upsert_vector_str = os.getenv("PRECOMPUTED_UPSERT_VECTOR_STR")
query_vector_str = os.getenv("PRECOMPUTED_QUERY_VECTOR_STR")

# 文字列を浮動小数点数のリストに変換する関数
def string_to_float_list(s):
    if not s:
        return []
    return [float(x.strip()) for x in s.split(',')]

PRECOMPUTED_UPSERT_VECTOR = string_to_float_list(upsert_vector_str)
PRECOMPUTED_QUERY_VECTOR = string_to_float_list(query_vector_str)

if not PRECOMPUTED_UPSERT_VECTOR or not PRECOMPUTED_QUERY_VECTOR:
    print("Error: Precomputed vectors not found in .env or are empty.")
    exit()

if len(PRECOMPUTED_UPSERT_VECTOR) != 1536 or len(PRECOMPUTED_QUERY_VECTOR) != 1536:
    print("警告: ハードコードされたベクトルの次元数が1536ではありません。実際のデータを貼り付けてください。")
    if len(PRECOMPUTED_UPSERT_VECTOR) != 1536 : PRECOMPUTED_UPSERT_VECTOR = [0.0] * 1536
    if len(PRECOMPUTED_QUERY_VECTOR) != 1536 : PRECOMPUTED_QUERY_VECTOR = [0.01] * 1536 # クエリは少し変える


def test_upstash_vector_connection():
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    if not url or not token:
        print("Error: UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN not found.")
        return
    try:
        index = Index(url=url, token=token)
        print("Successfully initialized Upstash Vector client.")

        vector_id = "test-py-precomputed-embed-1"

        upsert_vector_data = PRECOMPUTED_UPSERT_VECTOR
        print(f"Using precomputed upsert vector (dimension: {len(upsert_vector_data)}).")

        dummy_sparse_data_dict = {"indices": [10, 25, 100], "values": [0.5, 0.3, 0.8]}
        dummy_sparse_tuple = (dummy_sparse_data_dict["indices"], dummy_sparse_data_dict["values"])

        print(f"Upserting precomputed vector with id: {vector_id}")
        vector_to_upsert = Vector(
            id=vector_id,
            vector=upsert_vector_data,
            metadata={"source": "test_script_precomputed_embed"},
            sparse_vector=dummy_sparse_tuple
        )
        index.upsert(vectors=[vector_to_upsert],namespace="test")
        print(f"Upserted test data with id: {vector_id}")

        query_vector_data = PRECOMPUTED_QUERY_VECTOR
        print(f"Using precomputed query vector (dimension: {len(query_vector_data)}).")

        query_sparse_data_dict = {"indices": [10, 20, 100], "values": [0.4, 0.6, 0.9]}
        query_sparse_tuple = (query_sparse_data_dict["indices"], query_sparse_data_dict["values"])


        print("Performing query...")
        results = index.query(
            vector=query_vector_data,
            sparse_vector=query_sparse_tuple, # ここもタプル形式に変更
            top_k=1,
            include_metadata=True,
            include_vectors=True
        )
        if results:
            print("Upstash Vector connection and basic query successful!")
        else:
            print("No results found for the query.")        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_upstash_vector_connection()