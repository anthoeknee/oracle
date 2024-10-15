import discord
from discord.ext import commands
from src.core.config import Config
from src.modules.memory import Memory
from src.clients.cohere import CohereAIClient
from src.utils.monitor import Monitor
from src.modules.base import BaseModule

class ChatBot(BaseModule, commands.Cog):
    def __init__(self, bot: commands.Bot):
        BaseModule.__init__(self, bot)
        commands.Cog.__init__(self)
        self.config = Config()
        self.monitor = Monitor(__name__)
        self.memory = None
        self.ai_client = CohereAIClient()

    async def setup(self):
        self.monitor.log_info("Setting up ChatBot module")
        self.memory = self.bot.get_cog('Memory')
        if not self.memory:
            self.memory = Memory(self.bot)
            await self.memory.setup()
            await self.bot.add_cog(self.memory)
        self.monitor.log_info("ChatBot module set up complete")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        should_respond = (
            isinstance(message.channel, discord.DMChannel) or
            self.bot.user in message.mentions or
            message.reference and message.reference.resolved.author == self.bot.user
        )

        if should_respond:
            await self.process_message(message)

    async def process_message(self, message: discord.Message):
        user_id = str(message.author.id)
        
        try:
            await self.memory.add_message(user_id, f"User: {message.content}")
            history = await self.memory.get_history(user_id)
            prompt = "\n".join(history + ["AI:"])

            response = await self.ai_client.generate_response(prompt)
            await self.memory.add_message(user_id, f"AI: {response}")

            await message.channel.send(response)
            self.monitor.log_info(f"Sent response to user {user_id}")
        except Exception as e:
            self.monitor.log_error(f"Error processing message: {e}")
            await message.channel.send("I'm sorry, I encountered an error while processing your request.")

async def setup(bot: commands.Bot):
    chat_bot = ChatBot(bot)
    await chat_bot.setup()
    await bot.add_cog(chat_bot)
