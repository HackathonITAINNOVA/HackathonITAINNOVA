from .main import process_all_docs, periodic_task, solr, twitter, facebook

import logging
from logging.handlers import RotatingFileHandler

import os
import os.path

if not os.path.exists("logs/"):
    os.makedirs("logs/")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# BASIC_FORMAT = '%(asctime)s - %(levelname)-8s %(name)-20s > %(message)s'
BASIC_FORMAT = '%(asctime)s - %(levelname)-8s %(threadName)-10s > %(message)s    (%(name)s.%(funcName)s:%(lineno)d)'
console_formatter = logging.Formatter(BASIC_FORMAT, '%H:%M:%S')
file_formatter = logging.Formatter(BASIC_FORMAT)

console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(console_formatter)
logger.addHandler(console_log)

debug_file_log = RotatingFileHandler('logs/debug.log', encoding="utf-8", maxBytes=10000000, backupCount=10)
debug_file_log.setLevel(logging.DEBUG)
debug_file_log.setFormatter(file_formatter)
logger.addHandler(debug_file_log)

info_file_log = RotatingFileHandler('logs/info.log', encoding="utf-8", maxBytes=1000000, backupCount=10)
info_file_log.setLevel(logging.INFO)
info_file_log.setFormatter(file_formatter)
logger.addHandler(info_file_log)

error_file_log = RotatingFileHandler('logs/error.log', encoding="utf-8", maxBytes=1000000, backupCount=10)
error_file_log.setLevel(logging.WARNING)
error_file_log.setFormatter(file_formatter)
logger.addHandler(error_file_log)
