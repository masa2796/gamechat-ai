"""
セキュリティ強化ログ管理システム
機密情報の完全マスキングと監査ログ機能を提供
"""
import re
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone
import hashlib


class SecurityLogMasker:
    """機密情報を自動的にマスキングするクラス"""
    
    # 機密情報パターンの定義
    SENSITIVE_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key[s]?[:=\s]+)([a-zA-Z0-9_-]{20,})',
        'token': r'(?i)(token[:=\s]+)([a-zA-Z0-9_.-]{20,})',
        'password': r'(?i)(password[:=\s]+)([^\s\'"]+)',
        'secret': r'(?i)(secret[:=\s]+)([a-zA-Z0-9_.-]{8,})',
        'openai_key': r'(sk-[a-zA-Z0-9]{20,})',
        'bearer_token': r'(?i)(bearer\s+)([a-zA-Z0-9_.-]{20,})',
        'authorization': r'(?i)(authorization[:=\s]+)([^\s\'"]+)',
        'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        'credit_card': r'(\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b)',
        'ssn': r'(\b\d{3}-\d{2}-\d{4}\b)',
        'ip_address': r'(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
    }
    
    @classmethod
    def mask_sensitive_data(cls, data: Union[str, Dict[str, Any], Any]) -> Union[str, Dict[str, Any], Any]:
        """
        機密情報をマスキングする
        
        Args:
            data: マスキング対象のデータ
            
        Returns:
            マスキング済みのデータ
        """
        if isinstance(data, str):
            return cls._mask_string(data)
        elif isinstance(data, dict):
            return cls._mask_dict(data)
        elif isinstance(data, list):
            return [cls.mask_sensitive_data(item) for item in data]
        else:
            return data
    
    @classmethod
    def _mask_string(cls, text: str) -> str:
        """文字列内の機密情報をマスキング"""
        masked_text = text
        
        for pattern_name, pattern in cls.SENSITIVE_PATTERNS.items():
            if pattern_name == 'openai_key':
                # OpenAI APIキーの特別な処理
                masked_text = re.sub(pattern, r'sk-***MASKED***', masked_text)
            elif pattern_name in ['api_key', 'token', 'password', 'secret', 'bearer_token', 'authorization']:
                # 一般的な機密情報
                masked_text = re.sub(pattern, r'\1***MASKED***', masked_text)
            elif pattern_name == 'email':
                # メールアドレスの部分マスキング
                def mask_email(match: re.Match[str]) -> str:
                    email = match.group(1)
                    local, domain = email.split('@')
                    masked_local = local[:2] + '***' if len(local) > 2 else '***'
                    return f"{masked_local}@{domain}"
                masked_text = re.sub(pattern, mask_email, masked_text)
            elif pattern_name == 'ip_address':
                # IPアドレスの部分マスキング
                masked_text = re.sub(pattern, r'***.***.***.***', masked_text)
            else:
                # その他の機密情報
                masked_text = re.sub(pattern, r'***MASKED***', masked_text)
        
        return masked_text
    
    @classmethod
    def _mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """辞書内の機密情報をマスキング"""
        masked_dict: Dict[str, Any] = {}
        
        # 機密情報が含まれる可能性のあるキー
        sensitive_keys = {
            'api_key', 'api-key', 'apikey', 'x-api-key',
            'password', 'passwd', 'pwd',
            'token', 'access_token', 'refresh_token', 'bearer',
            'secret', 'client_secret',
            'authorization', 'auth',
            'openai_api_key', 'openai-api-key',
            'recaptcha_secret', 'recaptcha-secret',
            'email', 'email_address'
        }
        
        for key, value in data.items():
            key_lower = key.lower().replace('_', '').replace('-', '')
            
            if any(sensitive_key.replace('_', '').replace('-', '') in key_lower for sensitive_key in sensitive_keys):
                # キー名が機密情報を示唆する場合
                if isinstance(value, str) and len(value) > 4:
                    masked_dict[key] = f"***{value[-4:]}"
                else:
                    masked_dict[key] = "***MASKED***"
            else:
                # 通常の値の処理
                if isinstance(value, dict):
                    masked_dict[key] = cls.mask_sensitive_data(value)  # type: ignore
                elif isinstance(value, str):
                    masked_dict[key] = cls.mask_sensitive_data(value)  # type: ignore
                else:
                    masked_dict[key] = str(value)
        
        return masked_dict
    
    @classmethod
    def generate_safe_hash(cls, sensitive_data: str) -> str:
        """機密データの安全なハッシュを生成（デバッグ用）"""
        return hashlib.sha256(sensitive_data.encode()).hexdigest()[:8]


class SecurityAuditLogger:
    """セキュリティ監査専用ログシステム"""
    
    def __init__(self, logger_name: str = "security_audit"):
        self.logger = logging.getLogger(logger_name)
        self.masker = SecurityLogMasker()
    
    def log_auth_attempt(self, 
                        client_ip: str, 
                        auth_type: str, 
                        success: bool, 
                        details: Optional[Dict[str, Any]] = None) -> None:
        """認証試行のログ記録"""
        masked_details = self.masker.mask_sensitive_data(details) if details else {}
        
        log_data = {
            "event_type": "authentication_attempt",
            "client_ip": self.masker._mask_string(client_ip) if client_ip else "unknown",
            "auth_type": auth_type,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": masked_details
        }
        
        if success:
            self.logger.info(f"🔐 AUTH SUCCESS: {auth_type} from {self.masker._mask_string(client_ip)}", 
                           extra={"security_event": log_data})
        else:
            self.logger.warning(f"🚨 AUTH FAILED: {auth_type} from {self.masker._mask_string(client_ip)}", 
                              extra={"security_event": log_data})
    
    def log_rate_limit_exceeded(self, 
                               client_ip: str, 
                               api_key_type: str, 
                               limit: int,
                               details: Optional[Dict[str, Any]] = None) -> None:
        """レート制限超過のログ記録"""
        masked_details = self.masker.mask_sensitive_data(details) if details else {}
        
        log_data = {
            "event_type": "rate_limit_exceeded",
            "client_ip": self.masker._mask_string(client_ip) if client_ip else "unknown",
            "api_key_type": api_key_type,
            "rate_limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": masked_details
        }
        
        self.logger.warning(f"⚠️ RATE LIMIT: {api_key_type} from {self.masker._mask_string(client_ip)} (limit: {limit})", 
                          extra={"security_event": log_data})
    
    def log_suspicious_activity(self, 
                               activity_type: str, 
                               client_ip: str, 
                               description: str,
                               severity: str = "medium",
                               details: Optional[Dict[str, Any]] = None) -> None:
        """不審な活動のログ記録"""
        masked_details = self.masker.mask_sensitive_data(details) if details else {}
        
        log_data = {
            "event_type": "suspicious_activity",
            "activity_type": activity_type,
            "client_ip": self.masker._mask_string(client_ip) if client_ip else "unknown",
            "description": description,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": masked_details
        }
        
        severity_icon = {"low": "🔵", "medium": "🟡", "high": "🔴", "critical": "🚨"}.get(severity, "⚪")
        
        if severity in ["high", "critical"]:
            self.logger.error(f"{severity_icon} SUSPICIOUS: {activity_type} - {description}", 
                            extra={"security_event": log_data})
        else:
            self.logger.warning(f"{severity_icon} SUSPICIOUS: {activity_type} - {description}", 
                              extra={"security_event": log_data})
    
    def log_debug_endpoint_access(self, 
                                 client_ip: str, 
                                 endpoint: str, 
                                 user_agent: str,
                                 details: Optional[Dict[str, Any]] = None) -> None:
        """デバッグエンドポイントへのアクセス試行ログ"""
        masked_details = self.masker.mask_sensitive_data(details) if details else {}
        
        log_data = {
            "event_type": "debug_endpoint_access",
            "client_ip": self.masker._mask_string(client_ip) if client_ip else "unknown",
            "endpoint": endpoint,
            "user_agent": self.masker._mask_string(user_agent) if user_agent else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": masked_details,
            "severity": "critical"
        }
        
        self.logger.error(f"🚨 DEBUG ACCESS: Unauthorized access to {endpoint} from {self.masker._mask_string(client_ip)}", 
                        extra={"security_event": log_data})
    
    def log_api_key_usage(self, 
                         api_key_type: str, 
                         endpoint: str, 
                         client_ip: str,
                         details: Optional[Dict[str, Any]] = None) -> None:
        """APIキー使用状況のログ記録"""
        masked_details = self.masker.mask_sensitive_data(details) if details else {}
        
        log_data = {
            "event_type": "api_key_usage",
            "api_key_type": api_key_type,
            "endpoint": endpoint,
            "client_ip": self.masker._mask_string(client_ip) if client_ip else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": masked_details
        }
        
        self.logger.info(f"🔑 API USAGE: {api_key_type} accessed {endpoint}", 
                       extra={"security_event": log_data})
    
    def log_security_violation(self, 
                              violation_type: str, 
                              description: str, 
                              client_ip: str,
                              details: Optional[Dict[str, Any]] = None) -> None:
        """セキュリティ違反のログ記録"""
        masked_details = self.masker.mask_sensitive_data(details) if details else {}
        
        log_data = {
            "event_type": "security_violation",
            "violation_type": violation_type,
            "description": description,
            "client_ip": self.masker._mask_string(client_ip) if client_ip else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": masked_details,
            "severity": "critical"
        }
        
        self.logger.critical(f"🚨 SECURITY VIOLATION: {violation_type} - {description} from {self.masker._mask_string(client_ip)}", 
                           extra={"security_event": log_data})


# グローバルインスタンス
security_audit_logger = SecurityAuditLogger()


def mask_log_message(message: str) -> str:
    """ログメッセージの機密情報をマスキングする簡易関数"""
    result = SecurityLogMasker.mask_sensitive_data(message)
    return result if isinstance(result, str) else str(result)


def log_safe(logger: logging.Logger, level: str, message: str, **kwargs: Any) -> None:
    """安全なログ出力（機密情報自動マスキング）"""
    masked_message = mask_log_message(message)
    
    # 追加データもマスキング
    if 'extra' in kwargs and kwargs['extra']:
        kwargs['extra'] = SecurityLogMasker.mask_sensitive_data(kwargs['extra'])
    
    getattr(logger, level.lower())(masked_message, **kwargs)
