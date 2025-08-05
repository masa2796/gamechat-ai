"""
バックグラウンドタスク管理のテスト
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.core.background_tasks import (
    TaskStatus,
    BackgroundTask,
    BackgroundTaskManager,
    task_manager,
    process_heavy_rag_query,
    precompute_popular_queries,
    start_background_cleanup
)


class TestTaskStatus:
    """TaskStatus enumのテスト"""
    
    def test_task_status_values(self):
        """TaskStatusの値をテスト"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestBackgroundTask:
    """BackgroundTaskデータクラスのテスト"""
    
    def test_background_task_creation(self):
        """BackgroundTaskの作成をテスト"""
        task = BackgroundTask(
            id="test-id",
            name="test-task",
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert task.id == "test-id"
        assert task.name == "test-task"
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.created_at, datetime)
        assert task.started_at is None
        assert task.completed_at is None
        assert task.result is None
        assert task.error is None
        assert task.progress == 0.0
        assert task.metadata is None
    
    def test_background_task_with_metadata(self):
        """メタデータ付きBackgroundTaskの作成をテスト"""
        metadata = {"user_id": "123", "priority": "high"}
        task = BackgroundTask(
            id="test-id",
            name="test-task",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata
        )
        
        assert task.metadata == metadata


class TestBackgroundTaskManager:
    """BackgroundTaskManagerのテスト"""
    
    @pytest.fixture
    def task_manager_instance(self):
        """テスト用のTaskManagerインスタンス"""
        return BackgroundTaskManager(max_concurrent_tasks=2)
    
    def test_task_manager_initialization(self, task_manager_instance):
        """TaskManagerの初期化をテスト"""
        assert len(task_manager_instance.tasks) == 0
        assert len(task_manager_instance.running_tasks) == 0
        assert task_manager_instance.max_concurrent == 2
        assert task_manager_instance.semaphore._value == 2
    
    @pytest.mark.asyncio
    async def test_submit_simple_task(self, task_manager_instance):
        """シンプルなタスクの投入をテスト"""
        
        def simple_task(x, y):
            return x + y
        
        task_id = await task_manager_instance.submit_task(
            simple_task, 
            "addition_task",
            5, 
            3
        )
        
        assert task_id in task_manager_instance.tasks
        task = task_manager_instance.tasks[task_id]
        assert task.name == "addition_task"
        assert task.status == TaskStatus.PENDING
        
        # タスクの完了を待機
        await asyncio.sleep(0.1)
        
        # タスクが完了していることを確認
        updated_task = task_manager_instance.get_task_status(task_id)
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.result == 8
    
    @pytest.mark.asyncio
    async def test_submit_async_task(self, task_manager_instance):
        """非同期タスクの投入をテスト"""
        
        async def async_task(delay, result):
            await asyncio.sleep(delay)
            return result
        
        task_id = await task_manager_instance.submit_task(
            async_task,
            "async_task",
            0.01,  # 短い遅延
            "async_result"
        )
        
        # タスクの完了を待機
        result = await task_manager_instance.wait_for_task(task_id, timeout=1.0)
        assert result == "async_result"
        
        task = task_manager_instance.get_task_status(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100.0
    
    @pytest.mark.asyncio
    async def test_task_with_error(self, task_manager_instance):
        """エラーが発生するタスクのテスト"""
        
        def error_task():
            raise ValueError("Test error")
        
        task_id = await task_manager_instance.submit_task(
            error_task,
            "error_task"
        )
        
        # エラーが発生することを確認
        with pytest.raises(Exception, match="Task failed: Test error"):
            await task_manager_instance.wait_for_task(task_id, timeout=1.0)
        
        task = task_manager_instance.get_task_status(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "Test error"
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, task_manager_instance):
        """タスクのタイムアウトをテスト"""
        
        async def long_task():
            await asyncio.sleep(1.0)
            return "done"
        
        task_id = await task_manager_instance.submit_task(
            long_task,
            "long_task"
        )
        
        # タイムアウトが発生することを確認
        with pytest.raises(TimeoutError):
            await task_manager_instance.wait_for_task(task_id, timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_manager_instance):
        """タスクのキャンセルをテスト"""
        
        async def long_task():
            await asyncio.sleep(1.0)
            return "done"
        
        task_id = await task_manager_instance.submit_task(
            long_task,
            "long_task"
        )
        
        # タスクをキャンセル
        success = await task_manager_instance.cancel_task(task_id)
        assert success
        
        # 少し待ってからステータスを確認
        await asyncio.sleep(0.1)
        
        task = task_manager_instance.get_task_status(task_id)
        assert task.status == TaskStatus.CANCELLED
    
    def test_get_nonexistent_task(self, task_manager_instance):
        """存在しないタスクの取得をテスト"""
        result = task_manager_instance.get_task_status("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_wait_for_nonexistent_task(self, task_manager_instance):
        """存在しないタスクの待機をテスト"""
        result = await task_manager_instance.wait_for_task("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, task_manager_instance):
        """存在しないタスクのキャンセルをテスト"""
        success = await task_manager_instance.cancel_task("nonexistent")
        assert not success
    
    def test_get_all_tasks(self, task_manager_instance):
        """全タスクの取得をテスト"""
        all_tasks = task_manager_instance.get_all_tasks()
        assert isinstance(all_tasks, dict)
        assert len(all_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_tasks(self, task_manager_instance):
        """古いタスクのクリーンアップをテスト"""
        # 古いタスクを手動で作成
        old_time = datetime.now() - timedelta(hours=25)
        old_task = BackgroundTask(
            id="old-task",
            name="old-task",
            status=TaskStatus.COMPLETED,
            created_at=old_time
        )
        task_manager_instance.tasks["old-task"] = old_task
        
        # 新しいタスクも作成
        new_task = BackgroundTask(
            id="new-task",
            name="new-task",
            status=TaskStatus.COMPLETED,
            created_at=datetime.now()
        )
        task_manager_instance.tasks["new-task"] = new_task
        
        # クリーンアップ実行
        await task_manager_instance.cleanup_old_tasks(max_age_hours=24)
        
        # 古いタスクが削除され、新しいタスクが残っていることを確認
        assert "old-task" not in task_manager_instance.tasks
        assert "new-task" in task_manager_instance.tasks
    
    @pytest.mark.asyncio
    async def test_submit_task_with_metadata(self, task_manager_instance):
        """メタデータ付きタスクの投入をテスト"""
        
        def simple_task():
            return "result"
        
        metadata = {"user_id": "123", "priority": "high"}
        task_id = await task_manager_instance.submit_task(
            simple_task,
            "metadata_task",
            metadata=metadata
        )
        
        task = task_manager_instance.get_task_status(task_id)
        assert task.metadata == metadata


class TestGlobalTaskManager:
    """グローバルタスクマネージャーのテスト"""
    
    def test_global_task_manager_exists(self):
        """グローバルタスクマネージャーの存在をテスト"""
        assert task_manager is not None
        assert isinstance(task_manager, BackgroundTaskManager)
        assert task_manager.max_concurrent == 3


@pytest.mark.asyncio
async def test_start_background_cleanup():
    """バックグラウンドクリーンアップの開始をテスト"""
    # モックを使ってテスト
    with pytest.raises(asyncio.CancelledError):
        cleanup_task = asyncio.create_task(start_background_cleanup())
        await asyncio.sleep(0.01)  # 短時間実行
        cleanup_task.cancel()
        await cleanup_task


class TestHeavyProcessingFunctions:
    """重い処理用関数のテスト"""
    
    @pytest.mark.asyncio
    async def test_process_heavy_rag_query(self):
        """重いRAGクエリ処理のテスト"""
        # モックを使ってテスト
        from unittest.mock import patch
        
        mock_result = {
            "answer": "test answer",
            "context": ["context1", "context2"],
            "score": 0.95
        }
        
        with patch('app.services.rag_service.RagService') as mock_rag_service:
            mock_instance = AsyncMock()
            mock_instance.process_query.return_value = mock_result
            mock_rag_service.return_value = mock_instance
            
            result = await process_heavy_rag_query("test question", top_k=10)
            assert result == mock_result
            
            mock_instance.process_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_precompute_popular_queries(self):
        """人気クエリの事前計算をテスト"""
        # モックを使ってテスト
        from unittest.mock import patch
        
        with patch('app.core.background_tasks.process_heavy_rag_query') as mock_process:
            mock_process.return_value = {"answer": "mock answer", "score": 0.9}
            
            # 実行（エラーが発生しないことを確認）
            await precompute_popular_queries()
            
            # 人気クエリの数だけ呼ばれていることを確認
            assert mock_process.call_count == 5
