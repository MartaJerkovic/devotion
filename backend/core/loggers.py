import sys
import logging

class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    NAME_COLOR = '\033[94m'  # Blue
    RESET = '\033[0m'

    def format(self, record):
        if sys.stderr.isatty():
            # Color the level
            level_color = self.LEVEL_COLORS.get(record.levelname, '')

            record.levelname = f"{level_color}{record.levelname}{self.RESET}"

            record.name = f"{self.NAME_COLOR}{record.name}{self.RESET}"

        return super().format(record)

class BelowErrorFilter(logging.Filter):
    def filter(self, rec: logging.LogRecord) -> bool:
        return rec.levelno < logging.ERROR

class EscapeNewlines(logging.Filter):
    def filter(self, rec: logging.LogRecord) -> bool:
        rec.msg = str(rec.msg).replace('\n', '\\n').replace('\r', '\\r')
        return True