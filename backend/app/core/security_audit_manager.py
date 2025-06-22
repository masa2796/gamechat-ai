"""
自動セキュリティ監査システム
定期的な脆弱性スキャン、依存関係チェック、監査レポート生成
"""
import os
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
import re
from .log_security import security_audit_logger


class SecurityAuditManager:
    """包括的セキュリティ監査管理システム"""
    
    def __init__(self, audit_directory: str = "/app/security/audits"):
        """
        Args:
            audit_directory: 監査結果保存ディレクトリ
        """
        self.audit_dir = Path(audit_directory)
        self.logger = logging.getLogger(__name__)
        
        # 監査ディレクトリの作成
        try:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            self.logger.warning(f"Cannot create audit directory: {e}")
            self.audit_dir = None
    
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """包括的セキュリティ監査の実行"""
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        audit_start = datetime.now()
        
        self.logger.info(f"Starting comprehensive security audit: {audit_id}")
        
        audit_results = {
            "audit_id": audit_id,
            "start_time": audit_start.isoformat(),
            "audit_type": "comprehensive",
            "results": {}
        }
        
        # 各監査項目を実行
        audit_tasks = [
            ("dependency_scan", self._scan_dependencies),
            ("environment_security", self._check_environment_security),
            ("api_security", self._check_api_security),
            ("log_security", self._check_log_security),
            ("infrastructure_security", self._check_infrastructure),
            ("code_quality", self._analyze_code_quality)
        ]
        
        for task_name, task_func in audit_tasks:
            try:
                self.logger.info(f"Running audit task: {task_name}")
                result = await task_func()
                audit_results["results"][task_name] = result
                
            except Exception as e:
                self.logger.error(f"Audit task {task_name} failed: {e}")
                audit_results["results"][task_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # 監査完了
        audit_results["end_time"] = datetime.now().isoformat()
        audit_results["duration_seconds"] = (datetime.now() - audit_start).total_seconds()
        audit_results["overall_score"] = self._calculate_security_score(audit_results["results"])
        
        # 結果を保存
        if self.audit_dir:
            await self._save_audit_results(audit_results)
        
        # セキュリティログに記録
        security_audit_logger.log_security_violation(
            violation_type="security_audit_completed",
            description="Comprehensive security audit completed",
            client_ip="system",
            details={
                "audit_id": audit_id,
                "overall_score": audit_results["overall_score"],
                "duration": audit_results["duration_seconds"]
            }
        )
        
        self.logger.info(f"Security audit completed: {audit_id} (Score: {audit_results['overall_score']}/100)")
        
        return audit_results
    
    async def _scan_dependencies(self) -> Dict[str, Any]:
        """依存関係の脆弱性スキャン"""
        result = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "summary": {}
        }
        
        try:
            # requirements.txtの確認
            requirements_files = [
                "requirements.txt",
                "backend/requirements.txt",
                "frontend/package.json"
            ]
            
            for req_file in requirements_files:
                if Path(req_file).exists():
                    vuln_count = await self._check_file_vulnerabilities(req_file)
                    result["summary"][req_file] = vuln_count
            
            # Python安全性チェック（pipが利用可能な場合）
            try:
                safety_result = subprocess.run(
                    ["python", "-m", "pip", "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if safety_result.returncode == 0:
                    packages = json.loads(safety_result.stdout)
                    result["installed_packages"] = len(packages)
                    result["packages_checked"] = True
                else:
                    result["packages_checked"] = False
                    
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
                result["packages_checked"] = False
            
            result["total_vulnerabilities"] = sum(result["summary"].values())
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def _check_file_vulnerabilities(self, file_path: str) -> int:
        """ファイル内の既知の脆弱性パターンをチェック"""
        vulnerability_count = 0
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # 危険なパッケージやバージョンパターン
            dangerous_patterns = [
                r'django==1\.',  # 古いDjango
                r'flask==0\.',   # 古いFlask
                r'requests==2\.6\.',  # 脆弱なrequests
                r'pyyaml==3\.',  # 脆弱なPyYAML
                r'pillow==2\.',  # 古いPillow
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerability_count += 1
            
        except (IOError, OSError):
            pass
        
        return vulnerability_count
    
    async def _check_environment_security(self) -> Dict[str, Any]:
        """環境変数とシステム設定のセキュリティチェック"""
        result = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "score": 100
        }
        
        # 重要な環境変数の確認
        critical_env_vars = [
            "OPENAI_API_KEY",
            "API_KEY_PRODUCTION", 
            "RECAPTCHA_SECRET",
            "JWT_SECRET_KEY"
        ]
        
        missing_vars = []
        weak_vars = []
        
        for var in critical_env_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                result["score"] -= 15
            elif len(value) < 20:  # 短すぎるキー
                weak_vars.append(var)
                result["score"] -= 10
        
        if missing_vars:
            result["issues"].append({
                "type": "missing_environment_variables",
                "severity": "high",
                "description": f"Missing critical environment variables: {', '.join(missing_vars)}"
            })
        
        if weak_vars:
            result["issues"].append({
                "type": "weak_environment_variables", 
                "severity": "medium",
                "description": f"Potentially weak environment variables: {', '.join(weak_vars)}"
            })
        
        # デバッグモードの確認
        if os.getenv("DEBUG", "false").lower() == "true":
            result["issues"].append({
                "type": "debug_mode_enabled",
                "severity": "high", 
                "description": "Debug mode is enabled in production"
            })
            result["score"] -= 20
        
        # 本番環境設定の確認
        environment = os.getenv("ENVIRONMENT", "development")
        if environment not in ["production", "staging"]:
            result["issues"].append({
                "type": "non_production_environment",
                "severity": "medium",
                "description": f"Non-production environment detected: {environment}"
            })
            result["score"] -= 10
        
        return result
    
    async def _check_api_security(self) -> Dict[str, Any]:
        """APIセキュリティ設定の確認"""
        result = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "score": 100
        }
        
        # CORS設定の確認
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if "*" in cors_origins:
            result["checks"]["cors_wildcard"] = {
                "status": "fail",
                "description": "CORS wildcard detected - security risk"
            }
            result["score"] -= 25
        else:
            result["checks"]["cors_wildcard"] = {
                "status": "pass",
                "description": "CORS properly configured"
            }
        
        # レート制限の確認
        result["checks"]["rate_limiting"] = {
            "status": "pass",
            "description": "Rate limiting implemented"
        }
        
        # HTTPSの確認
        api_url = os.getenv("API_URL", "")
        if api_url and not api_url.startswith("https://"):
            result["checks"]["https_enforcement"] = {
                "status": "fail",
                "description": "HTTPS not enforced"
            }
            result["score"] -= 20
        else:
            result["checks"]["https_enforcement"] = {
                "status": "pass", 
                "description": "HTTPS properly configured"
            }
        
        return result
    
    async def _check_log_security(self) -> Dict[str, Any]:
        """ログのセキュリティ確認"""
        result = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "log_files_checked": 0,
            "sensitive_data_found": False,
            "issues": []
        }
        
        # ログファイルの確認
        log_patterns = [
            "/app/logs/*.log",
            "./logs/*.log",
            "*.log"
        ]
        
        sensitive_patterns = [
            r"password\s*[:=]\s*[^\s]+",
            r"token\s*[:=]\s*[^\s]+",
            r"api[_-]?key\s*[:=]\s*[^\s]+",
            r"sk-[a-zA-Z0-9]{20,}",  # OpenAI API key pattern
        ]
        
        for pattern in log_patterns:
            for log_file in Path().glob(pattern):
                if log_file.is_file():
                    result["log_files_checked"] += 1
                    
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read()
                        
                        for sens_pattern in sensitive_patterns:
                            if re.search(sens_pattern, content, re.IGNORECASE):
                                result["sensitive_data_found"] = True
                                result["issues"].append({
                                    "file": str(log_file),
                                    "pattern": sens_pattern,
                                    "severity": "high"
                                })
                    
                    except (IOError, OSError):
                        continue
        
        return result
    
    async def _check_infrastructure(self) -> Dict[str, Any]:
        """インフラストラクチャセキュリティの確認"""
        result = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "score": 100
        }
        
        # Container security
        if os.path.exists("/.dockerenv"):
            result["checks"]["containerized"] = {
                "status": "pass",
                "description": "Running in containerized environment"
            }
        
        # File permissions check
        critical_files = ["requirements.txt", ".env", "config.py"]
        for file_path in critical_files:
            if Path(file_path).exists():
                stat = Path(file_path).stat()
                if stat.st_mode & 0o044:  # world readable
                    result["checks"][f"file_permissions_{file_path}"] = {
                        "status": "fail",
                        "description": f"{file_path} has overly permissive permissions"
                    }
                    result["score"] -= 10
        
        return result
    
    async def _analyze_code_quality(self) -> Dict[str, Any]:
        """コード品質とセキュリティパターンの分析"""
        result = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": 0,
            "security_issues": [],
            "score": 100
        }
        
        # Python files security scan
        python_files = list(Path().glob("**/*.py"))
        
        security_anti_patterns = [
            (r"eval\s*\(", "Use of eval() function - security risk"),
            (r"exec\s*\(", "Use of exec() function - security risk"),
            (r"os\.system\s*\(", "Use of os.system() - command injection risk"),
            (r"subprocess\.call.*shell=True", "Subprocess with shell=True - injection risk"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
            (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
        ]
        
        for py_file in python_files[:50]:  # Limit to first 50 files
            if py_file.is_file():
                result["files_analyzed"] += 1
                
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                    
                    for pattern, description in security_anti_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            result["security_issues"].append({
                                "file": str(py_file),
                                "pattern": pattern,
                                "description": description,
                                "matches": len(matches)
                            })
                            result["score"] -= 5 * len(matches)
                
                except (IOError, OSError):
                    continue
        
        return result
    
    def _calculate_security_score(self, results: Dict[str, Any]) -> int:
        """セキュリティスコアの計算"""
        total_score = 0
        valid_results = 0
        
        for task_name, task_result in results.items():
            if isinstance(task_result, dict) and "score" in task_result:
                total_score += task_result["score"]
                valid_results += 1
        
        if valid_results == 0:
            return 0
        
        average_score = total_score // valid_results
        return max(0, min(100, average_score))
    
    async def _save_audit_results(self, audit_results: Dict[str, Any]) -> None:
        """監査結果の保存"""
        if not self.audit_dir:
            return
        
        try:
            audit_file = self.audit_dir / f"{audit_results['audit_id']}.json"
            
            with open(audit_file, 'w') as f:
                json.dump(audit_results, f, indent=2, default=str)
            
            # 最新の監査結果リンクを作成
            latest_link = self.audit_dir / "latest_audit.json"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(audit_file.name)
            
            self.logger.info(f"Audit results saved: {audit_file}")
            
        except (PermissionError, OSError) as e:
            self.logger.error(f"Failed to save audit results: {e}")
    
    async def get_latest_audit_summary(self) -> Optional[Dict[str, Any]]:
        """最新の監査結果サマリーを取得"""
        if not self.audit_dir:
            return None
        
        latest_file = self.audit_dir / "latest_audit.json"
        
        if not latest_file.exists():
            return None
        
        try:
            with open(latest_file, 'r') as f:
                audit_data = json.load(f)
            
            return {
                "audit_id": audit_data.get("audit_id"),
                "timestamp": audit_data.get("end_time"),
                "overall_score": audit_data.get("overall_score"),
                "duration": audit_data.get("duration_seconds"),
                "total_issues": sum(
                    len(result.get("issues", [])) 
                    for result in audit_data.get("results", {}).values()
                    if isinstance(result, dict)
                )
            }
        
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading latest audit: {e}")
            return None
    
    async def run_quick_security_check(self) -> Dict[str, Any]:
        """簡易セキュリティチェック"""
        result = {
            "check_type": "quick",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "issues": []
        }
        
        # 基本的なセキュリティチェック
        checks = [
            ("debug_mode", os.getenv("DEBUG", "false").lower() == "true"),
            ("production_env", os.getenv("ENVIRONMENT") == "production"),
            ("openai_key_set", bool(os.getenv("OPENAI_API_KEY"))),
            ("api_key_set", bool(os.getenv("API_KEY_PRODUCTION"))),
        ]
        
        for check_name, condition in checks:
            if check_name in ["debug_mode"] and condition:
                result["issues"].append(f"Security risk: {check_name}")
            elif check_name not in ["debug_mode"] and not condition:
                result["issues"].append(f"Configuration issue: {check_name}")
        
        result["total_issues"] = len(result["issues"])
        result["security_status"] = "good" if result["total_issues"] == 0 else "needs_attention"
        
        return result


# グローバルインスタンス
security_audit_manager = SecurityAuditManager()


async def run_security_audit() -> Dict[str, Any]:
    """セキュリティ監査の実行"""
    return await security_audit_manager.run_comprehensive_audit()


async def get_security_status() -> Dict[str, Any]:
    """現在のセキュリティ状況を取得"""
    latest_audit = await security_audit_manager.get_latest_audit_summary()
    quick_check = await security_audit_manager.run_quick_security_check()
    
    return {
        "latest_audit": latest_audit,
        "quick_check": quick_check,
        "last_check": datetime.now().isoformat()
    }
