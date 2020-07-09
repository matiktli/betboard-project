import logging

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def lambda_handler(event, context):
    LOGGER.info('The event arrives hoho: {}'.format(event))
    return True
