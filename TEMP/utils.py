import logging
import os

def setup_logger(log_file, console_output=False, max_size_mb=1):
    """Универсальный логгер с ограничением размера."""
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.INFO)

    # Очистка обработчиков (чтобы не дублировалось при повторном запуске)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Проверка и ограничение размера файла
    if os.path.exists(log_file) and os.path.getsize(log_file) > max_size_mb * 1024 * 1024:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Сохраняем последние ~500 строк
        with open(log_file, "w", encoding="utf-8") as f:
            f.writelines(lines[-500:])

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
