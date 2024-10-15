import logging
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback
from rich.console import Console

# Install Rich traceback handling
install_rich_traceback()

class Logger:
    def __init__(self, name: str, log_file: str = 'data/logs/app.log'):
        """Initialize the logger with a specified name and log file."""
        # Create a Rich console for prettier output
        self.console = Console()

        # Configure logging with Rich handler
        logging.basicConfig(
            level="INFO",
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=self.console, rich_tracebacks=True)]
        )

        self.logger = logging.getLogger(name)

        # Add file handler for logging to file
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)

    def critical(self, message: str):
        """Log a critical message."""
        self.logger.critical(message)


class ErrorHandler:
    def __init__(self, logger: Logger):
        """Initialize the error handler with a logger instance."""
        self.logger = logger

    def handle_exception(self, exception: Exception):
        """Handle exceptions by logging them."""
        self.logger.error(f"An error occurred: {exception}")
        # Rich will automatically provide a pretty traceback


class Monitor:
    def __init__(self, name: str = 'Monitor'):
        """Initialize the monitor with a logger and error handler."""
        self.logger = Logger(name)
        self.error_handler = ErrorHandler(self.logger)

    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def log_error(self, exception: Exception):
        """Log an error message using the error handler."""
        self.error_handler.handle_exception(exception)

    # Additional monitoring methods can be added here
