from environs import Env

from .loggers import ColorFormatter

env = Env()
env.read_env()

LOGGING: dict = env.json('LOGGING', None) or {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            '()': ColorFormatter,
            'format': '%(levelname)s: %(name)s | [%(asctime)s.%(msecs)03d] | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'filters': {
        'belowError': {
            '()': 'core.loggers.BelowErrorFilter'
        },
        'escapeNewlines': {
            '()': 'core.loggers.EscapeNewlines'
        }
    },
    'handlers': {
        'stdout': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
            'filters': ['belowError', 'escapeNewlines']
        },
        'stderr': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': 'ext://sys.stderr',
            'filters': ['escapeNewlines'],
        }
    },
    'loggers': {
        'apps': {
            'handlers': ['stdout', 'stderr'],
            'level': 'DEBUG',
            'propagate': False
        },
        'core': {
            'handlers': ['stdout', 'stderr'],
            'level': 'DEBUG',
            'propagate': False
        },
        'main': {
            'handlers': ['stdout', 'stderr'],
            'level': 'DEBUG',
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['stdout', 'stderr'],
            'level': 'DEBUG',
            'propagate': False
        },
    },
    'root': {
        'handlers': ['stdout', 'stderr'],
        'level': 'WARNING',
    },
}

DATABASE_URL: str = env.str('DATABASE_URL', 'sqlite:///./devotion.db')
ENVIRONMENT = env.str('ENVIRONMENT', 'development')
SECRET_KEY = env.str("AUTH_SECRET_KEY", "devotion_secret_key")
ALGORITHM = env.str("AUTH_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = env.int("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", 24 * 60 * 60)
