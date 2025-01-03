from logging.handlers import RotatingFileHandler
import os
import logging

def setup_logging(logs_dir="logs", info_log_file="info.log", error_log_file="error.log", clear_logs=False):
    """
    Configure logging with optional clearing or rotating log files.

    Args:
        logs_dir (str): Directory to store the logs.
        info_log_file (str): Log file for INFO-level logs.
        error_log_file (str): Log file for ERROR-level logs.
        clear_logs (bool): Whether to clear logs on each execution.
    """
    try:
        # Define the logs directory path
        logs_path = os.path.abspath(logs_dir)
        os.makedirs(logs_path, exist_ok=True)

        # Set log file paths
        info_log_path = os.path.join(logs_path, info_log_file)
        error_log_path = os.path.join(logs_path, error_log_file)

        # Clear log files if specified
        if clear_logs:
            open(info_log_path, 'w').close()
            open(error_log_path, 'w').close()

        # Get the root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to prevent duplication
        while logger.handlers:
            logger.handlers.pop()

        # INFO handler with optional rotation
        info_handler = RotatingFileHandler(info_log_path, maxBytes=15 * 1024, backupCount=1)
        info_handler.setLevel(logging.INFO)
        info_handler.addFilter(lambda record: record.levelno <= logging.INFO)
        info_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(info_handler)

        # ERROR handler with optional rotation
        error_handler = RotatingFileHandler(error_log_path, maxBytes=15 * 1024, backupCount=1)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(error_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

        logging.info("Logging setup complete.")
        logging.info(f"Logs will be written to {logs_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to set up logging: {e}")
