import asyncio
from discord.ext import commands
import discord
from src.core.config import Config
from src.utils.module_loader import ModuleLoader
from src.utils.monitor import Monitor
import aiohttp

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        config = Config()
        super().__init__(
            command_prefix=config.bot.prefix,
            intents=intents
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
            self.monitor.log_error(e)

    async def on_ready(self):
        self.monitor.log_info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        self.monitor.log_info('------')

    async def on_error(self, event_method, *args, **kwargs):
        self.monitor.log_error(f"An error occurred in {event_method}")

    async def close(self):
        self.monitor.log_info("Closing bot and cleaning up...")
        if self.session and not self.session.closed:
            await self.session.close()
        for cog in self.cogs.values():
            if hasattr(cog, 'cleanup'):
                await cog.cleanup()
        await super().close()

async def main():
    bot = Bot()
    config = Config()
    try:
        await bot.start(config.bot.token)
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Shutting down...")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
