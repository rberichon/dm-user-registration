import logging
import sys


def setup_logging() -> None:
    """Configure the root logger once with a consistent format.

    All loggers in the app inherit this configuration automatically.
    Uvicorn's built-in access log is silenced because the HTTP middleware
    produces its own access entries.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03dZ %(levelname)-8s %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
