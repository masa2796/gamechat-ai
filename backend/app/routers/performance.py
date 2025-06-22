"""
パフォーマンス監視用のAPI エンドポイント
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..core.performance import profiler, bottleneck_detector
from ..core.cache import query_cache, search_cache
import time
import psutil
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])

@router.get("/metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    システムパフォーマンスメトリクスを取得
    """
    try:
        # プロファイラー統計
        profiler_stats = profiler.get_summary()
        
        # ボトルネック情報
        bottleneck_report = bottleneck_detector.get_report()
        
        # キャッシュ統計
        query_cache_stats = await query_cache.get_stats()
        
        # システムリソース情報
        system_stats = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
            "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
        
        return {
            "timestamp": time.time(),
            "profiler": profiler_stats,
            "bottlenecks": bottleneck_report,
            "cache": {
                "query_cache": query_cache_stats
            },
            "system": system_stats
        }
        
    except Exception as e:
        logger.error(f"パフォーマンスメトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="メトリクス取得に失敗しました")

@router.get("/health")
async def performance_health_check() -> Dict[str, Any]:
    """
    パフォーマンス状態のヘルスチェック
    """
    try:
        # 基本的な状態確認
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        # ヘルス判定
        health_status = "healthy"
        issues = []
        
        if cpu_percent > 80:
            health_status = "warning"
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        if memory_percent > 85:
            health_status = "warning"
            issues.append(f"High memory usage: {memory_percent}%")
        
        # ボトルネック確認
        bottleneck_report = bottleneck_detector.get_report()
        if bottleneck_report["status"] == "bottlenecks_detected":
            critical_count = bottleneck_report["critical_count"]
            if critical_count > 0:
                health_status = "critical"
                issues.append(f"Critical bottlenecks detected: {critical_count}")
        
        return {
            "status": health_status,
            "timestamp": time.time(),
            "issues": issues,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent
            }
        }
        
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return {
            "status": "error",
            "timestamp": time.time(),
            "error": str(e)
        }

@router.post("/clear-cache")
async def clear_performance_cache() -> Dict[str, str]:
    """
    パフォーマンスキャッシュをクリア
    """
    try:
        # キャッシュクリア
        await query_cache.clear_cache()
        
        # プロファイラーリセット
        profiler.clear()
        
        logger.info("パフォーマンスキャッシュをクリアしました")
        return {"message": "キャッシュがクリアされました"}
        
    except Exception as e:
        logger.error(f"キャッシュクリアエラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュクリアに失敗しました")

@router.get("/bottlenecks")
async def get_bottleneck_report() -> Dict[str, Any]:
    """
    詳細なボトルネックレポートを取得
    """
    try:
        report = bottleneck_detector.get_report()
        
        # 追加分析
        if report["bottlenecks"]:
            # 最も遅い操作
            slowest = max(report["bottlenecks"], key=lambda x: x["duration"])
            
            # 操作タイプ別集計
            operation_stats = {}
            for bottleneck in report["bottlenecks"]:
                op_type = bottleneck["operation"]
                if op_type not in operation_stats:
                    operation_stats[op_type] = {
                        "count": 0,
                        "total_duration": 0,
                        "max_duration": 0
                    }
                
                operation_stats[op_type]["count"] += 1
                operation_stats[op_type]["total_duration"] += bottleneck["duration"]
                operation_stats[op_type]["max_duration"] = max(
                    operation_stats[op_type]["max_duration"],
                    bottleneck["duration"]
                )
            
            report["analysis"] = {
                "slowest_operation": slowest,
                "operation_stats": operation_stats
            }
        
        return report
        
    except Exception as e:
        logger.error(f"ボトルネックレポート取得エラー: {e}")
        raise HTTPException(status_code=500, detail="レポート取得に失敗しました")
