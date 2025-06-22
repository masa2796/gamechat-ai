"""
パフォーマンス最適化用のプロファイリングと監視機能
"""
import time
import functools
from typing import Dict, Any, Callable, Optional, List, AsyncIterator
from datetime import datetime
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """パフォーマンス測定・プロファイリング用クラス"""
    
    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """タイマー開始"""
        self.start_times[operation] = time.perf_counter()
        logger.debug(f"⏱️ Starting timer for: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """タイマー終了と経過時間取得"""
        if operation not in self.start_times:
            logger.warning(f"Timer not started for operation: {operation}")
            return 0.0
        
        elapsed = time.perf_counter() - self.start_times[operation]
        
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(elapsed)
        
        logger.debug(f"⏱️ {operation}: {elapsed:.3f}s")
        return elapsed
    
    @asynccontextmanager
    async def timer(self, operation: str) -> AsyncIterator[None]:
        """コンテキストマネージャーとしてのタイマー"""
        start_time = time.perf_counter()
        logger.debug(f"⏱️ Starting: {operation}")
        
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed)
            logger.info(f"⏱️ {operation}: {elapsed:.3f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        summary = {}
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    "count": len(times),
                    "total": sum(times),
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "last": times[-1] if times else 0
                }
        return summary
    
    def clear(self) -> None:
        """メトリクスをクリア"""
        self.metrics.clear()
        self.start_times.clear()


def async_timer(operation_name: str) -> Callable:
    """非同期関数用デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            logger.debug(f"⏱️ Starting: {operation_name}")
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time
                logger.info(f"⏱️ {operation_name}: {elapsed:.3f}s")
        
        return wrapper
    return decorator


def sync_timer(operation_name: str) -> Callable:
    """同期関数用デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            logger.debug(f"⏱️ Starting: {operation_name}")
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time
                logger.info(f"⏱️ {operation_name}: {elapsed:.3f}s")
        
        return wrapper
    return decorator


class BottleneckDetector:
    """ボトルネック検出機能"""
    
    def __init__(self, threshold_seconds: float = 1.0):
        self.threshold = threshold_seconds
        self.bottlenecks: List[Dict[str, Any]] = []
    
    def check_operation(self, operation: str, duration: float, context: Optional[Dict] = None) -> None:
        """操作の実行時間をチェックしてボトルネックを検出"""
        if duration > self.threshold:
            bottleneck = {
                "operation": operation,
                "duration": duration,
                "threshold": self.threshold,
                "timestamp": datetime.now().isoformat(),
                "severity": self._get_severity(duration),
                "context": context or {}
            }
            self.bottlenecks.append(bottleneck)
            
            severity_emoji = "🔴" if bottleneck["severity"] == "critical" else "🟡"
            logger.warning(
                f"{severity_emoji} Bottleneck detected: {operation} took {duration:.3f}s "
                f"(threshold: {self.threshold}s)"
            )
    
    def _get_severity(self, duration: float) -> str:
        """実行時間に基づく重要度判定"""
        if duration > self.threshold * 5:
            return "critical"
        elif duration > self.threshold * 2:
            return "high"
        else:
            return "medium"
    
    def get_report(self) -> Dict[str, Any]:
        """ボトルネックレポートを生成"""
        if not self.bottlenecks:
            return {"status": "no_bottlenecks", "bottlenecks": []}
        
        return {
            "status": "bottlenecks_detected",
            "total_count": len(self.bottlenecks),
            "critical_count": len([b for b in self.bottlenecks if b["severity"] == "critical"]),
            "bottlenecks": self.bottlenecks[-10:]  # 最新10件
        }


# グローバルインスタンス
profiler = PerformanceProfiler()
bottleneck_detector = BottleneckDetector(threshold_seconds=2.0)
