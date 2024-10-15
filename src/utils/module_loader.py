import os
import importlib
import inspect
import logging
import asyncio
from discord.ext import commands
from src.modules.base import BaseModule
from typing import List, Any
from src.utils.monitor import Monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModuleLoader(commands.Cog):
    """Cog for dynamically loading modules."""

    def __init__(self, bot: commands.Bot, module_dir: str):
        self.bot = bot
        self.module_dir = module_dir
        self.monitor = Monitor(__name__)

    async def load_modules(self):
        """Dynamically load all modules from the specified directory."""
        for module_name in os.listdir(self.module_dir):
            if module_name.endswith('.py') and not module_name.startswith('__'):
                try:
                    module = importlib.import_module(f'src.modules.{module_name[:-3]}')
                    setup_func = getattr(module, 'setup', None)
                    if setup_func and asyncio.iscoroutinefunction(setup_func):
                        await setup_func(self.bot)
                    elif setup_func:
                        setup_func(self.bot)
                    else:
                        self.monitor.log_warning(f"Module {module_name} has no setup function, skipping")
                    self.monitor.log_info(f"Loaded module: {module_name}")
                except Exception as e:
                    self.monitor.log_error(f"Failed to load module {module_name}: {str(e)}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Event listener for when the bot is ready."""
        for module in self.bot.cogs.values():
            if isinstance(module, BaseModule) and hasattr(module, 'setup'):
                await module.setup()
                self.monitor.log_info(f"Set up module: {module.__class__.__name__}")

# Example usage
def setup(bot: commands.Bot):
    """Load the ModuleLoader cog."""
    module_loader = ModuleLoader(bot, 'src/modules')
    bot.add_cog(module_loader)
