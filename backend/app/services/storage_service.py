"""
Google Cloud Storageサービス

Cloud Storageからデータファイルをダウンロードし、
ローカル環境では従来通りdata/から直接読み込む機能を提供します。
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    storage = None
    GCS_AVAILABLE = False

from ..core.config import settings
from ..core.exceptions import StorageException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger


class StorageService:
    _instance = None
    def __new__(cls, *args: object, **kwargs: object) -> "StorageService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    """Google Cloud Storageとローカルファイルシステムの統合管理"""
    
    def __init__(self) -> None:
        self.initialized: bool = getattr(self, 'initialized', False)
        if self.initialized:
            return  # すでに初期化済みの場合は何もしない
        
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.is_cloud_environment = settings.ENVIRONMENT == "production"
        self.cache_dir = Path("/tmp/gamechat-data") if self.is_cloud_environment else None
        
        # Cloud環境でのみGoogle Cloud Storageクライアントを初期化
        if self.is_cloud_environment and self.bucket_name and GCS_AVAILABLE:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                GameChatLogger.log_info("storage_service", "Cloud Storage初期化完了", {
                    "bucket_name": self.bucket_name,
                    "environment": settings.ENVIRONMENT
                })
            except Exception as e:
                GameChatLogger.log_error("storage_service", "Cloud Storage初期化に失敗", e)
                self.client = None
                self.bucket = None
        else:
            self.client = None
            self.bucket = None
            if not GCS_AVAILABLE and self.is_cloud_environment:
                GameChatLogger.log_warning("storage_service", "Google Cloud Storage ライブラリが利用できません")
            GameChatLogger.log_info("storage_service", "ローカル環境モードで初期化", {
                "environment": settings.ENVIRONMENT,
                "bucket_configured": bool(self.bucket_name),
                "gcs_available": GCS_AVAILABLE
            })
        
        self.initialized = True
    
    def _ensure_cache_directory(self) -> None:
        """キャッシュディレクトリが存在することを確認"""
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @handle_service_exceptions("storage", fallback_return=None)
    def _download_from_gcs(self, gcs_path: str, local_path: str) -> bool:
        """Google Cloud Storageからファイルをダウンロード"""
        if not self.bucket:
            GameChatLogger.log_warning("storage_service", "Cloud Storageが利用できません", {
                "gcs_path": gcs_path
            })
            return False
        
        try:
            blob = self.bucket.blob(gcs_path)
            
            # ファイルが存在するかチェック
            if not blob.exists():
                GameChatLogger.log_warning("storage_service", "GCSファイルが存在しません", {
                    "gcs_path": gcs_path,
                    "bucket": self.bucket_name
                })
                return False
            
            # ダウンロード実行
            blob.download_to_filename(local_path)
            
            GameChatLogger.log_success("storage_service", "GCSからダウンロード完了", {
                "gcs_path": gcs_path,
                "local_path": local_path,
                "file_size": blob.size
            })
            return True
            
        except Exception as e:
            # 例外の種類を確認してログ出力
            if "NotFound" in str(type(e).__name__) or "404" in str(e):
                GameChatLogger.log_warning("storage_service", "GCSファイルが見つかりません", {
                    "gcs_path": gcs_path,
                    "bucket": self.bucket_name,
                    "error_type": type(e).__name__
                })
            else:
                GameChatLogger.log_error("storage_service", "GCSダウンロードに失敗", e, {
                    "gcs_path": gcs_path,
                    "local_path": local_path,
                    "error_type": type(e).__name__
                })
            return False
    
    def _get_local_file_path(self, file_key: str) -> str:
        """ファイルキーに対応するローカルファイルパスを取得"""
        path_mapping = {
            "data": settings.DATA_FILE_PATH,
            "convert_data": settings.CONVERTED_DATA_FILE_PATH,
            "embedding_list": settings.EMBEDDING_FILE_PATH,
            "query_data": settings.QUERY_DATA_FILE_PATH
        }
        
        if file_key not in path_mapping:
            raise StorageException(
                message=f"未対応のファイルキー: {file_key}",
                code="INVALID_FILE_KEY",
                details={"file_key": file_key, "supported_keys": list(path_mapping.keys())}
            )
        
        return path_mapping[file_key]
    
    def _get_gcs_file_path(self, file_key: str) -> str:
        """ファイルキーに対応するGCSファイルパスを取得"""
        gcs_path_mapping = {
            "data": "data/data.json",
            "convert_data": "data/convert_data.json", 
            "embedding_list": "data/embedding_list.jsonl",
            "query_data": "data/query_data.json"
        }
        
        return gcs_path_mapping.get(file_key, f"data/{file_key}")
    
    @handle_service_exceptions("storage", fallback_return=None)
    def get_file_path(self, file_key: str) -> Optional[str]:
        """
        ファイルキーに基づいて利用可能なファイルパスを取得
        
        Args:
            file_key: データファイルのキー ("data", "convert_data", "embedding_list", "query_data")
            
        Returns:
            利用可能なファイルパス、または None（エラー時）
        """
        # ローカル環境では直接ローカルファイルパスを返す
        if not self.is_cloud_environment:
            local_path = self._get_local_file_path(file_key)
            abs_path = os.path.abspath(local_path)
            if os.path.exists(local_path):
                GameChatLogger.log_info(
                    "storage_service",
                    f"ローカルファイルを使用: {local_path} (絶対パス: {abs_path})",
                    {
                        "file_key": file_key,
                        "path": local_path,
                        "abs_path": abs_path
                    }
                )
                return local_path
            else:
                dir_exists = os.path.isdir(os.path.dirname(abs_path))
                GameChatLogger.log_warning(
                    "storage_service",
                    f"ローカルファイルが存在しません: {local_path} (絶対パス: {abs_path}) ディレクトリ存在: {dir_exists}",
                    {
                        "file_key": file_key,
                        "path": local_path,
                        "abs_path": abs_path,
                        "exists": False,
                        "dir_exists": dir_exists
                    }
                )
                return None
        
        # Cloud環境での処理
        self._ensure_cache_directory()
        
        if self.cache_dir is None:
            return None
        cache_path = self.cache_dir / f"{file_key}.cache"
        
        # キャッシュが存在する場合はそれを使用
        if cache_path.exists():
            GameChatLogger.log_info("storage_service", "キャッシュファイルを使用", {
                "file_key": file_key,
                "cache_path": str(cache_path)
            })
            return str(cache_path)
        
        # GCSからダウンロードを試行
        gcs_path = self._get_gcs_file_path(file_key)
        if self._download_from_gcs(gcs_path, str(cache_path)):
            return str(cache_path)
        
        # GCSからのダウンロードに失敗した場合、ローカルファイルを試行
        local_path = self._get_local_file_path(file_key)
        if os.path.exists(local_path):
            GameChatLogger.log_info("storage_service", "フォールバックでローカルファイルを使用", {
                "file_key": file_key,
                "path": local_path,
                "reason": "GCS_DOWNLOAD_FAILED"
            })
            return local_path
        
        GameChatLogger.log_error("storage_service", "利用可能なファイルが見つかりません", Exception("No file available"), {
            "file_key": file_key,
            "gcs_path": gcs_path,
            "local_path": local_path,
            "cache_path": str(cache_path)
        })
        return None
    
    @handle_service_exceptions("storage", fallback_return=[])
    def load_json_data(self, file_key: str) -> List[Dict[str, Any]]:
        """
        JSONファイルからデータを読み込む
        
        Args:
            file_key: データファイルのキー
            
        Returns:
            読み込んだデータのリスト
        """
        file_path = self.get_file_path(file_key)
        
        if not file_path:
            GameChatLogger.log_error("storage_service", "データファイルが利用できません", Exception("File path not available"), {
                "file_key": file_key
            })
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                GameChatLogger.log_error("storage_service", "データファイル形式が不正です", Exception("Invalid data format"), {
                    "file_key": file_key,
                    "file_path": file_path,
                    "data_type": type(data).__name__
                })
                return []
                
            GameChatLogger.log_success("storage_service", "データファイル読み込み完了", {
                "file_key": file_key,
                "file_path": file_path,
                "data_count": len(data)
            })
            return data
            
        except json.JSONDecodeError as e:
            GameChatLogger.log_error("storage_service", "JSONデコードエラー", e, {
                "file_key": file_key,
                "file_path": file_path
            })
            return []
        except Exception as e:
            GameChatLogger.log_error("storage_service", "ファイル読み込みエラー", e, {
                "file_key": file_key,
                "file_path": file_path
            })
            return []
    
    @handle_service_exceptions("storage", fallback_return=[])
    def load_jsonl_data(self, file_key: str) -> List[Dict[str, Any]]:
        """
        JSONLファイルからデータを読み込む
        
        Args:
            file_key: データファイルのキー
            
        Returns:
            読み込んだデータのリスト
        """
        file_path = self.get_file_path(file_key)
        
        if not file_path:
            GameChatLogger.log_error("storage_service", "データファイルが利用できません", Exception("File path not available for JSONL"), {
                "file_key": file_key
            })
            return []
        
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        GameChatLogger.log_warning("storage_service", f"JSONL行のパースエラー（行 {line_num}）", {
                            "file_key": file_key,
                            "line_number": line_num,
                            "line_content": line[:100] + "..." if len(line) > 100 else line,
                            "error": str(e)
                        })
                        continue
            
            GameChatLogger.log_success("storage_service", "JSONLファイル読み込み完了", {
                "file_key": file_key,
                "file_path": file_path,
                "data_count": len(data)
            })
            return data
            
        except Exception as e:
            GameChatLogger.log_error("storage_service", "JSONLファイル読み込みエラー", e, {
                "file_key": file_key,
                "file_path": file_path
            })
            return []
    
    def clear_cache(self) -> None:
        """キャッシュディレクトリをクリア"""
        if not self.cache_dir or not self.cache_dir.exists():
            return
        
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            GameChatLogger.log_info("storage_service", "キャッシュディレクトリをクリアしました", {
                "cache_dir": str(self.cache_dir)
            })
        except Exception as e:
            GameChatLogger.log_error("storage_service", "キャッシュクリアに失敗", e, {
                "cache_dir": str(self.cache_dir)
            })
    
    def get_cache_info(self) -> Dict[str, Any]:
        """キャッシュ情報を取得"""
        if not self.cache_dir:
            return {"cache_enabled": False}
        
        cache_info: Dict[str, Any] = {
            "cache_enabled": True,
            "cache_dir": str(self.cache_dir),
            "cache_exists": self.cache_dir.exists(),
            "cached_files": []
        }
        
        if self.cache_dir.exists():
            try:
                for file_path in self.cache_dir.iterdir():
                    if file_path.is_file():
                        cache_info["cached_files"].append({
                            "name": file_path.name,
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime
                        })
            except Exception as e:
                GameChatLogger.log_error("storage_service", "キャッシュ情報取得エラー", e)
        
        return cache_info
