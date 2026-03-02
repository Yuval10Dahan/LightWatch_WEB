import os
import logging
from datetime import datetime


import os
import logging
from datetime import datetime


def create_logger(root_directory, log_file_name, directory_name=None):
    """
    Create logger under root_directory.

    If directory_name is provided:
        root_directory/directory_name/<timestamp>_run/

    Otherwise:
        root_directory/<timestamp>_run/
    """

    root_directory = os.path.normpath(root_directory)

    # Decide parent directory
    if directory_name:
        directory_name = os.path.normpath(directory_name)
        parent_directory = os.path.join(root_directory, directory_name)
    else:
        parent_directory = root_directory

    # Create parent directory safely
    os.makedirs(parent_directory, exist_ok=True)

    # Create timestamp run folder
    tmp_folder = datetime.now().strftime('%H%M%S_%d%m%y') + '_run'
    test_folder = os.path.join(parent_directory, tmp_folder)
    os.makedirs(test_folder, exist_ok=True)

    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicated handlers between runs
    if logger.hasHandlers():
        logger.handlers.clear()

    logfile = os.path.join(test_folder, log_file_name)

    f_handler = logging.FileHandler(logfile, mode='w')
    f_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    f_handler.setFormatter(formatter)

    logger.addHandler(f_handler)

    return logger