import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def init_logger(logdir='./logs', debug=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers:
        logger.removeHandler(handler)

    logdir = Path(logdir)
    logdir.mkdir(exist_ok=True)
    logfile = logdir / 'index.html'

    file_handler = TimedRotatingFileHandler(filename=str(logfile), when='D', interval=1, backupCount=14, delay=False)
    console_handler = logging.StreamHandler()

    file_log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s <br>'
    console_log_format = '%(asctime)s - %(message)s'
    file_formatter = logging.Formatter(file_log_format)
    console_formatter = logging.Formatter(console_log_format)
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    if not debug:
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

