import logging


def init_logger(logfile, debug=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(logfile)
    console_handler = logging.StreamHandler()

    file_log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

