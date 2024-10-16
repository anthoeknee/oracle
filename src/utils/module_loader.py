import os
import importlib
import importlib.util
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
        """Load all modules in the specified directory."""
        module_order = ['ai.short_term', 'ai.chat']  # Specify the order of modules to load
        for module_name in module_order:
            await self.load_file_module(module_name)

        # Load remaining modules
        for module_file in os.listdir(self.module_dir):
            if module_file.endswith('.py') and not module_file.startswith('__'):
                module_name = module_file[:-3]
                if module_name not in [m.split('.')[-1] for m in module_order]:
                    await self.load_file_module(module_name)

    async def load_folder_module(self, folder_name: str):
        """Load a module from a folder."""
        try:
            module = importlib.import_module(f'src.modules.{folder_name}')
            if hasattr(module, 'setup'):
                setup_func = getattr(module, 'setup')
                if asyncio.iscoroutinefunction(setup_func):
                    await setup_func(self.bot)
                else:
                    setup_func(self.bot)
                self.monitor.log_info(f"Loaded folder module: {folder_name}")
            else:
                self.monitor.log_warning(f"Folder module {folder_name} has no setup function, skipping")
        except ImportError as e:
            self.monitor.log_error(f"Failed to import folder module {folder_name}: {str(e)}")
        except Exception as e:
            self.monitor.log_error(f"Failed to load folder module {folder_name}: {str(e)}")

    async def load_file_module(self, module_name: str):
        """Load a module from a file."""
        try:
            module = importlib.import_module(f'src.modules.{module_name}')
            setup_func = getattr(module, 'setup', None)
            if setup_func:
                if asyncio.iscoroutinefunction(setup_func):
                    await setup_func(self.bot)
                else:
                    setup_func(self.bot)
                self.monitor.log_info(f"Loaded file module: {module_name}")
            else:
                self.monitor.log_warning(f"File module {module_name} has no setup function, skipping")
        except Exception as e:
            self.monitor.log_error(f"Failed to load file module {module_name}: {str(e)}")

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
