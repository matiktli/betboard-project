import logging
import requests
import boto3
import botocore
import os
import json
import time


class Transformer():

    def matchesToDbs(self, matches_dtos):
        result = []
        for match_dto in matches_dtos:
            result.append(self.matchToDb(match_dto))
        return result

    def matchToDb(self, match_dto):
        return {
            'match_id': int(match_dto['id']),
            'team_one_id': int(match_dto['teams']['home']['id']),
            'team_two_id': int(match_dto['teams']['away']['id']),
            'date': match_dto['time']['date'],
            'leauge_id': int(match_dto['league']['id']),
            'country_id': int(match_dto['league']['country_id']),
            'json': match_dto
        }


class SoccerApi():
    HEADERS = {'Content-Type': 'application/json'}

    API_BASE_URL = 'https://api.soccersapi.com/v2.2'
    PATH_FIXTURES = API_BASE_URL + '/fixtures/'

    DENMARK, SUPERLIGAEN = 37, 1609
    AUSTRALIA, ALEAGUE = 14, 974

    def __init__(self, user, token, transformer=Transformer()):
        self.user = user
        self.token = token
        self.t = transformer

    def __add_auth(self, params):
        params['user'] = self.user
        params['token'] = self.token

    def __check_response_valid(self, response):
        response.raise_for_status()
        if int(response.json()['meta']['count']) == 0:
            return False
        return True

    def find_matches_by_league_id_and_date(self, league_id, date):
        params = {'league_id': league_id, 'd': date, 't': 'schedule'}
        self.__add_auth(params)
        response = requests.get(SoccerApi.PATH_FIXTURES,
                                params=params, headers=SoccerApi.HEADERS)
        if not self.__check_response_valid(response):
            return []
        return self.t.matchesToDbs(response.json()['data'])

    def find_match_by_id(self, match_id):
        params = {'id': match_id, 't': 'info'}
        self.__add_auth(params)
        response = requests.get(SoccerApi.PATH_FIXTURES,
                                params=params, headers=SoccerApi.HEADERS)
        if not self.__check_response_valid(response):
            return None
        return self.t.matchToDb(response.json()['data'])


class StoreSvc():

    MATCH_TABLE = 'match'

    def __init__(self, env):
        self.env = env
        self.dynamo = boto3.resource('dynamodb')

    def __prefix_table(self, table_name):
        return self.env + '-' + table_name

    def save_match_if_not_exists(self, match):
        table = self.dynamo.Table(self.__prefix_table(StoreSvc.MATCH_TABLE))
        try:
            table.put_item(
                Item=match,
                ConditionExpression='attribute_not_exists(match_id)'
            )
        except botocore.exceptions.ClientError as ex:
            if ex.response['Error']['Code'] != 'ConditionalCheckFailedException':
                raise
            else:
                LOGGER.info("Match with id: {} already exists in db, skipping.".format(
                    match['match_id']))
        return True

    def save_matches(self, matches) -> bool:
        table = self.dynamo.Table(self.__prefix_table(StoreSvc.MATCH_TABLE))
        with table.batch_writer() as batch:
            for match in matches:
                batch.put_item(Item=match)
        return True


""" 
    --- Actual Lambda Code --- 
"""
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
SECRETS = json.loads(boto3.client('secretsmanager').get_secret_value(
    SecretId='SoccerApiSecrets')['SecretString'])
API = SoccerApi(SECRETS['SOCCER_API_USERNAME'],
                SECRETS['SOCCER_API_TOKEN'])
STORE = StoreSvc(os.getenv('ENV', 'prod'))


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
