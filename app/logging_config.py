import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_dir: str = 'logs', level: int = logging.INFO):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger('svn_ai_review')
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'
    ))
    logger.addHandler(console)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        str(Path(log_dir) / 'app.log'),
        when='midnight',
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    ))
    logger.addHandler(file_handler)

    return logger
