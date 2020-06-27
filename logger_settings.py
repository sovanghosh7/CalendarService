LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(process)d %(asctime)s %(module)s File name: [%(filename)s] Function name: [%(funcName)s] Line No: [%(lineno)d] %(message)s",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "default.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 4,
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        '': {
            'level': 'WARNING',
            'handlers': ['default', 'console'],
        },
    },
}
