import os
import logging
from datetime import datetime


def create_logger(root_directory, log_file_name):
    """
    Create logger under root_directory with timestamped run folder.

    Structure:
        root_directory/
            HHMMSS_DDMMYY_run/
                log_file_name
    """

    root_directory = os.path.normpath(root_directory)

    # Create root directory if not exists
    os.makedirs(root_directory, exist_ok=True)

    # Create run folder
    tmp_folder = datetime.now().strftime('%H%M%S_%d%m%y') + '_run'
    test_folder = os.path.join(root_directory, tmp_folder)
    os.makedirs(test_folder, exist_ok=True)

    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers (VERY important in automation runs)
    if logger.hasHandlers():
        logger.handlers.clear()

    logfile = os.path.join(test_folder, log_file_name)

    f_handler = logging.FileHandler(logfile, mode='w')
    f_handler.setLevel(logging.DEBUG)

    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    logger.addHandler(f_handler)

    return logger