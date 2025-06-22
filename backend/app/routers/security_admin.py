"""
セキュリティ管理エンドポイント
管理者向けのセキュリティ監視とAPIキーローテーション機能
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Dict, Any
import logging
from datetime import datetime

from ..core.auth import require_read_permission
from ..core.log_security import security_audit_logger
from ..core.api_key_rotation import api_key_rotation_manager
from ..core.security_audit_manager import security_audit_manager
from ..core.intrusion_detection import intrusion_detection_system

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/security", tags=["Security Management"])


@router.get("/status")
async def get_security_status(
    request: Request,
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """
    システム全体のセキュリティ状況を取得
    管理者権限が必要
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 管理者権限チェック
    if auth_info.get("user_info", {}).get("name") not in ["production", "development"]:
        security_audit_logger.log_suspicious_activity(
            activity_type="unauthorized_admin_access",
            client_ip=client_ip,
            description="Non-admin user attempted to access security status",
            severity="high",
            details={"auth_info": auth_info}
        )
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        # 各システムの状況を取得
        rotation_status = api_key_rotation_manager.get_rotation_status()
        latest_audit = await security_audit_manager.get_latest_audit_summary()
        ids_metrics = intrusion_detection_system.get_security_metrics()
        
        security_status = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "api_key_rotation": {
                "status": rotation_status,
                "keys_needing_rotation": [
                    key for key, info in rotation_status.items()
                    if info.get("needs_rotation", False)
                ]
            },
            "latest_security_audit": latest_audit,
            "intrusion_detection": {
                "status": "active",
                "metrics": ids_metrics,
                "blocked_ips_count": ids_metrics.get("currently_blocked_ips", 0)
            },
            "overall_security_score": latest_audit.get("overall_score", 0) if latest_audit else 0
        }
        
        # セキュリティログに記録
        security_audit_logger.log_api_key_usage(
            api_key_type=auth_info.get("user_info", {}).get("name", "unknown"),
            endpoint="/admin/security/status",
            client_ip=client_ip,
            details={"requested_by": auth_info}
        )
        
        return security_status
        
    except Exception as e:
        logger.error(f"Error retrieving security status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security status")


@router.post("/api-key/rotate/{key_type}")
async def rotate_api_key(
    key_type: str,
    request: Request,
    force: bool = Query(False, description="Force rotation even if not needed"),
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """
    指定されたAPIキーのローテーションを実行
    管理者権限が必要
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 管理者権限チェック
    if auth_info.get("user_info", {}).get("name") not in ["production", "development"]:
        security_audit_logger.log_suspicious_activity(
            activity_type="unauthorized_admin_action",
            client_ip=client_ip,
            description=f"Non-admin user attempted to rotate API key: {key_type}",
            severity="critical",
            details={"auth_info": auth_info, "key_type": key_type}
        )
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # 有効なキータイプのチェック
    valid_key_types = ["production", "development", "frontend", "readonly"]
    if key_type not in valid_key_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid key type. Must be one of: {', '.join(valid_key_types)}"
        )
    
    try:
        result = await api_key_rotation_manager.rotate_api_key(key_type, force)
        
        # セキュリティログに記録
        security_audit_logger.log_security_violation(
            violation_type="api_key_rotation_requested",
            description=f"API key rotation requested for {key_type}",
            client_ip=client_ip,
            details={
                "key_type": key_type,
                "force": force,
                "requested_by": auth_info.get("user_info", {}).get("name"),
                "success": result.get("success", False)
            }
        )
        
        if result.get("success"):
            # 機密情報をマスク
            result["new_key"] = f"***{result['new_key'][-8:]}"
            
        return result
        
    except Exception as e:
        logger.error(f"Error rotating API key {key_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rotate API key: {str(e)}")


@router.get("/audit/latest")
async def get_latest_audit(
    request: Request,
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """
    最新のセキュリティ監査結果を取得
    管理者権限が必要
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 管理者権限チェック
    if auth_info.get("user_info", {}).get("name") not in ["production", "development"]:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        latest_audit = await security_audit_manager.get_latest_audit_summary()
        
        if not latest_audit:
            return {"message": "No audit results available", "audit_available": False}
        
        # セキュリティログに記録
        security_audit_logger.log_api_key_usage(
            api_key_type=auth_info.get("user_info", {}).get("name", "unknown"),
            endpoint="/admin/security/audit/latest",
            client_ip=client_ip
        )
        
        return {"audit_available": True, **latest_audit}
        
    except Exception as e:
        logger.error(f"Error retrieving latest audit: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit results")


@router.post("/audit/run")
async def run_security_audit(
    request: Request,
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """
    新しいセキュリティ監査を実行
    管理者権限が必要
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 管理者権限チェック
    if auth_info.get("user_info", {}).get("name") not in ["production", "development"]:
        security_audit_logger.log_suspicious_activity(
            activity_type="unauthorized_admin_action",
            client_ip=client_ip,
            description="Non-admin user attempted to run security audit",
            severity="high",
            details={"auth_info": auth_info}
        )
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        # セキュリティ監査を開始
        audit_result = await security_audit_manager.run_comprehensive_audit()
        
        # セキュリティログに記録
        security_audit_logger.log_security_violation(
            violation_type="security_audit_initiated",
            description="Security audit manually initiated",
            client_ip=client_ip,
            details={
                "audit_id": audit_result.get("audit_id"),
                "initiated_by": auth_info.get("user_info", {}).get("name"),
                "overall_score": audit_result.get("overall_score")
            }
        )
        
        # 機密情報を除去してレスポンス
        response = {
            "audit_id": audit_result.get("audit_id"),
            "start_time": audit_result.get("start_time"),
            "end_time": audit_result.get("end_time"),
            "duration_seconds": audit_result.get("duration_seconds"),
            "overall_score": audit_result.get("overall_score"),
            "summary": {
                "total_issues": sum(
                    len(result.get("issues", []))
                    for result in audit_result.get("results", {}).values()
                    if isinstance(result, dict)
                )
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error running security audit: {e}")
        raise HTTPException(status_code=500, detail="Failed to run security audit")


@router.get("/intrusion-detection/metrics")
async def get_ids_metrics(
    request: Request,
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """
    侵入検知システムのメトリクスを取得
    管理者権限が必要
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 管理者権限チェック
    if auth_info.get("user_info", {}).get("name") not in ["production", "development"]:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        metrics = intrusion_detection_system.get_security_metrics()
        
        # セキュリティログに記録
        security_audit_logger.log_api_key_usage(
            api_key_type=auth_info.get("user_info", {}).get("name", "unknown"),
            endpoint="/admin/security/intrusion-detection/metrics",
            client_ip=client_ip
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving IDS metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve IDS metrics")


@router.post("/intrusion-detection/unblock/{ip_address}")
async def unblock_ip_address(
    ip_address: str,
    request: Request,
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """
    指定されたIPアドレスのブロックを解除
    管理者権限が必要
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 管理者権限チェック
    if auth_info.get("user_info", {}).get("name") not in ["production", "development"]:
        security_audit_logger.log_suspicious_activity(
            activity_type="unauthorized_admin_action",
            client_ip=client_ip,
            description=f"Non-admin user attempted to unblock IP: {ip_address}",
            severity="critical",
            details={"auth_info": auth_info, "target_ip": ip_address}
        )
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        success = await intrusion_detection_system.unblock_ip(
            ip_address,
            f"manually_unblocked_by_{auth_info.get('user_info', {}).get('name', 'admin')}"
        )
        
        # セキュリティログに記録
        security_audit_logger.log_security_violation(
            violation_type="ip_unblock_requested",
            description=f"IP address unblock requested: {ip_address}",
            client_ip=client_ip,
            details={
                "target_ip": ip_address,
                "requested_by": auth_info.get("user_info", {}).get("name"),
                "success": success
            }
        )
        
        return {
            "success": success,
            "ip_address": ip_address,
            "message": "IP address unblocked successfully" if success else "IP address was not blocked"
        }
        
    except Exception as e:
        logger.error(f"Error unblocking IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unblock IP address: {str(e)}")


@router.get("/health")
async def security_health_check() -> Dict[str, Any]:
    """
    セキュリティシステムの健全性チェック
    認証不要の公開エンドポイント
    """
    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "security_systems": {
                "api_key_rotation": "operational",
                "security_audit": "operational", 
                "intrusion_detection": "operational",
                "log_security": "operational"
            },
            "overall_status": "healthy"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "degraded",
            "error": str(e)
        }
