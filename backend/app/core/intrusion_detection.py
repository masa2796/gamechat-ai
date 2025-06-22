"""
高度侵入検知システム (IDS)
リアルタイム脅威検出、異常パターン分析、自動ブロック機能
"""
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field
import logging
from .log_security import security_audit_logger
from .security_audit import SeverityLevel


@dataclass
class ThreatPattern:
    """脅威パターン定義"""
    name: str
    description: str
    conditions: Dict[str, Any]
    severity: SeverityLevel
    auto_block: bool = False
    cooldown_minutes: int = 60


@dataclass 
class AttackAttempt:
    """攻撃試行記録"""
    ip_address: str
    attack_type: str
    timestamp: datetime
    severity: SeverityLevel
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False


class IntrusionDetectionSystem:
    """高度侵入検知システム"""
    
    def __init__(self, 
                 enable_auto_block: bool = True,
                 max_failed_attempts: int = 5,
                 block_duration_minutes: int = 60,
                 monitoring_window_minutes: int = 15):
        """
        Args:
            enable_auto_block: 自動ブロック機能の有効化
            max_failed_attempts: 最大失敗試行回数
            block_duration_minutes: ブロック持続時間（分）
            monitoring_window_minutes: 監視ウィンドウ（分）
        """
        self.enable_auto_block = enable_auto_block
        self.max_failed_attempts = max_failed_attempts
        self.block_duration = timedelta(minutes=block_duration_minutes)
        self.monitoring_window = timedelta(minutes=monitoring_window_minutes)
        
        # 脅威追跡データ構造
        self.failed_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns: Dict[str, List[AttackAttempt]] = defaultdict(list)
        self.rate_limit_violations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.attack_fingerprints: Set[str] = set()
        
        # 脅威パターン定義
        self.threat_patterns = self._initialize_threat_patterns()
        
        self.logger = logging.getLogger(__name__)
        
        # セキュリティメトリクス
        self.metrics = {
            "total_blocked_ips": 0,
            "total_attack_attempts": 0,
            "total_threats_detected": 0,
            "false_positives": 0
        }
    
    def _initialize_threat_patterns(self) -> List[ThreatPattern]:
        """脅威パターンの初期化"""
        return [
            ThreatPattern(
                name="brute_force_login",
                description="Brute force login attempts",
                conditions={
                    "failed_attempts_threshold": 10,
                    "time_window_minutes": 5,
                    "pattern_type": "authentication_failure"
                },
                severity=SeverityLevel.HIGH,
                auto_block=True,
                cooldown_minutes=120
            ),
            ThreatPattern(
                name="api_key_scanning",
                description="API key scanning attempts",
                conditions={
                    "invalid_key_attempts": 20,
                    "time_window_minutes": 10,
                    "pattern_type": "api_key_scan"
                },
                severity=SeverityLevel.HIGH,
                auto_block=True,
                cooldown_minutes=180
            ),
            ThreatPattern(
                name="rate_limit_abuse",
                description="Excessive rate limit violations",
                conditions={
                    "rate_violations": 15,
                    "time_window_minutes": 5,
                    "pattern_type": "rate_abuse"
                },
                severity=SeverityLevel.MEDIUM,
                auto_block=True,
                cooldown_minutes=60
            ),
            ThreatPattern(
                name="debug_endpoint_probing",
                description="Debug endpoint probing attempts",
                conditions={
                    "debug_access_attempts": 3,
                    "time_window_minutes": 10,
                    "pattern_type": "debug_probing"
                },
                severity=SeverityLevel.CRITICAL,
                auto_block=True,
                cooldown_minutes=240
            ),
            ThreatPattern(
                name="suspicious_user_agent",
                description="Suspicious or automated user agents",
                conditions={
                    "pattern_type": "suspicious_agent",
                    "blacklisted_agents": [
                        "sqlmap", "nikto", "nmap", "masscan", "zap",
                        "burp", "w3af", "dirb", "gobuster", "curl"
                    ]
                },
                severity=SeverityLevel.MEDIUM,
                auto_block=False,
                cooldown_minutes=30
            ),
            ThreatPattern(
                name="anomalous_request_patterns",
                description="Anomalous request patterns",
                conditions={
                    "pattern_type": "anomaly",
                    "request_spike_threshold": 100,
                    "time_window_minutes": 1
                },
                severity=SeverityLevel.MEDIUM,
                auto_block=False,
                cooldown_minutes=15
            )
        ]
    
    async def analyze_request(self, 
                            client_ip: str,
                            user_agent: str,
                            endpoint: str,
                            method: str,
                            auth_success: bool,
                            additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        リクエストの脅威分析
        
        Args:
            client_ip: クライアントIPアドレス
            user_agent: ユーザーエージェント
            endpoint: アクセスされたエンドポイント
            method: HTTPメソッド
            auth_success: 認証成功の可否
            additional_data: 追加データ
            
        Returns:
            分析結果と推奨アクション
        """
        analysis_start = time.time()
        
        # ブロック済みIPのチェック
        if await self._is_blocked(client_ip):
            return {
                "action": "block",
                "reason": "IP address is blocked",
                "threat_level": "high",
                "blocked_until": self.blocked_ips.get(client_ip),
                "analysis_time": time.time() - analysis_start
            }
        
        # 各脅威パターンの分析
        detected_threats = []
        
        for pattern in self.threat_patterns:
            threat_detected = await self._check_threat_pattern(
                pattern, client_ip, user_agent, endpoint, method, auth_success, additional_data
            )
            
            if threat_detected:
                detected_threats.append(threat_detected)
        
        # 総合的な脅威レベル判定
        overall_threat = self._calculate_threat_level(detected_threats)
        
        # 自動ブロック判定
        should_block = any(
            threat.get("auto_block", False) and threat.get("severity") in ["high", "critical"]
            for threat in detected_threats
        )
        
        if should_block and self.enable_auto_block:
            await self._block_ip(client_ip, detected_threats)
        
        # メトリクス更新
        if detected_threats:
            self.metrics["total_threats_detected"] += len(detected_threats)
        
        return {
            "action": "block" if should_block else "allow",
            "threats_detected": len(detected_threats),
            "threat_details": detected_threats,
            "overall_threat_level": overall_threat,
            "analysis_time": time.time() - analysis_start,
            "recommendations": self._generate_recommendations(detected_threats)
        }
    
    async def _check_threat_pattern(self,
                                   pattern: ThreatPattern,
                                   client_ip: str,
                                   user_agent: str,
                                   endpoint: str,
                                   method: str,
                                   auth_success: bool,
                                   additional_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """個別脅威パターンのチェック"""
        
        if pattern.name == "brute_force_login":
            return await self._check_brute_force(pattern, client_ip, auth_success)
            
        elif pattern.name == "api_key_scanning":
            return await self._check_api_key_scanning(pattern, client_ip, additional_data)
            
        elif pattern.name == "rate_limit_abuse":
            return await self._check_rate_abuse(pattern, client_ip, additional_data)
            
        elif pattern.name == "debug_endpoint_probing":
            return await self._check_debug_probing(pattern, client_ip, endpoint)
            
        elif pattern.name == "suspicious_user_agent":
            return await self._check_suspicious_agent(pattern, client_ip, user_agent)
            
        elif pattern.name == "anomalous_request_patterns":
            return await self._check_anomalous_patterns(pattern, client_ip, method, endpoint)
        
        return None
    
    async def _check_brute_force(self, pattern: ThreatPattern, client_ip: str, auth_success: bool) -> Optional[Dict[str, Any]]:
        """ブルートフォース攻撃のチェック"""
        if auth_success:
            return None
        
        now = datetime.now()
        window_start = now - timedelta(minutes=pattern.conditions["time_window_minutes"])
        
        # 最近の失敗試行を記録
        self.failed_attempts[client_ip].append(now)
        
        # ウィンドウ内の失敗回数をカウント
        recent_failures = sum(
            1 for attempt_time in self.failed_attempts[client_ip]
            if attempt_time > window_start
        )
        
        if recent_failures >= pattern.conditions["failed_attempts_threshold"]:
            return {
                "pattern_name": pattern.name,
                "severity": pattern.severity.value,
                "auto_block": pattern.auto_block,
                "details": {
                    "failed_attempts": recent_failures,
                    "threshold": pattern.conditions["failed_attempts_threshold"],
                    "time_window": pattern.conditions["time_window_minutes"]
                }
            }
        
        return None
    
    async def _check_api_key_scanning(self, pattern: ThreatPattern, client_ip: str, additional_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """APIキースキャニングのチェック"""
        if not additional_data or additional_data.get("auth_type") != "api_key" or additional_data.get("success"):
            return None
        
        now = datetime.now()
        window_start = now - timedelta(minutes=pattern.conditions["time_window_minutes"])
        
        # 無効なAPIキー試行を記録
        key = f"api_scan_{client_ip}"
        if key not in self.suspicious_patterns:
            self.suspicious_patterns[key] = []
        
        self.suspicious_patterns[key].append(
            AttackAttempt(
                ip_address=client_ip,
                attack_type="api_key_scan",
                timestamp=now,
                severity=pattern.severity,
                details=additional_data
            )
        )
        
        # ウィンドウ内の試行回数をカウント
        recent_attempts = sum(
            1 for attempt in self.suspicious_patterns[key]
            if attempt.timestamp > window_start
        )
        
        if recent_attempts >= pattern.conditions["invalid_key_attempts"]:
            return {
                "pattern_name": pattern.name,
                "severity": pattern.severity.value,
                "auto_block": pattern.auto_block,
                "details": {
                    "invalid_attempts": recent_attempts,
                    "threshold": pattern.conditions["invalid_key_attempts"]
                }
            }
        
        return None
    
    async def _check_rate_abuse(self, pattern: ThreatPattern, client_ip: str, additional_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """レート制限乱用のチェック"""
        if not additional_data or not additional_data.get("rate_limit_exceeded"):
            return None
        
        now = datetime.now()
        window_start = now - timedelta(minutes=pattern.conditions["time_window_minutes"])
        
        # レート制限違反を記録
        self.rate_limit_violations[client_ip].append(now)
        
        # ウィンドウ内の違反回数をカウント
        recent_violations = sum(
            1 for violation_time in self.rate_limit_violations[client_ip]
            if violation_time > window_start
        )
        
        if recent_violations >= pattern.conditions["rate_violations"]:
            return {
                "pattern_name": pattern.name,
                "severity": pattern.severity.value,
                "auto_block": pattern.auto_block,
                "details": {
                    "violations": recent_violations,
                    "threshold": pattern.conditions["rate_violations"]
                }
            }
        
        return None
    
    async def _check_debug_probing(self, pattern: ThreatPattern, client_ip: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """デバッグエンドポイント探査のチェック"""
        debug_endpoints = ["/debug", "/admin", "/.env", "/config", "/status", "/health", "/metrics"]
        
        if not any(debug_path in endpoint.lower() for debug_path in debug_endpoints):
            return None
        
        now = datetime.now()
        window_start = now - timedelta(minutes=pattern.conditions["time_window_minutes"])
        
        # デバッグアクセス試行を記録
        key = f"debug_probe_{client_ip}"
        if key not in self.suspicious_patterns:
            self.suspicious_patterns[key] = []
        
        self.suspicious_patterns[key].append(
            AttackAttempt(
                ip_address=client_ip,
                attack_type="debug_probing",
                timestamp=now,
                severity=pattern.severity,
                details={"endpoint": endpoint}
            )
        )
        
        # ウィンドウ内の試行回数をカウント
        recent_attempts = sum(
            1 for attempt in self.suspicious_patterns[key]
            if attempt.timestamp > window_start
        )
        
        if recent_attempts >= pattern.conditions["debug_access_attempts"]:
            return {
                "pattern_name": pattern.name,
                "severity": pattern.severity.value,
                "auto_block": pattern.auto_block,
                "details": {
                    "attempts": recent_attempts,
                    "endpoint": endpoint,
                    "threshold": pattern.conditions["debug_access_attempts"]
                }
            }
        
        return None
    
    async def _check_suspicious_agent(self, pattern: ThreatPattern, client_ip: str, user_agent: str) -> Optional[Dict[str, Any]]:
        """不審なユーザーエージェントのチェック"""
        user_agent_lower = user_agent.lower()
        
        for blacklisted_agent in pattern.conditions["blacklisted_agents"]:
            if blacklisted_agent in user_agent_lower:
                return {
                    "pattern_name": pattern.name,
                    "severity": pattern.severity.value,
                    "auto_block": pattern.auto_block,
                    "details": {
                        "user_agent": user_agent,
                        "matched_pattern": blacklisted_agent
                    }
                }
        
        return None
    
    async def _check_anomalous_patterns(self, pattern: ThreatPattern, client_ip: str, method: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """異常なリクエストパターンのチェック"""
        # 実装例: 短時間での大量リクエスト検出
        now = datetime.now()
        window_start = now - timedelta(minutes=pattern.conditions["time_window_minutes"])
        
        key = f"requests_{client_ip}"
        if key not in self.suspicious_patterns:
            self.suspicious_patterns[key] = []
        
        self.suspicious_patterns[key].append(
            AttackAttempt(
                ip_address=client_ip,
                attack_type="request_spike",
                timestamp=now,
                severity=pattern.severity,
                details={"method": method, "endpoint": endpoint}
            )
        )
        
        # ウィンドウ内のリクエスト数をカウント
        recent_requests = sum(
            1 for attempt in self.suspicious_patterns[key]
            if attempt.timestamp > window_start
        )
        
        if recent_requests >= pattern.conditions["request_spike_threshold"]:
            return {
                "pattern_name": pattern.name,
                "severity": pattern.severity.value,
                "auto_block": pattern.auto_block,
                "details": {
                    "requests": recent_requests,
                    "threshold": pattern.conditions["request_spike_threshold"]
                }
            }
        
        return None
    
    def _calculate_threat_level(self, detected_threats: List[Dict[str, Any]]) -> str:
        """総合的な脅威レベルの計算"""
        if not detected_threats:
            return "none"
        
        max_severity = max(
            threat.get("severity", "low") for threat in detected_threats
        )
        
        if max_severity == "critical":
            return "critical"
        elif max_severity == "high":
            return "high"
        elif max_severity == "medium":
            return "medium"
        else:
            return "low"
    
    async def _is_blocked(self, client_ip: str) -> bool:
        """IPアドレスがブロックされているかチェック"""
        if client_ip not in self.blocked_ips:
            return False
        
        block_time = self.blocked_ips[client_ip]
        if datetime.now() > block_time + self.block_duration:
            # ブロック期間終了
            del self.blocked_ips[client_ip]
            return False
        
        return True
    
    async def _block_ip(self, client_ip: str, threats: List[Dict[str, Any]]) -> None:
        """IPアドレスをブロック"""
        self.blocked_ips[client_ip] = datetime.now()
        self.metrics["total_blocked_ips"] += 1
        
        # セキュリティログに記録
        security_audit_logger.log_security_violation(
            violation_type="ip_address_blocked",
            description="IP address automatically blocked due to threats",
            client_ip=client_ip,
            details={
                "threats": threats,
                "block_duration_minutes": self.block_duration.total_seconds() / 60,
                "auto_blocked": True
            }
        )
        
        self.logger.warning(f"IP {client_ip} blocked due to threats: {[t['pattern_name'] for t in threats]}")
    
    def _generate_recommendations(self, detected_threats: List[Dict[str, Any]]) -> List[str]:
        """脅威に基づく推奨事項の生成"""
        recommendations = []
        
        for threat in detected_threats:
            pattern_name = threat.get("pattern_name", "")
            
            if pattern_name == "brute_force_login":
                recommendations.append("Enable account lockout after failed attempts")
                recommendations.append("Implement CAPTCHA for repeated failures")
                
            elif pattern_name == "api_key_scanning":
                recommendations.append("Monitor API key usage patterns")
                recommendations.append("Implement API key rotation")
                
            elif pattern_name == "rate_limit_abuse":
                recommendations.append("Consider stricter rate limiting")
                recommendations.append("Implement progressive delays")
                
            elif pattern_name == "debug_endpoint_probing":
                recommendations.append("Remove debug endpoints from production")
                recommendations.append("Implement IP whitelist for admin endpoints")
        
        return list(set(recommendations))  # 重複を除去
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """セキュリティメトリクスの取得"""
        return {
            **self.metrics,
            "currently_blocked_ips": len(self.blocked_ips),
            "active_threat_patterns": len([
                pattern for pattern in self.suspicious_patterns
                if self.suspicious_patterns[pattern]
            ]),
            "monitoring_since": datetime.now().isoformat()
        }
    
    async def unblock_ip(self, client_ip: str, reason: str = "manual") -> bool:
        """IPアドレスのブロック解除"""
        if client_ip in self.blocked_ips:
            del self.blocked_ips[client_ip]
            
            security_audit_logger.log_security_violation(
                violation_type="ip_address_unblocked",
                description="IP address manually unblocked",
                client_ip=client_ip,
                details={
                    "reason": reason,
                    "unblocked_by": "admin"
                }
            )
            
            self.logger.info(f"IP {client_ip} unblocked (reason: {reason})")
            return True
        
        return False


# グローバルインスタンス
intrusion_detection_system = IntrusionDetectionSystem()


async def analyze_request_security(client_ip: str,
                                  user_agent: str,
                                  endpoint: str,
                                  method: str = "GET",
                                  auth_success: bool = True,
                                  additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """リクエストのセキュリティ分析"""
    return await intrusion_detection_system.analyze_request(
        client_ip, user_agent, endpoint, method, auth_success, additional_data
    )


def get_ids_metrics() -> Dict[str, Any]:
    """侵入検知システムのメトリクス取得"""
    return intrusion_detection_system.get_security_metrics()


async def manually_unblock_ip(ip_address: str) -> bool:
    """手動でIPアドレスのブロックを解除"""
    return await intrusion_detection_system.unblock_ip(ip_address, "manual_admin_action")
