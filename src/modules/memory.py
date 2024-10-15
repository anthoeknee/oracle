import asyncio
from typing import List
import redis.asyncio as redis
from src.core.config import Config
from src.utils.monitor import Monitor
from src.modules.base import BaseModule

class Memory(BaseModule):
    def __init__(self, bot):
        super().__init__(bot)
        self.config = Config()
        self.monitor = Monitor(__name__)
        self.redis = None
        self.max_history = getattr(self.config.memory, 'max_history', 100)

    async def setup(self):
        self.monitor.log_info("Setting up Memory module")
        if hasattr(self.config, 'redis') and hasattr(self.config.redis, 'url'):
            try:
                self.redis = await redis.from_url(self.config.redis.url)
                await self.redis.ping()
                self.monitor.log_info("Successfully connected to Redis")
            except redis.RedisError as e:
                self.monitor.log_error(e)
                self.redis = None
        else:
            self.monitor.log_warning("Redis configuration not found. Memory module will not be functional.")

    async def add_message(self, user_id: str, message: str):
        if not self.redis:
            self.monitor.log_warning("Redis is not connected. Cannot add message.")
            return
        try:
            key = f"user:{user_id}:messages"
            await self.redis.lpush(key, message)
            await self.redis.ltrim(key, 0, self.max_history - 1)
            self.monitor.log_info(f"Added message for user {user_id}")
        except redis.RedisError as e:
            self.monitor.log_error(e)

    async def get_history(self, user_id: str) -> List[str]:
        if not self.redis:
            self.monitor.log_warning("Redis is not connected. Cannot get history.")
            return []
        try:
            key = f"user:{user_id}:messages"
            messages = await self.redis.lrange(key, 0, -1)
            return [msg.decode('utf-8') for msg in reversed(messages)]
        except redis.RedisError as e:
            self.monitor.log_error(e)
            return []

    async def clear_history(self, user_id: str):
        if not self.redis:
            self.monitor.log_warning("Redis is not connected. Cannot clear history.")
            return
        try:
            key = f"user:{user_id}:messages"
            await self.redis.delete(key)
            self.monitor.log_info(f"Cleared history for user {user_id}")
        except redis.RedisError as e:
            self.monitor.log_error(e)

    async def cleanup(self):
        if self.redis:
            await self.redis.close()
            self.monitor.log_info("Closed Redis connection")

async def setup(bot):
    memory = Memory(bot)
    await memory.setup()
    await bot.add_cog(memory)
