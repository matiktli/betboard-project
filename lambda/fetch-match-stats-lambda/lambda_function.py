import logging
import os
from betboard_shared import SoccerApi, Secrets, StoreSvc


""" 
    --- Actual Lambda Code --- 
"""
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
SECRETS = Secrets()

API = SoccerApi(SECRETS.get('SoccerApiSecrets', 'SOCCER_API_USERNAME'),
                SECRETS.get('SoccerApiSecrets', 'SOCCER_API_TOKEN'))
STORE = StoreSvc(os.getenv('ENV', 'prod'), logger=LOGGER)


def __get_match_id_from_record(record) -> int:
    return int(record['dynamodb']['Keys']['match_id']['N'])


def lambda_handler(event, context):
    LOGGER.info('Consuming: {}'.format(event))
    for record in event['Records']:
        match_id = __get_match_id_from_record(record)
        match_stats = API.find_match_stats_by_match_id(match_id)
        result = STORE.save_match_stats(match_stats)
    LOGGER.info('Finished consuming: {}'.format(event))
    return result
