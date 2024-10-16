import discord
from discord.ext import commands
from src.modules.base import BaseModule
from src.clients.base import BaseAIClient
from src.core.config import config
from src.utils.monitor import Monitor
import redis.asyncio as redis
import json
import time
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader

class AIChatModule(BaseModule):
    def __init__(self, bot: commands.Bot, ai_client: BaseAIClient):
        super().__init__(bot)
        self.monitor = Monitor(__name__)
        self.ai_client = ai_client
        self.redis: Optional[redis.Redis] = None
        self.short_term_limit = config.memory.short_term_limit
        self.server_ttl = 600  # 10 minutes in seconds
        self.dm_ttl = 5400  # 1.5 hours in seconds
        self.jinja_env = Environment(loader=FileSystemLoader('data/templates'))

    async def setup(self):
        try:
            self.redis = await redis.from_url(config.redis.url)
            self.monitor.log_info(f"AIChatModule setup completed. Short-term limit: {self.short_term_limit}")
        except Exception as e:
            self.monitor.log_error(f"Error setting up Redis connection: {e}")
            raise

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)

        if isinstance(message.channel, discord.DMChannel) or \
           self.bot.user in message.mentions or \
           (message.reference and message.reference.resolved.author == self.bot.user):
            await self._process_chat(ctx, message.content)

    async def _process_chat(self, ctx: commands.Context, message: str):
        try:
            channel_id = self._get_channel_id(ctx)
            is_dm = isinstance(ctx.channel, discord.DMChannel)
            
            conversation_history = await self._get_conversation_history(channel_id, message)
            
            self.monitor.log_info(f"Sending chat request with history: {json.dumps(conversation_history, indent=2)}")
            
            response = await self.ai_client.chat(
                model=config.cohere.model,
                messages=conversation_history
            )
            
            self.monitor.log_info(f"Received response: {json.dumps(response, indent=2)}")

            await ctx.send(response["content"])

            await self._store_interaction(channel_id, message, response["content"], is_dm)
        except Exception as e:
            self.monitor.log_error(f"Error in _process_chat: {type(e).__name__}: {str(e)}")
            await self._handle_error(ctx, e)

    async def _get_conversation_history(self, channel_id: str, current_message: str) -> List[Dict]:
        recent_interactions = await self._get_recent_interactions(channel_id)
        
        # Load and render the system prompt template
        template = self.jinja_env.get_template('system_prompt.j2')
        system_prompt = template.render(config=config)
        
        conversation_history = [
            {"role": "System", "message": system_prompt}
        ]
        for interaction in recent_interactions:
            conversation_history.append({"role": "User", "message": interaction['content']})
            conversation_history.append({"role": "Chatbot", "message": interaction['response']})
        
        conversation_history.append({"role": "User", "message": current_message})
        return conversation_history

    async def _store_interaction(self, channel_id: str, user_message: str, ai_response: str, is_dm: bool):
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
            
            ttl = self.dm_ttl if is_dm else self.server_ttl
            await self.redis.expire(key, ttl)
            
            self.monitor.log_info(f"Stored interaction for channel {channel_id} with TTL {ttl} seconds")
        except Exception as e:
            self.monitor.log_error(f"Error storing interaction: {e}")

    async def _get_recent_interactions(self, channel_id: str) -> List[Dict]:
        try:
            key = f'channel:{channel_id}:interactions'
            interactions = await self.redis.lrange(key, 0, self.short_term_limit - 1)
            return [json.loads(interaction.decode('utf-8')) for interaction in interactions]
        except Exception as e:
            self.monitor.log_error(f"Error retrieving interactions: {e}")
            return []

    async def _handle_error(self, ctx: commands.Context, error: Exception):
        self.monitor.log_error(f"Error in chat command: {error}")
        error_message = "I apologize, but I encountered an error while processing your request."
        await ctx.send(error_message)

    def _get_channel_id(self, ctx: commands.Context) -> str:
        return f"dm_{ctx.author.id}" if isinstance(ctx.channel, discord.DMChannel) else str(ctx.channel.id)

async def setup(bot: commands.Bot):
    from src.clients.cohere import CohereAIClient
    
    ai_client = CohereAIClient()
    chat_module = AIChatModule(bot, ai_client)
    await chat_module.setup()
    await bot.add_cog(chat_module)
