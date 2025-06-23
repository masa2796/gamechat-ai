"""
APIキー自動ローテーションシステム
定期的なAPIキー更新とダウンタイムなしの切り替えを実装
"""
import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path
from .log_security import security_audit_logger


class APIKeyRotationManager:
    """APIキーの自動ローテーション管理"""
    
    def __init__(self, 
                 rotation_interval_days: int = 30,
                 overlap_period_hours: int = 24,
                 backup_directory: Optional[str] = None):
        """
        Args:
            rotation_interval_days: ローテーション間隔（日）
            overlap_period_hours: 新旧キーの重複期間（時間）
            backup_directory: キーバックアップディレクトリ
        """
        self.rotation_interval = timedelta(days=rotation_interval_days)
        self.overlap_period = timedelta(hours=overlap_period_hours)
        self.logger = logging.getLogger(__name__)
        
        # バックアップディレクトリの設定と作成
        self.backup_dir = self._setup_backup_directory(backup_directory)
    
    def _setup_backup_directory(self, backup_directory: Optional[str]) -> Optional[Path]:
        """バックアップディレクトリを安全に設定"""
        if not backup_directory:
            # 環境変数から取得を試行
            backup_directory = os.getenv("BACKUP_DIRECTORY")
        
        if not backup_directory:
            # デフォルトパスの候補
            candidates = [
                "/tmp/gamechat_backups",
                "./backups",
                "./tmp"
            ]
            
            for candidate in candidates:
                try:
                    backup_path = Path(candidate)
                    backup_path.mkdir(parents=True, exist_ok=True)
                    # 書き込み権限をテスト
                    test_file = backup_path / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                    self.logger.info(f"Using backup directory: {backup_path}")
                    return backup_path
                except (PermissionError, OSError) as e:
                    self.logger.debug(f"Cannot use {candidate}: {e}")
                    continue
            
            self.logger.warning("No writable backup directory found, backup disabled")
            return None
        
        try:
            backup_path = Path(backup_directory)
            backup_path.mkdir(parents=True, exist_ok=True)
            # 書き込み権限をテスト
            test_file = backup_path / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            self.logger.info(f"Using backup directory: {backup_path}")
            return backup_path
        except (PermissionError, OSError) as e:
            self.logger.warning(f"Cannot create backup directory {backup_directory}: {e}")
            return None
    
    def generate_api_key(self, key_type: str) -> str:
        """
        新しいAPIキーを生成
        
        Args:
            key_type: キータイプ（production, development, etc.）
            
        Returns:
            新しいAPIキー
        """
        prefix_map = {
            "production": "gc_prod_",
            "development": "gc_dev_",
            "frontend": "gc_fe_",
            "readonly": "gc_ro_"
        }
        
        prefix = prefix_map.get(key_type, "gc_")
        # 32文字のランダム文字列を生成
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) 
                             for _ in range(32))
        
        return f"{prefix}{random_part}"
    
    def is_rotation_needed(self, key_type: str) -> bool:
        """
        ローテーションが必要かチェック
        
        Args:
            key_type: チェック対象のキータイプ
            
        Returns:
            ローテーションが必要かどうか
        """
        rotation_file = self.backup_dir / f"{key_type}_last_rotation.json" if self.backup_dir else None
        
        if not rotation_file or not rotation_file.exists():
            # 初回またはファイルが存在しない場合はローテーション必要
            return True
        
        try:
            with open(rotation_file, 'r') as f:
                data = json.load(f)
                last_rotation = datetime.fromisoformat(data['last_rotation'])
                
                # ローテーション間隔を過ぎているかチェック
                return datetime.now() - last_rotation > self.rotation_interval
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Error reading rotation file for {key_type}: {e}")
            return True
    
    def record_rotation(self, key_type: str, new_key: str, old_key: Optional[str] = None) -> None:
        """
        ローテーション実行の記録
        
        Args:
            key_type: キータイプ
            new_key: 新しいキー
            old_key: 古いキー（オプション）
        """
        if not self.backup_dir:
            return
        
        rotation_data = {
            "key_type": key_type,
            "last_rotation": datetime.now().isoformat(),
            "new_key_hash": self._hash_key(new_key),
            "old_key_hash": self._hash_key(old_key) if old_key else None,
            "rotation_id": secrets.token_hex(8)
        }
        
        rotation_file = self.backup_dir / f"{key_type}_last_rotation.json"
        
        try:
            with open(rotation_file, 'w') as f:
                json.dump(rotation_data, f, indent=2)
            
            # セキュリティ監査ログ
            security_audit_logger.log_security_violation(
                violation_type="api_key_rotation",
                description=f"API key rotated for {key_type}",
                client_ip="system",
                details={
                    "key_type": key_type,
                    "rotation_id": rotation_data["rotation_id"],
                    "automated": True
                }
            )
            
            self.logger.info(f"Recorded rotation for {key_type} (ID: {rotation_data['rotation_id']})")
            
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to record rotation for {key_type}: {e}")
    
    def _hash_key(self, api_key: str) -> str:
        """APIキーのハッシュを生成（ログ用）"""
        if not api_key:
            return ""
        
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """
        全キータイプのローテーション状況を取得
        
        Returns:
            ローテーション状況の辞書
        """
        key_types = ["production", "development", "frontend", "readonly"]
        status = {}
        
        for key_type in key_types:
            rotation_file = self.backup_dir / f"{key_type}_last_rotation.json" if self.backup_dir else None
            
            if not rotation_file or not rotation_file.exists():
                status[key_type] = {
                    "needs_rotation": True,
                    "last_rotation": None,
                    "next_rotation": "immediate"
                }
                continue
            
            try:
                with open(rotation_file, 'r') as f:
                    data = json.load(f)
                    last_rotation = datetime.fromisoformat(data['last_rotation'])
                    next_rotation = last_rotation + self.rotation_interval
                    
                    status[key_type] = {
                        "needs_rotation": self.is_rotation_needed(key_type),
                        "last_rotation": last_rotation.isoformat(),
                        "next_rotation": next_rotation.isoformat(),
                        "days_until_rotation": str((next_rotation - datetime.now()).days)
                    }
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.warning(f"Error reading rotation status for {key_type}: {e}")
                status[key_type] = {
                    "needs_rotation": True,
                    "last_rotation": None,
                    "next_rotation": "immediate",
                    "error": str(e)
                }
        
        return status
    
    async def rotate_api_key(self, key_type: str, force: bool = False) -> Dict[str, Any]:
        """
        APIキーのローテーションを実行
        
        Args:
            key_type: ローテーション対象のキータイプ
            force: 強制ローテーション
            
        Returns:
            ローテーション結果
        """
        if not force and not self.is_rotation_needed(key_type):
            return {
                "success": False,
                "message": f"Rotation not needed for {key_type}",
                "key_type": key_type
            }
        
        try:
            # 現在のキーを取得
            env_var_name = f"API_KEY_{key_type.upper()}"
            current_key = os.getenv(env_var_name)
            
            # 新しいキーを生成
            new_key = self.generate_api_key(key_type)
            
            # ローテーション記録
            self.record_rotation(key_type, new_key, current_key)
            
            result = {
                "success": True,
                "key_type": key_type,
                "new_key": new_key,
                "old_key_hash": self._hash_key(current_key) if current_key else None,
                "rotation_time": datetime.now().isoformat(),
                "instructions": self._get_rotation_instructions(key_type, new_key)
            }
            
            self.logger.info(f"Successfully rotated API key for {key_type}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to rotate API key for {key_type}: {e}")
            
            security_audit_logger.log_security_violation(
                violation_type="api_key_rotation_failure",
                description=f"Failed to rotate API key for {key_type}",
                client_ip="system",
                details={
                    "key_type": key_type,
                    "error": str(e),
                    "automated": True
                }
            )
            
            return {
                "success": False,
                "key_type": key_type,
                "error": str(e),
                "rotation_time": datetime.now().isoformat()
            }
    
    def _get_rotation_instructions(self, key_type: str, new_key: str) -> List[str]:
        """ローテーション手順を生成"""
        env_var_name = f"API_KEY_{key_type.upper()}"
        
        return [
            f"1. Update environment variable: {env_var_name}",
            f"2. Update Secret Manager: {env_var_name}",
            "3. Deploy new configuration to Cloud Run",
            "4. Test API endpoints with new key",
            f"5. Verify old key is disabled after {self.overlap_period.total_seconds() / 3600} hours",
            "6. Update frontend/client configurations if applicable"
        ]
    
    async def batch_rotation_check(self) -> Dict[str, Any]:
        """
        全APIキーのローテーション必要性をチェック
        
        Returns:
            チェック結果とローテーション推奨事項
        """
        status = self.get_rotation_status()
        rotation_needed = []
        
        for key_type, info in status.items():
            if info["needs_rotation"]:
                rotation_needed.append(key_type)
        
        result = {
            "check_time": datetime.now().isoformat(),
            "total_keys": len(status),
            "rotation_needed_count": len(rotation_needed),
            "rotation_needed_keys": rotation_needed,
            "status_details": status
        }
        
        if rotation_needed:
            self.logger.warning(f"API key rotation needed for: {', '.join(rotation_needed)}")
            
            security_audit_logger.log_suspicious_activity(
                activity_type="api_key_rotation_needed",
                client_ip="system",
                description=f"API keys need rotation: {', '.join(rotation_needed)}",
                severity="medium",
                details={"keys_needing_rotation": rotation_needed}
            )
        
        return result


# グローバルインスタンス
api_key_rotation_manager = APIKeyRotationManager()


async def check_api_key_rotation_status() -> Dict[str, Any]:
    """APIキーローテーション状況の簡易チェック"""
    return await api_key_rotation_manager.batch_rotation_check()


async def rotate_api_key_if_needed(key_type: str, force: bool = False) -> Dict[str, Any]:
    """指定されたAPIキーのローテーション実行"""
    return await api_key_rotation_manager.rotate_api_key(key_type, force)


def get_api_key_rotation_instructions() -> Dict[str, List[str]]:
    """APIキーローテーションの手順を取得"""
    return {
        "general_steps": [
            "1. システムメンテナンス時間を設定",
            "2. 新しいAPIキーを生成",
            "3. Secret Managerに新キーを追加",
            "4. 新旧キーの重複期間を設定（推奨24時間）",
            "5. アプリケーションを新キーでテスト",
            "6. 古いキーを無効化",
            "7. クライアント側の設定を更新"
        ],
        "emergency_rotation": [
            "1. 即座に古いキーを無効化",
            "2. 新しいAPIキーを緊急生成",
            "3. 緊急メンテナンスを実施",
            "4. 新キーでサービスを再開",
            "5. インシデントレポートを作成"
        ]
    }
