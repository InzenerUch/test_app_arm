# logger.py
import sys
import logging
import logging.handlers
from PyQt6.QtCore import qInstallMessageHandler, QtMsgType, QMessageLogContext

# Имя логгера
LOGGER_NAME = "KRD_Application"

def setup_logger(log_file_path: str = "app_errors.log"):
    """Настраивает логгер с записью в файл и консоль"""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)  # Перехватываем всё

    # Формат: Дата-Время | Уровень | Файл:Строка | Сообщение
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Файловый обработчик с ротацией (макс 5 МБ, хранит 3 архивных файла)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.ERROR)  # В файл пишем только ОШИБКИ и КРИТИЧЕСКИЕ сбои
    file_handler.setFormatter(formatter)

    # 2. Консольный обработчик (для разработки)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    ГЛОБАЛЬНЫЙ ПЕРЕХВАТЧИК: Ловит ЛЮБЫЕ необработанные исключения Python.
    Вам больше не нужен try...except в каждом методе для перехвата крашей!
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(LOGGER_NAME)
    # exc_info=True автоматически добавит полный стек-трейс (traceback) в лог
    logger.critical("НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ (CRASH)", exc_info=(exc_type, exc_value, exc_traceback))

def qt_message_handler(mode: QtMsgType, context: QMessageLogContext, message: str):
    """Перехватывает системные предупреждения и ошибки самого фреймворка PyQt6"""
    logger = logging.getLogger(LOGGER_NAME)
    file_info = f"({context.file}:{context.line})" if context.file else ""
    
    if mode == QtMsgType.QtDebugMsg:
        logger.debug(f"Qt Debug: {message} {file_info}")
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning(f"Qt Warning: {message} {file_info}")
    elif mode == QtMsgType.QtCriticalMsg:
        logger.critical(f"Qt Critical: {message} {file_info}")
    elif mode == QtMsgType.QtFatalMsg:
        logger.critical(f"Qt Fatal: {message} {file_info}")
    else:
        logger.info(f"Qt Info: {message} {file_info}")

def init_global_logging():
    """Инициализирует все глобальные перехватчики. Вызывать ОДИН РАЗ в main()"""
    logger = setup_logger("app_errors.log")
    
    # Подменяем стандартный обработчик исключений Python
    sys.excepthook = global_exception_handler
    
    # Подменяем обработчик сообщений Qt
    qInstallMessageHandler(qt_message_handler)
    
    logger.info("=" * 60)
    logger.info("Глобальная система логирования и перехвата ошибок инициализирована")
    logger.info("=" * 60)