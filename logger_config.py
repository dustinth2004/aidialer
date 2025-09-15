import sys

from loguru import logger

# Remove the default handler
logger.remove()

# Add a new handler with INFO level
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO",  
    colorize=True
)

def get_logger(name):
    """
    Returns a logger instance with the specified name.

    Args:
        name (str): The name to bind to the logger.

    Returns:
        loguru.Logger: A logger instance with the given name.
    """
    return logger.bind(name=name)