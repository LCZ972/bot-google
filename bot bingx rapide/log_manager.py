# log_manager.py
import datetime
import traceback
import logging

# === Configuration du logger === #
logger = logging.getLogger("BotLogger")
logger.setLevel(logging.DEBUG)  # Niveau global : DEBUG, INFO, WARNING, ERROR, CRITICAL

# Format des messages
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler : fichier
file_handler = logging.FileHandler("bot.log", encoding='utf-8')
file_handler.setFormatter(formatter)

# Handler : console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Évite les handlers en double
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# === Fonctions utilitaires === #
def log_info(message: str):
    logger.info(message)


def log_warning(message: str):
    logger.warning(message)


def log_error(message: str, error_obj: Exception = None):
    logger.error(message)
    if error_obj:
        logger.error("Traceback :\n" + traceback.format_exc())


def log_debug(message: str):
    logger.debug(message)


def log_critical(message: str):
    logger.critical(message)
