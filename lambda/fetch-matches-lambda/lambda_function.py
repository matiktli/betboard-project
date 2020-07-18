import logging
import requests
import boto

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class SoccerApi():
    HEADERS = {'Content-Type': 'application/json'}

    API_BASE_URL = 'https://api.soccersapi.com/v2.2'
    PATH_FIXTURES = API_BASE_URL + '/fixtures/'

    def __init__(self, user, token):
        self.user = user
        self.token = token

    def __add_auth(self, params):
        params['user'] = self.user
        params['token'] = self.token

    def find_matches_by_leauge_id_and_date(self, leauge_id, date):
        params = {'leauge_id': leauge_id, 'd': date, 't': 'schedule'}
        self.__add_auth(params)
        response = requests.get(SoccerApi.PATH_FIXTURES,
                                params=params, headers=SoccerApi.HEADERS)
        return response.json()['data']

    def find_match_by_id(self, match_id):
        params = {'id': match_id, 't': 'info'}
        self.__add_auth(params)
        response = requests.get(SoccerApi.PATH_FIXTURES,
                                params=params, headers=SoccerApi.HEADERS)
        return response.json()['data']


def lambda_handler(event, context):
    LOGGER.info('The event arrives hoho: {}'.format(event))
    return True
