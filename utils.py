import logging
logger = logging.getLogger('axius.utils')

def safe_print(*a, **kw):
    logger.info(' '.join(map(str,a)))
