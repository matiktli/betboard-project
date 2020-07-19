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


def lambda_handler(event, context):
    LOGGER.info('Consuming: {}'.format(event))
    for job in event['data']['jobs']:
        LOGGER.info('Executing job: {}'.format(job))
        found_matches = API.find_matches_by_league_id_and_date(
            job['params']['league_id'],
            job['params']['date']
        )
        result = STORE.save_matches(found_matches)
        job['status'] = 'done' if result else 'failed'
        LOGGER.info('Job [{}]: {}'.format(job['status'], job))
    LOGGER.info('Finished consuming: {}'.format(event))
    return True
