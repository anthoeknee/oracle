import asyncio
from discord.ext import commands
import discord
from src.core.config import Config
from src.utils.module_loader import ModuleLoader
from src.utils.monitor import Monitor
import aiohttp

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.dm_reactions = True
        intents.dm_typing = True
        intents.guild_messages = True
        intents.guild_reactions = True
        intents.guild_typing = True
        self.config = Config()
        super().__init__(
            command_prefix=commands.when_mentioned_or(self.config.bot.prefix),
            intents=intents,
            dm_permission=True
        )
        self.monitor = Monitor(__name__)
        self.module_loader = ModuleLoader(self, 'src/modules')
        self.session = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        try:
            await self.module_loader.load_modules()
            self.monitor.log_info("Modules loaded successfully")
        except Exception as e:
            self.monitor.log_error(f"Error during setup: {e}")

    async def on_ready(self):
        self.monitor.log_info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        self.monitor.log_info('------')

    async def on_error(self, event_method, *args, **kwargs):
        self.monitor.log_error(f"An error occurred in {event_method}")

    async def close(self):
        self.monitor.log_info("Closing bot and cleaning up...")
        if not self.is_closed():
            if self.session:
                await self.session.close()
            await super().close()
        # Add any other cleanup tasks specific to your bot here

    async def start_bot(self):
        try:
            await self.start(self.config.bot.token)
        except KeyboardInterrupt:
            self.monitor.log_info("Received keyboard interrupt. Shutting down...")
        except asyncio.CancelledError:
            self.monitor.log_info("Bot start cancelled. Shutting down...")
        finally:
            await self.close()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # Silently ignore CommandNotFound errors
            return
        # For other types of errors, you might want to log them
        self.monitor.log_error(f"An error occurred: {error}")

async def main():
    bot = Bot()
    config = Config()
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Shutting down...")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
