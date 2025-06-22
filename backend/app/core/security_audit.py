"""
セキュリティ監査ログシステム
重要なセキュリティイベントを記録・分析するためのモジュール
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

class SecurityEventType(Enum):
    """セキュリティイベントタイプ"""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_USAGE = "api_key_usage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DEBUG_ENDPOINT_ACCESS = "debug_endpoint_access"
    SECURITY_VIOLATION = "security_violation"

class SeverityLevel(Enum):
    """セキュリティイベントの重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """セキュリティイベントデータ構造"""
    event_type: SecurityEventType
    severity: SeverityLevel
    message: str
    timestamp: str
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    api_key_type: Optional[str] = None
    endpoint: Optional[str] = None
    request_method: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)

class SecurityAuditLogger:
    """セキュリティ監査ログシステム"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)
        
        # セキュリティ専用ログハンドラーの設定
        if log_file_path:
            handler = logging.FileHandler(log_file_path)
        else:
            handler = logging.StreamHandler()
            
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # イベント統計追跡
        self.event_stats: Dict[str, int] = {}
        self.suspicious_ips: Dict[str, List[float]] = {}
        
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SeverityLevel,
        message: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        api_key_type: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_method: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """セキュリティイベントをログに記録"""
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            timestamp=datetime.now().isoformat(),
            client_ip=client_ip,
            user_agent=user_agent,
            api_key_type=api_key_type,
            endpoint=endpoint,
            request_method=request_method,
            additional_data=additional_data
        )
        
        # ログに記録（機密情報は除外）
        safe_data = self._sanitize_log_data(event.to_dict())
        self.logger.info(json.dumps(safe_data, ensure_ascii=False))
        
        # 統計更新
        self._update_statistics(event)
        
        # 異常検知
        await self._detect_anomalies(event)
        
    def _sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ログデータから機密情報を除外"""
        safe_data = data.copy()
        
        # 機密情報をマスキング
        if safe_data.get("additional_data"):
            additional = safe_data["additional_data"]
            for key in list(additional.keys()):
                if any(sensitive in key.lower() for sensitive in ["key", "token", "secret", "password"]):
                    additional[key] = "***MASKED***"
                    
        return safe_data
        
    def _update_statistics(self, event: SecurityEvent) -> None:
        """イベント統計を更新"""
        event_key = f"{event.event_type.value}_{event.severity.value}"
        self.event_stats[event_key] = self.event_stats.get(event_key, 0) + 1
        
        # IPアドレス別の追跡
        if event.client_ip:
            if event.client_ip not in self.suspicious_ips:
                self.suspicious_ips[event.client_ip] = []
            self.suspicious_ips[event.client_ip].append(time.time())
            
    async def _detect_anomalies(self, event: SecurityEvent) -> None:
        """異常パターンの検出"""
        
        # 認証失敗の連続検出
        if event.event_type == SecurityEventType.AUTHENTICATION_FAILURE:
            await self._check_brute_force_attempt(event)
            
        # レート制限超過の頻発検出
        if event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
            await self._check_rate_limit_abuse(event)
            
        # デバッグエンドポイントへの不正アクセス
        if event.event_type == SecurityEventType.DEBUG_ENDPOINT_ACCESS:
            await self._alert_debug_access(event)
            
    async def _check_brute_force_attempt(self, event: SecurityEvent) -> None:
        """ブルートフォース攻撃の検出"""
        if not event.client_ip:
            return
            
        recent_failures = [
            timestamp for timestamp in self.suspicious_ips.get(event.client_ip, [])
            if time.time() - timestamp < 300  # 5分以内
        ]
        
        if len(recent_failures) >= 5:
            await self.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                SeverityLevel.HIGH,
                f"Potential brute force attack detected from IP: {event.client_ip}",
                client_ip=event.client_ip,
                additional_data={"failure_count": len(recent_failures)}
            )
            
    async def _check_rate_limit_abuse(self, event: SecurityEvent) -> None:
        """レート制限乱用の検出"""
        if not event.client_ip:
            return
            
        # 実装：レート制限超過の頻度チェック
        # 簡単な実装例
        await self.log_security_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            SeverityLevel.MEDIUM,
            f"Repeated rate limit violations from IP: {event.client_ip}",
            client_ip=event.client_ip
        )
        
    async def _alert_debug_access(self, event: SecurityEvent) -> None:
        """デバッグエンドポイントアクセスのアラート"""
        await self.log_security_event(
            SecurityEventType.SECURITY_VIOLATION,
            SeverityLevel.CRITICAL,
            f"Unauthorized debug endpoint access attempted",
            client_ip=event.client_ip,
            endpoint=event.endpoint,
            additional_data={"should_not_exist_in_production": True}
        )
        
    def get_security_summary(self) -> Dict[str, Any]:
        """セキュリティサマリーの取得"""
        current_time = time.time()
        
        # 過去24時間のイベント統計
        recent_events = {}
        for event_key, count in self.event_stats.items():
            if count > 0:
                recent_events[event_key] = count
                
        # 疑わしいIPアドレス
        suspicious_ips_summary = {}
        for ip, timestamps in self.suspicious_ips.items():
            recent_activity = [
                t for t in timestamps 
                if current_time - t < 86400  # 24時間以内
            ]
            if recent_activity:
                suspicious_ips_summary[ip] = len(recent_activity)
                
        return {
            "summary_generated_at": datetime.now().isoformat(),
            "recent_events": recent_events,
            "suspicious_ips": suspicious_ips_summary,
            "total_events_tracked": sum(self.event_stats.values())
        }

# グローバルインスタンス
security_audit_logger = SecurityAuditLogger()

# 便利な関数
async def log_auth_success(api_key_type: str, client_ip: str, endpoint: str) -> None:
    """認証成功ログ"""
    await security_audit_logger.log_security_event(
        SecurityEventType.AUTHENTICATION_SUCCESS,
        SeverityLevel.LOW,
        f"Authentication successful using {api_key_type}",
        client_ip=client_ip,
        api_key_type=api_key_type,
        endpoint=endpoint
    )

async def log_auth_failure(client_ip: str, endpoint: str, reason: str) -> None:
    """認証失敗ログ"""
    await security_audit_logger.log_security_event(
        SecurityEventType.AUTHENTICATION_FAILURE,
        SeverityLevel.MEDIUM,
        f"Authentication failed: {reason}",
        client_ip=client_ip,
        endpoint=endpoint,
        additional_data={"failure_reason": reason}
    )

async def log_rate_limit_exceeded(api_key_type: str, client_ip: str) -> None:
    """レート制限超過ログ"""
    await security_audit_logger.log_security_event(
        SecurityEventType.RATE_LIMIT_EXCEEDED,
        SeverityLevel.MEDIUM,
        f"Rate limit exceeded for {api_key_type}",
        client_ip=client_ip,
        api_key_type=api_key_type
    )

async def log_debug_access_attempt(client_ip: str, endpoint: str, user_agent: str) -> None:
    """デバッグエンドポイントアクセス試行ログ"""
    await security_audit_logger.log_security_event(
        SecurityEventType.DEBUG_ENDPOINT_ACCESS,
        SeverityLevel.CRITICAL,
        f"Debug endpoint access attempted: {endpoint}",
        client_ip=client_ip,
        endpoint=endpoint,
        user_agent=user_agent
    )
