import discord
from discord.ext import commands
from .chat import setup as setup_chat

async def setup(bot: commands.Bot):
    await setup_chat(bot)
