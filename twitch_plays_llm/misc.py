from loguru import logger


def log_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception calling {func.__name__}: {str(e)}")
            raise
    return wrapper
