# modules/base_module.py
from abc import abstractmethod
from discord.ext import commands

class BaseModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @abstractmethod
    async def setup(self):
        """Set up the module."""
        pass

async def setup(bot):
    # This is a base class, so we don't need to add it as a cog
    pass
