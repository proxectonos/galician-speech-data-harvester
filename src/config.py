"""
Configuration settings for the scraping tools
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from scrapy.utils.log import configure_logging
from twisted.internet import asyncioreactor

asyncioreactor.install()

"-----------------PARTE GLOBAL CONFIGURABLE---------------------"
# Number of simultaneous downloads
WORKERS = 5

# Audio settings
AUDIO_SAMPLE_RATE = 16000  # 16 kHz
AUDIO_CHANNELS = 1  # Mono
AUDIO_FORMAT = "wav"

# Download settings
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
CHUNK_SIZE = 8192  # bytes for streaming downloads

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
LOGS_DIR = PROJECT_ROOT / "logs"

"---------------------------------------------------------------"

# Create directories if they don't exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging for scrapy
configure_logging(install_root_handler=False)
logging.getLogger("scrapy").propagate = False
logging.getLogger("scrapy").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
CONSOLE_LOG_FORMAT = "%(message)s"
# Create log filename with timestamp (including seconds)
LOG_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOGS_DIR / f"scraper_{LOG_TIMESTAMP}.log"


# User agent for web scraping (unified across all sources)
USER_AGENT = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0"
)

# Default headers for HTTP requests
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Referer": "https://www.google.com/",
}

# Source-specific settings
PARLAMENTO_CONFIG = {
    "base_url": "https://www.es.parlamentodegalicia.es/Buscador/Boletins",
    "search_url": "https://mediateca.parlamentodegalicia.gal/search",
    "session_types": {
        "pleno": "DSPG",  # Diario de Sesións do Parlamento de Galicia
        "comision": "CPG",  # Comisión
        "comision_np": "CPG_NP",  # Comisión non permanente
        "comision_enp": "CPG_ENP",  # Comisión especial non permanente
        "comision_pnl": "CPG_PNL",  # Comisión permanente non lexislativa
        "outros": "PG",  # Outros casos
    },
    "limit_date": datetime.strptime("2022-05-25", "%Y-%m-%d").date(),
    "headers": DEFAULT_HEADERS,
}

# YT-DLP settings
YTDLP_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": "%(title)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }
    ],
}


def setup_logging(name: str = "scraper", level: str = None) -> logging.Logger:
    """
    Set up logging configuration

    Args:
        name: Logger name
        level: Log level (defaults to LOG_LEVEL from config)

    Returns:
        Configured logger instance
    """
    level = level or LOG_LEVEL

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(CONSOLE_LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def setup_root_logging(level: str = None, console_handler=None) -> None:
    """
    Set up root logger configuration so all modules inherit handlers

    Args:
        level: Log level (defaults to LOG_LEVEL from config)
        console_handler: Optional custom console handler (e.g., for spinner support)
    """
    level = level or LOG_LEVEL

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # Console handler - use custom handler if provided, otherwise create default
    if console_handler is None:
        console_handler = logging.StreamHandler()

    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(CONSOLE_LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)


def get_headers() -> dict[str, str]:
    """
    Get default headers for web requests

    Returns:
        Dictionary of headers
    """
    return DEFAULT_HEADERS.copy()
