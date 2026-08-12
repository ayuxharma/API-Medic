import logging
import os

# only these log levels can be configured through the enviornment
LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL_ERROR": logging.CRITICAL,
}


def configure_logging() -> None:
    """
    Configure application-wide logging.

    LOG_LEVEL can be changed in .env without changing code.
    Invalid values safely fall back to INFO.
    """

    level_name = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    log_level = LOG_LEVELS.get(
        level_name,
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s level=%(levelname)s logger=%(name)s %(message)s"),
    )
