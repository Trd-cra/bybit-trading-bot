import logging

def setup_logger(log_file, console_output=False):
    """Настраивает логгер с возможностью вывода в консоль."""
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)

    # Удаляем старые обработчики, если они есть (чтобы избежать дублирования)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Лог в файл
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Лог в консоль (если True)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    return logger
