import dateutil.rrule as rrule
import datetime
from selenium import webdriver
import selenium
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.spiders import Rule
from scrapy.selector import Selector
import csv
import re
from multiprocessing import Process, Queue
from twisted.internet import reactor
import os
import time
from scrapy_selenium import SeleniumRequest
from itertools import islice
import dateutil.relativedelta as relativedelta


class ObtainMatchLineupsSpider():
    name = 'match_lineups_spider'
    allowed_domains = ['football-lineups.com']

    def __init__(self, urls):
        self.urls = urls
        self.driver = webdriver.Firefox()

    def __del__(self):
        self.driver.close()

    def __extract_sub_player_data(self, sub_player_row):
        sub_player_no = sub_player_row.find_element_by_xpath(
            './/div/span[2]/span').get_attribute("textContent")
        sub_player_name = sub_player_row.find_element_by_xpath(
            './/div[1]/span[3]/a').get_attribute("textContent").replace('\t', '').replace('\n', '')
        return [sub_player_name, sub_player_no, None]

    def __add_sub_players_left(self, sub_players, sub_players_elements):
        # Not efficient but there will be no more than 5 there or 7 so whatever
        def _is_sub_already_defined(sub_players, sub_name, sub_no):
            for sub_data in sub_players:
                if sub_data[0] == sub_name and sub_data[1] == sub_no:
                    return True
            return False

        for sub_player_row in sub_players_elements.find_elements_by_xpath('.//tr/td/div'):
            sub_player_result = self.__extract_sub_player_data(sub_player_row)

            if not _is_sub_already_defined(sub_players, sub_player_result[0], sub_player_result[1]):
                sub_players.append(sub_player_result)
        return sub_players

    def __extract_master_stats(self, player_row):
        player_master_stat_name = player_row.find_element_by_xpath(
            './/div[2]/div/div[1]/span[1]').get_attribute("textContent")
        player_master_stat_val = player_row.find_element_by_xpath(
            './/div[2]/div/div[1]/span[2]').get_attribute("textContent")

        if player_master_stat_name == 'Saves':
            return (0, player_master_stat_val)
        elif player_master_stat_name == 'Goals':
            return (player_master_stat_val, 0)

    def __extract_shots_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="totalShots"]').get_attribute("textContent")

    def __extract_shotsontarget_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="shotsOnTarget"]').get_attribute("textContent")

    def __extract_foulscommitted_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="foulsCommitted"]').get_attribute("textContent")

    def __extract_foulsagainst_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="foulsSuffered"]').get_attribute("textContent")

    def __extract_assists_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="goalAssists"]').get_attribute("textContent")

    def __extract_yellows_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="yellowCards"]').get_attribute("textContent")

    def __extract_reds_stats(self, player_row):
        return player_row.find_element_by_xpath(
            './/span[@data-stat="redCards"]').get_attribute("textContent")

    def __extract_player_data(self, player_row):
        result_player_stat = {'goals': 0, 'saves': 0, 'shots': 0,
                              'shots-on-target': 0, 'fouls-committed': 0, 'fouls-against': 0, 'assists': 0, 'reds': 0, 'yellows': 0}
        player_no = player_row.find_element_by_xpath(
            './/div[1]/span[2]/span').get_attribute("textContent")
        player_name = player_row.find_element_by_xpath(
            './/div[1]/span[3]/a').get_attribute("textContent").replace('\t', '').replace('\n', '')

        goals, saves = self.__extract_master_stats(player_row)
        result_player_stat['goals'] = goals
        result_player_stat['saves'] = saves

        result_player_stat['shots'] = self.__extract_shots_stats(player_row)
        result_player_stat['shots-on-target'] = self.__extract_shotsontarget_stats(
            player_row)

        result_player_stat['fouls-committed'] = self.__extract_foulscommitted_stats(
            player_row)
        result_player_stat['fouls-against'] = self.__extract_foulsagainst_stats(
            player_row)

        result_player_stat['assists'] = self.__extract_assists_stats(
            player_row)
        result_player_stat['reds'] = self.__extract_reds_stats(
            player_row)
        result_player_stat['yellows'] = self.__extract_yellows_stats(
            player_row)

        return [player_name, player_no, result_player_stat]

    def __extract_players_data(self, players_elements):
        main_players_result = []
        for player_row in players_elements.find_elements_by_xpath('.//tr/td/div[1]'):
            player_result = self.__extract_player_data(
                player_row)
            main_players_result.append(player_result)

        sub_players_result = []
        for sub_player_row in players_elements.find_elements_by_xpath('.//tr/td/div[2]'):
            sub_player_result = self.__extract_player_data(
                sub_player_row)
            sub_players_result.append(sub_player_result)
        return main_players_result, sub_players_result

    def start_requests(self):
        for url in self.urls:
            self.driver.get(url)
            home_lineup_ele = self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/header/div/a[1]/div/div[2]')
            home_lineup = home_lineup_ele.text

            away_lineup_ele = self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/header/div/a[2]/div/div[2]')
            away_lineup = away_lineup_ele.text

            home_squad_table = self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/div/div[1]/div/div/div/table/tbody[1]')
            away_squad_table = self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/div/div[2]/div/div/div/table/tbody[1]')
            home_players_data, home_subplayers_data = self.__extract_players_data(
                home_squad_table)
            away_players_data, away_subplayers_data = self.__extract_players_data(
                away_squad_table)

            home_subsquad_table = self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/div/div[1]/div/div/div/table/tbody[2]')
            away_subsquad_table = self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/div/div[2]/div/div/div/table/tbody[2]')
            self.__add_sub_players_left(
                home_subplayers_data, home_subsquad_table)
            self.__add_sub_players_left(
                away_subplayers_data, away_subsquad_table)

            venue_name = str(self.driver.find_element_by_xpath(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[2]/article/div/ul[1]/li/div').text).replace('VENUE: ', '')

            date = str(self.driver.find_element_by_xpath(
                '/html/head/title').get_attribute("textContent")).replace(' - ESPN', '')
            date = date[date.rfind('-') + 2:]

            print('URL: ', url)
            print('DATE: ', date)
            print('VENUE: ', venue_name)
            print('HOME-lineup: ', home_lineup)
            print('AWAY-lineup: ', away_lineup)
            print('HOME-players: ', home_players_data)
            print('AWAY-players: ', away_players_data)
            print('HOME-subplayers: ', home_subplayers_data)
            print('AWAY-subplayers: ', away_subplayers_data)


class SpiderRunner():

    def __load_csv_data(self, fifa_no, start=None, end=None):
        result = []
        with open(f'results/match/premierLeague_{fifa_no}.csv', 'rt') as f:
            reader = csv.reader(f, delimiter=',')

            if start != None and end != None:
                for row in islice(reader, start, end):
                    if row[0] == 'E0':
                        result.append([row[1], row[2], row[3]])
            else:
                for row in reader:
                    if row[0] == 'E0':
                        result.append([row[1], row[2], row[3]])
        return result

    def __all_mondays(self, year):
        before = datetime.datetime(year-1, 8, 2)
        after = datetime.datetime(year+1, 6, 22)
        rr = rrule.rrule(
            rrule.WEEKLY, byweekday=relativedelta.SU, dtstart=before)
        return rr.between(before, after, inc=True)

    def __init__(self, fifa_no, spider_obj):
        self.fifa_no = fifa_no
        self.spider_model = spider_obj
        self.dates = self.__all_mondays(int('20' + str(fifa_no)))
        print(self.dates[0])

    def run_single(self):
        spider = self.spider_model(
            ['https://www.espn.com/soccer/match?gameId=422655'])
        spider.start_requests()


runner = SpiderRunner(16, ObtainMatchLineupsSpider)
# runner.run_single()
