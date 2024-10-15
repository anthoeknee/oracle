import asyncio
from src.core.bot import Bot
from src.core.config import Config

async def main():
    config = Config()
    bot = Bot()
    
    try:
        await bot.start(config.bot.token)
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Shutting down...")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot has been shut down.")
