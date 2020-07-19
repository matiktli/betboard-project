import json
import requests
import boto3
import botocore

"""
This file is currently copied among lambdas,
it will be moved to lambda-layers etc at some point
"""


class Secrets():

    def __init__(self):
        self.secret_manager = boto3.client('secretsmanager')

    def get(self, secret_id, secret_key):
        secret = self.secret_manager.get_secret_value(SecretId=secret_id)
        return json.loads(secret['SecretString'])[secret_key]


class Transformer():

    def matchesToDbs(self, matches_dtos):
        result = []
        for match_dto in matches_dtos:
            result.append(self.matchToDb(match_dto))
        return result

    def matchStatToListOfDbs(self, match_stat_dto, match_id):
        def create_stat(match_id, stat_type, team_id, value):
            return {
                'match_id': int(match_id),
                'stat_type__team_id': stat_type + '__' + team_id,
                'value': value
            }

        result = []
        for team_stat in match_stat_dto:
            team_id = team_stat['team_id']
            for stat_key in team_stat:
                if stat_key in ['team_id']:
                    continue
                elif stat_key == 'passes':
                    result.append(create_stat(
                        match_id, 'passes_total', team_id, team_stat['passes']['total']))
                    result.append(create_stat(
                        match_id, 'passes_accurate', team_id, team_stat['passes']['accurate']))
                    result.append(create_stat(
                        match_id, 'passes_percentage', team_id, team_stat['passes']['percentage']))
                elif 'cards' in stat_key:
                    card_key = 'cards_' + stat_key.replace('cards', '')
                    result.append(create_stat(
                        match_id, card_key, team_id, team_stat[stat_key]))
                else:
                    result.append(create_stat(
                        match_id, stat_key, team_id, team_stat[stat_key]))
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
    PATH_STATS = API_BASE_URL + '/stats/'

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
        if 'meta' in response.json() and 'count' in response.json()['meta'] and int(response.json()['meta']['count']) == 0:
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

    def find_match_stats_by_match_id(self, match_id) -> []:
        params = {'id': match_id, 't': 'match'}
        self.__add_auth(params)
        response = requests.get(SoccerApi.PATH_STATS,
                                params=params, headers=SoccerApi.HEADERS)
        if not self.__check_response_valid(response):
            return None
        return self.t.matchStatToListOfDbs(response.json()['data'], match_id)


class StoreSvc():

    MATCH_TABLE = 'match'
    MATCH_STATS_TABLE = 'match-stats'

    def __init__(self, env, logger):
        self.env = env
        self.log = logger
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
                self.log.info("Match with id: {} already exists in db, skipping.".format(
                    match['match_id']))
        return True

    def save_matches(self, matches) -> bool:
        table = self.dynamo.Table(self.__prefix_table(StoreSvc.MATCH_TABLE))
        with table.batch_writer() as batch:
            for match in matches:
                batch.put_item(Item=match)
        return True

    def save_match_stats(self, match_stats_list: []):
        table = self.dynamo.Table(
            self.__prefix_table(StoreSvc.MATCH_STATS_TABLE))
        with table.batch_writer() as batch:
            for match_stat in match_stats_list:
                batch.put_item(Item=match_stat)
        return True
