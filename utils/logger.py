import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

def setup_logger(log_dir: str = "data/output/logs", level: str = "INFO"):
    """Setup logging configuration"""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # File handler for all logs
    logger.add(
        log_path / f"seo_automation_{datetime.now().strftime('%Y%m%d')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Error file handler
    logger.add(
        log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="50 MB",
        retention="60 days"
    )
    
    logger.info("🪵 Logging setup complete")
    return logger

def get_logger(name: str = None):
    """Get logger instance"""
    if name:
        return logger.bind(name=name)
    return logger