#!/usr/bin/env python3
"""
Google Cloud Storageにデータファイルをアップロードするスクリプト

使用方法:
    python scripts/deployment/upload_data_to_gcs.py

環境変数:
    GCS_BUCKET_NAME: Cloud Storageバケット名 (デフォルト: gamechat-ai-data)
    GCS_PROJECT_ID: Google CloudプロジェクトID
    GOOGLE_APPLICATION_CREDENTIALS: サービスアカウントキーファイルのパス (オプション)
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    GCS_AVAILABLE = True
except ImportError:
    print("エラー: google-cloud-storage ライブラリがインストールされていません")
    print("以下のコマンドでインストールしてください:")
    print("pip install google-cloud-storage")
    sys.exit(1)

# プロジェクトルートを取得
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from backend.app.core.logging import GameChatLogger


class DataUploader:
    """Google Cloud Storageへのデータアップロード管理"""
    
    def __init__(self, bucket_name: str = "gamechat-ai-data", project_id: str = None):
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.client = None
        self.bucket = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Cloud Storageクライアントを初期化"""
        try:
            if self.project_id:
                self.client = storage.Client(project=self.project_id)
            else:
                self.client = storage.Client()
            
            # バケットが存在するかチェック
            try:
                self.bucket = self.client.bucket(self.bucket_name)
                self.bucket.reload()  # バケットの存在確認
                print(f"✅ バケット '{self.bucket_name}' に接続しました")
            except NotFound:
                print(f"❌ バケット '{self.bucket_name}' が見つかりません")
                print("以下のコマンドでバケットを作成してください:")
                print(f"gsutil mb -l asia-northeast1 gs://{self.bucket_name}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Google Cloud Storage初期化に失敗: {e}")
            print("認証設定を確認してください:")
            print("1. gcloud auth application-default login")
            print("2. または GOOGLE_APPLICATION_CREDENTIALS 環境変数を設定")
            sys.exit(1)
    
    def _get_data_files(self) -> List[Tuple[Path, str]]:
        """アップロード対象のデータファイルリストを取得"""
        data_dir = project_root / "data"
        
        # アップロード対象ファイルの定義
        file_mappings = [
            ("data.json", "data/data.json"),
            ("convert_data.json", "data/convert_data.json"),
            ("embedding_list.jsonl", "data/embedding_list.jsonl"),
            ("query_data.json", "data/query_data.json")
        ]
        
        existing_files = []
        missing_files = []
        
        for local_name, gcs_path in file_mappings:
            local_path = data_dir / local_name
            if local_path.exists():
                existing_files.append((local_path, gcs_path))
            else:
                missing_files.append(local_name)
        
        if missing_files:
            print(f"⚠️  以下のファイルが見つかりません: {', '.join(missing_files)}")
        
        if not existing_files:
            print("❌ アップロード可能なデータファイルが見つかりません")
            print(f"データディレクトリ: {data_dir}")
            sys.exit(1)
        
        return existing_files
    
    def upload_file(self, local_path: Path, gcs_path: str) -> bool:
        """単一ファイルをGCSにアップロード"""
        try:
            blob = self.bucket.blob(gcs_path)
            
            # ファイルサイズとメタデータを設定
            file_size = local_path.stat().st_size
            blob.upload_from_filename(str(local_path))
            
            print(f"✅ アップロード完了: {local_path.name} -> gs://{self.bucket_name}/{gcs_path}")
            print(f"   ファイルサイズ: {file_size:,} bytes")
            
            GameChatLogger.log_success("data_uploader", "ファイルアップロード完了", {
                "local_path": str(local_path),
                "gcs_path": gcs_path,
                "bucket": self.bucket_name,
                "file_size": file_size
            })
            
            return True
            
        except Exception as e:
            print(f"❌ アップロード失敗: {local_path.name} - {e}")
            GameChatLogger.log_error("data_uploader", "ファイルアップロード失敗", e, {
                "local_path": str(local_path),
                "gcs_path": gcs_path,
                "bucket": self.bucket_name
            })
            return False
    
    def upload_all(self) -> bool:
        """すべてのデータファイルをアップロード"""
        files_to_upload = self._get_data_files()
        
        print(f"\n📤 {len(files_to_upload)}個のファイルをアップロードします...")
        print(f"バケット: gs://{self.bucket_name}")
        print("-" * 50)
        
        success_count = 0
        for local_path, gcs_path in files_to_upload:
            if self.upload_file(local_path, gcs_path):
                success_count += 1
        
        print("-" * 50)
        if success_count == len(files_to_upload):
            print(f"🎉 全{len(files_to_upload)}ファイルのアップロードが完了しました!")
            return True
        else:
            print(f"⚠️  {success_count}/{len(files_to_upload)}ファイルがアップロードされました")
            return False
    
    def list_uploaded_files(self):
        """アップロード済みファイルの一覧表示"""
        print(f"\n📋 バケット gs://{self.bucket_name}/data/ の内容:")
        print("-" * 50)
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix="data/")
            found_any = False
            
            for blob in blobs:
                found_any = True
                size_mb = blob.size / (1024 * 1024)
                print(f"📄 {blob.name}")
                print(f"   サイズ: {size_mb:.2f} MB")
                print(f"   更新日時: {blob.updated}")
                print()
            
            if not found_any:
                print("ファイルが見つかりませんでした")
                
        except Exception as e:
            print(f"❌ ファイル一覧取得に失敗: {e}")


def main():
    """メイン実行関数"""
    print("🚀 Google Cloud Storage データアップローダー")
    print("=" * 50)
    
    # 環境変数から設定を取得
    bucket_name = os.getenv("GCS_BUCKET_NAME", "gamechat-ai-data")
    project_id = os.getenv("GCS_PROJECT_ID")
    
    print(f"バケット名: {bucket_name}")
    if project_id:
        print(f"プロジェクトID: {project_id}")
    
    # アップローダーを初期化
    uploader = DataUploader(bucket_name=bucket_name, project_id=project_id)
    
    # アップロード実行
    success = uploader.upload_all()
    
    # アップロード後のファイル一覧表示
    uploader.list_uploaded_files()
    
    if success:
        print("\n✅ すべての処理が正常に完了しました!")
        print("\n次のステップ:")
        print("1. Cloud Runサービスアカウントに 'Storage Object Viewer' 権限を付与")
        print("2. Cloud Runサービスに以下の環境変数を設定:")
        print(f"   GCS_BUCKET_NAME={bucket_name}")
        if project_id:
            print(f"   GCS_PROJECT_ID={project_id}")
        print("3. Cloud Runサービスをデプロイ")
    else:
        print("\n❌ 一部の処理でエラーが発生しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
