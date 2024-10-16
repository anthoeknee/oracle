import redis.asyncio as redis
from discord.ext import commands
from src.core.config import Config
from src.utils.monitor import Monitor
import json
import time
from typing import List, Dict, Optional
import asyncio

class ShortTermMemory:
    """Class for managing short-term conversation state using Redis."""

    def __init__(self, config: Config, monitor: Monitor):
        self.config = config
        self.monitor = monitor
        self.redis: Optional[redis.Redis] = None
        self.short_term_limit = self.config.memory.short_term_limit
        self.server_ttl = 600  # 10 minutes in seconds
        self.dm_ttl = 5400  # 1.5 hours in seconds

    async def setup(self):
        """Initialize the Redis connection."""
        try:
            self.redis = await redis.from_url(self.config.redis.url)
            self.monitor.log_info(f"ShortTermMemory Redis connection established successfully. Short-term limit: {self.short_term_limit}")
        except Exception as e:
            self.monitor.log_error(f"Error setting up Redis connection: {e}")
            raise

    async def store_interaction(self, channel_id: str, user_message: str, ai_response: str, is_dm: bool):
        """Store a new interaction in the short-term memory."""
        try:
            interaction = {
                'user': 'User',
                'content': user_message,
                'response': ai_response,
                'timestamp': time.time()
            }
            key = f'channel:{channel_id}:interactions'
            await self.redis.lpush(key, json.dumps(interaction))
            await self.redis.ltrim(key, 0, self.short_term_limit - 1)
            
            # Set TTL based on whether it's a DM or server channel
            ttl = self.dm_ttl if is_dm else self.server_ttl
            await self.redis.expire(key, ttl)
            
            self.monitor.log_info(f"Stored interaction for channel {channel_id} with TTL {ttl} seconds")
        except Exception as e:
            self.monitor.log_error(f"Error storing interaction: {e}")

    async def get_recent_interactions(self, channel_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Retrieve recent interactions from the short-term memory."""
        try:
            if limit is None:
                limit = self.short_term_limit
            key = f'channel:{channel_id}:interactions'
            interactions = await self.redis.lrange(key, 0, limit - 1)
            return [json.loads(interaction.decode('utf-8')) for interaction in interactions]
        except Exception as e:
            self.monitor.log_error(f"Error retrieving interactions: {e}")
            return []

    async def fetch_and_fill_buffer(self, channel_id: str, is_dm: bool):
        """Asynchronously fetch and fill the short-term buffer for a channel."""
        try:
            key = f'channel:{channel_id}:interactions'
            current_size = await self.redis.llen(key)

            if current_size < self.short_term_limit:
                # Fetch more interactions to fill the buffer
                # This is a placeholder - you would implement the actual fetching logic here
                new_interactions = await self._fetch_more_interactions(channel_id, self.short_term_limit - current_size)

                if new_interactions:
                    # Add new interactions to the buffer
                    for interaction in new_interactions:
                        await self.store_interaction(channel_id, interaction['content'], interaction['response'], is_dm)

            # Refresh TTL
            ttl = self.dm_ttl if is_dm else self.server_ttl
            await self.redis.expire(key, ttl)

            self.monitor.log_info(f"Fetched and filled buffer for channel {channel_id}")
        except Exception as e:
            self.monitor.log_error(f"Error fetching and filling buffer: {e}")

    async def _fetch_more_interactions(self, channel_id: str, count: int) -> List[Dict]:
        """Fetch more interactions from the channel history."""
        # This is a placeholder method. In a real implementation, you would:
        # 1. Use the Discord API to fetch recent messages from the channel
        # 2. Process these messages to create interaction objects
        # 3. Return a list of these interaction objects
        # For now, we'll return an empty list
        return []

async def setup(bot: commands.Bot):
    """Setup function to return the ShortTermMemory class."""
    config = bot.config
    monitor = Monitor(__name__)
    short_term_memory = ShortTermMemory(config, monitor)
    await short_term_memory.setup()
    return short_term_memory
