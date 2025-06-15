"""
Database connection pool and management for production environment.
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration."""
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    idle_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0

class UpstashVectorPool:
    """Upstash Vector connection pool manager."""
    
    def __init__(self, config: Optional[ConnectionPoolConfig] = None):
        self.config = config or ConnectionPoolConfig()
        self.url = os.getenv("UPSTASH_VECTOR_REST_URL")
        self.token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        self.pool: Dict[str, Dict[str, Any]] = {}
        self.pool_lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_connections)
        self._initialized = False
        
        if not self.url or not self.token:
            logger.warning("Upstash Vector credentials not found")
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        async with self.pool_lock:
            if self._initialized:
                return
            
            logger.info("Initializing Upstash Vector connection pool")
            
            # Create initial connections
            for i in range(self.config.min_connections):
                connection_id = f"conn_{i}"
                connection = await self._create_connection(connection_id)
                if connection:
                    self.pool[connection_id] = connection
            
            self._initialized = True
            logger.info(f"Initialized {len(self.pool)} connections in Upstash Vector pool")
    
    async def _create_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Create a new connection to Upstash Vector."""
        try:
            # Import upstash_vector here to handle import errors gracefully
            try:
                from upstash_vector import Index
            except ImportError:
                logger.error("upstash_vector not available")
                return None
            
            if not self.url or not self.token:
                logger.error("Upstash Vector credentials not configured")
                return None
            
            index = Index(url=self.url, token=self.token)
            
            # Test the connection
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: index.info()
            )
            
            connection = {
                "id": connection_id,
                "index": index,
                "created_at": time.time(),
                "last_used": time.time(),
                "in_use": False,
                "error_count": 0
            }
            
            logger.debug(f"Created Upstash Vector connection: {connection_id}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create Upstash Vector connection {connection_id}: {e}")
            return None
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Any, None]:
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()
        
        connection = None
        connection_id = None
        
        try:
            # Get available connection
            async with self.pool_lock:
                for conn_id, conn in self.pool.items():
                    if not conn["in_use"]:
                        conn["in_use"] = True
                        conn["last_used"] = time.time()
                        connection = conn
                        connection_id = conn_id
                        break
                
                # If no available connection and pool not at max, create new one
                if not connection and len(self.pool) < self.config.max_connections:
                    new_conn_id = f"conn_{len(self.pool)}"
                    new_connection = await self._create_connection(new_conn_id)
                    if new_connection:
                        new_connection["in_use"] = True
                        self.pool[new_conn_id] = new_connection
                        connection = new_connection
                        connection_id = new_conn_id
            
            if not connection:
                raise Exception("No available connections in pool")
            
            yield connection["index"]
            
        except Exception as e:
            logger.error(f"Error using connection {connection_id}: {e}")
            # Mark connection as having an error
            if connection:
                connection["error_count"] += 1
                # Remove connection if too many errors
                if connection["error_count"] > self.config.retry_attempts:
                    async with self.pool_lock:
                        if connection_id in self.pool:
                            del self.pool[connection_id]
                            logger.warning(f"Removed faulty connection {connection_id}")
            raise
        finally:
            # Release connection
            if connection and connection_id:
                async with self.pool_lock:
                    if connection_id in self.pool:
                        self.pool[connection_id]["in_use"] = False
    
    async def cleanup_idle_connections(self) -> None:
        """Clean up idle connections."""
        current_time = time.time()
        idle_threshold = current_time - self.config.idle_timeout
        
        async with self.pool_lock:
            connections_to_remove = []
            
            for conn_id, connection in self.pool.items():
                if (not connection["in_use"] and 
                    connection["last_used"] < idle_threshold and 
                    len(self.pool) > self.config.min_connections):
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                del self.pool[conn_id]
                logger.debug(f"Removed idle connection {conn_id}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all connections."""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        healthy_connections = 0
        total_connections = len(self.pool)
        
        async with self.pool_lock:
            for connection in self.pool.values():
                try:
                    if not connection["in_use"]:
                        # Quick health check
                        await asyncio.get_event_loop().run_in_executor(
                            self.executor,
                            lambda: connection["index"].info()
                        )
                        healthy_connections += 1
                except Exception as e:
                    logger.warning(f"Health check failed for connection {connection['id']}: {e}")
        
        return {
            "status": "healthy" if healthy_connections > 0 else "unhealthy",
            "total_connections": total_connections,
            "healthy_connections": healthy_connections,
            "pool_utilization": f"{(total_connections / self.config.max_connections) * 100:.1f}%"
        }
    
    async def close(self) -> None:
        """Close all connections in the pool."""
        async with self.pool_lock:
            logger.info(f"Closing {len(self.pool)} connections")
            self.pool.clear()
        
        self.executor.shutdown(wait=True)
        self._initialized = False

class DatabaseManager:
    """Centralized database connection manager."""
    
    def __init__(self) -> None:
        self.upstash_pool = UpstashVectorPool()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize all database connections."""
        await self.upstash_pool.initialize()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("Database manager initialized")
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.upstash_pool.cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    @asynccontextmanager
    async def get_vector_connection(self) -> AsyncGenerator[Any, None]:
        """Get Upstash Vector connection."""
        async with self.upstash_pool.get_connection() as connection:
            yield connection
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all database connections."""
        health_data = {
            "timestamp": time.time(),
            "upstash_vector": await self.upstash_pool.health_check()
        }
        
        return health_data
    
    async def close(self) -> None:
        """Close all database connections."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.upstash_pool.close()
        logger.info("Database manager closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
async def get_vector_db() -> AsyncGenerator[Any, None]:
    """Get vector database connection."""
    async with db_manager.get_vector_connection() as connection:
        yield connection

async def initialize_database() -> None:
    """Initialize database connections."""
    await db_manager.initialize()

async def close_database() -> None:
    """Close database connections."""
    await db_manager.close()

async def database_health_check() -> Dict[str, Any]:
    """Get database health status."""
    return await db_manager.health_check()
