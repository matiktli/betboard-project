import logging
import requests
import boto3

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

    def find_matches_by_league_id_and_date(self, league_id, date):
        params = {'country_id': league_id, 'd': date, 't': 'schedule'}
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


class StoreSvc():

    MATCH_TABLE = 'match'

    def __init__(self, env):
        self.env = env
        self.dynamo = boto3.resource('dynamodb')

    def __prefix_table(self, table_name):
        return self.env + '-' + table_name

    def save_match(self, match):
        table = self.dynamo.Table(self.__prefix_table(StoreSvc.MATCH_TABLE))
        return table.put_item(Item=match)


class Transformer():

    def matchToDb(self, match_dto):
        return {
            'match_id': int(match_dto['id']),
            'team_one_id': int(match_dto['teams']['home']['id']),
            'team_two_id': int(match_dto['teams']['away']['id']),
            'date': match_dto['time']['date'],
            'leauge_id': int(match_dto['league']['id']),
            'country_id': int(match_dto['league']['country_id'])
        }


def lambda_handler(event, context):
    LOGGER.info('The event arrives hoho: {}'.format(event))
    return True
