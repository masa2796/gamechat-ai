"""
バックグラウンドタスク管理
重い処理を非同期で実行してレスポンス時間を改善
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BackgroundTask:
    id: str
    name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class BackgroundTaskManager:
    """バックグラウンドタスク管理クラス"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
    
    async def submit_task(
        self, 
        func: Callable, 
        name: str, 
        *args, 
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        バックグラウンドタスクを投入
        """
        task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            id=task_id,
            name=name,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        
        # 非同期でタスクを実行
        asyncio_task = asyncio.create_task(
            self._execute_task(task_id, func, *args, **kwargs)
        )
        self.running_tasks[task_id] = asyncio_task
        
        logger.info(f"📋 Background task submitted: {name} (ID: {task_id})")
        return task_id
    
    async def _execute_task(self, task_id: str, func: Callable, *args, **kwargs):
        """タスクを実行"""
        task = self.tasks[task_id]
        
        async with self.semaphore:  # 同時実行数制限
            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                logger.info(f"🚀 Starting background task: {task.name}")
                
                # 関数が非同期かどうかをチェック
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # 同期関数を非同期で実行
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, func, *args, **kwargs
                    )
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress = 100.0
                
                duration = (task.completed_at - task.started_at).total_seconds()
                logger.info(f"✅ Background task completed: {task.name} ({duration:.2f}s)")
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                
                logger.error(f"❌ Background task failed: {task.name} - {e}")
            
            finally:
                # 実行中タスクリストから削除
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
    
    def get_task_status(self, task_id: str) -> Optional[BackgroundTask]:
        """タスクの状態を取得"""
        return self.tasks.get(task_id)
    
    async def wait_for_task(self, task_id: str, timeout: float = 30.0) -> Optional[Any]:
        """タスクの完了を待機"""
        if task_id not in self.tasks:
            return None
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            task = self.tasks[task_id]
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.status == TaskStatus.COMPLETED:
                    return task.result
                else:
                    raise Exception(f"Task failed: {task.error}")
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(0.1)
    
    async def cancel_task(self, task_id: str) -> bool:
        """タスクをキャンセル"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus.CANCELLED
            return True
        return False
    
    def get_all_tasks(self) -> Dict[str, BackgroundTask]:
        """全タスクの状態を取得"""
        return self.tasks.copy()
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """古いタスクをクリーンアップ"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        tasks_to_remove = [
            task_id for task_id, task in self.tasks.items()
            if task.created_at < cutoff_time and 
               task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.debug(f"🗑️ Cleaned up old task: {task_id}")
        
        if tasks_to_remove:
            logger.info(f"🧹 Cleaned up {len(tasks_to_remove)} old tasks")

# グローバルタスクマネージャー
task_manager = BackgroundTaskManager(max_concurrent_tasks=3)

async def start_background_cleanup():
    """バックグラウンドクリーンアップタスクを開始"""
    while True:
        try:
            await task_manager.cleanup_old_tasks()
            await asyncio.sleep(3600)  # 1時間ごと
        except Exception as e:
            logger.error(f"Background cleanup error: {e}")
            await asyncio.sleep(300)  # エラー時は5分後に再試行

# 高負荷処理用のラッパー関数
async def process_heavy_rag_query(question: str, top_k: int = 50) -> Dict[str, Any]:
    """
    重いRAGクエリをバックグラウンドで処理
    """
    from ..services.rag_service import RagService
    from ..models.rag_models import RagRequest
    
    rag_service = RagService()
    rag_request = RagRequest(question=question, top_k=top_k, with_context=True)
    
    logger.info(f"🔄 Processing heavy RAG query in background: {question[:50]}...")
    result = await rag_service.process_query(rag_request)
    
    return result

async def precompute_popular_queries():
    """
    人気のあるクエリを事前計算してキャッシュ
    """
    popular_queries = [
        "おすすめのゲーム",
        "初心者向けの攻略",
        "最新ゲーム情報",
        "人気ランキング",
        "ゲーム攻略のコツ"
    ]
    
    results = {}
    for query in popular_queries:
        try:
            result = await process_heavy_rag_query(query, top_k=10)
            results[query] = result
            logger.info(f"✅ Precomputed result for: {query}")
        except Exception as e:
            logger.error(f"❌ Failed to precompute {query}: {e}")
    
    return results
