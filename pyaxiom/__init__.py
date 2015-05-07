__version__ = "0.0.9"

# Package level logger
import logging
try:
    # Python >= 2.7
    from logging import NullHandler
except ImportError:
    # Python < 2.7
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
logger = logging.getLogger("pyaxiom")
logger.addHandler(logging.NullHandler())
