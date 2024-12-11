import logging

def setup_logging():
    """
    Configure logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("retrieve_data.log"),
            logging.StreamHandler()
        ]
    )
