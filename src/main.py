import asyncio
import signal
from src.core.bot import Bot
from src.utils.monitor import Monitor

monitor = Monitor(__name__)

async def main():
    bot = Bot()
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(bot, loop)))
    
    try:
        await bot.start_bot()
    except asyncio.CancelledError:
        pass
    finally:
        await cleanup(bot)

async def shutdown(bot: Bot, loop: asyncio.AbstractEventLoop):
    monitor.log_info("Received signal to shut down. Cleaning up...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await cleanup(bot)
    loop.stop()

async def cleanup(bot: Bot):
    monitor.log_info("Performing cleanup...")
    if not bot.is_closed():
        await bot.close()
    # Add any other cleanup tasks here, e.g., closing database connections

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # The shutdown process is handled by the signal handler
