import logging, colorlog, os, sys


class Logger(logging.Formatter):
    def get_logger(format, silent, loglevel):
        logger = logging.getLogger()

        if "debug" in loglevel:
            if format == "json":
                formatter = '{"time": "%(asctime)s", "origin": "p%(process)s %(filename)s:%(name)s:%(lineno)d", "level": "%(levelname)s", "log": "%(message)s"}'
            else:
                formatter = "[%(levelname)s] %(asctime)s p%(process)s %(filename)s:%(name)s:%(lineno)d %(message)s"
        else:
            if format == "json":
                formatter = '{"time": "%(asctime)s", "level": "%(levelname)s", "log": "%(message)s"}'
            else:
                formatter = "[%(levelname)s] %(message)s"

        if "debug" in loglevel:
            logger.setLevel(logging.DEBUG)
        elif loglevel in ["warning", "warn"]:
            logger.setLevel(logging.WARNING)
        else:
            logger.setLevel(logging.INFO)

        if "colorlog" in sys.modules and os.isatty(2):
            cformat = "%(log_color)s" + formatter
            f = colorlog.ColoredFormatter(
                cformat,
                datefmt=None,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "reset",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        console_handler = logging.StreamHandler()

        console_handler.setFormatter(f)
        logger.addHandler(console_handler)

        return logger
