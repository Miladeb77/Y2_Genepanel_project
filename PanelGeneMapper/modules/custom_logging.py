import logging
import os


def setup_logging(logs_dir="logs", info_log_file="info.log", error_log_file="error.log"):
    """
    Configure logging settings for centralized logging.

    Args:
        logs_dir (str): Directory to store the logs.
        info_log_file (str): Log file for INFO-level logs.
        error_log_file (str): Log file for ERROR-level logs.

    Logs:
        Info-level messages that logging has been set up.
    """
    try:
        # Define the logs directory path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        logs_path = os.path.join(base_dir, logs_dir)

        # Ensure the logs directory exists
        os.makedirs(logs_path, exist_ok=True)

        # Set log file paths
        info_log_path = os.path.join(logs_path, info_log_file)
        error_log_path = os.path.join(logs_path, error_log_file)

        # Get the root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicate logs
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # INFO handler
        info_handler = logging.FileHandler(info_log_path)
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(info_handler)

        # ERROR handler
        error_handler = logging.FileHandler(error_log_path)
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
