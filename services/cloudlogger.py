import json
import logging
import logging.config
import logging.handlers
import pathlib

# import google.cloud.logging


def get_logger(name):
    # log_client = google.cloud.logging.Client()
    # log_handler = log_client.get_default_handler()

    config_file = pathlib.Path("services/logging_config.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)
    logger = logging.getLogger(name)

    return logger


# CloudLogger.initiate_logger()
