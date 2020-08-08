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

    def __init__(self, dates, fifa_no):
        self.dates = dates
        self.fifa_no = fifa_no
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

    def __create_date_url(self, date):
        url_date_part = str(date.year) + str(date.month if date.month >= 10 else "0" + str(
            date.month)) + str(date.day if date.day >= 10 else "0" + str(date.day))
        return f'https://www.espn.com/soccer/fixtures/_/date/{url_date_part}/league/eng.1'

    def __obtain_game_urls_from_date(self, date_url, date, is_recovery):
        try:
            self.__get_url_with_retry(date_url)
            game_links_elements = self.driver.find_elements_by_xpath(
                './/html/body/div[5]/section/section/div/section/div[1]/div/div[2]/div/table/tbody/tr/td[1]/span[2]/a')
            result = []
            for game_link_ele in game_links_elements:
                game_url = game_link_ele.get_attribute(
                    'href').replace('report', 'match')
                result.append(game_url)
            return result
        except Exception as ex:
            if is_recovery:
                raise ex
            self.write_exception(date_url, date, ex)
            return []

    def __get_url_with_retry(self, url, retry_times=3):
        for i in range(0, retry_times):
            try:
                self.driver.get(url)
                time.sleep(2.5)
                page_error_text = self.driver.find_element_by_xpath(
                    '/html/body/div[4]/section/section/div/section/header/h1').get_attribute("textContent")
                if page_error_text != 'Page error.':
                    # Means we are not on error page that is fine
                    return
                else:
                    print('we are on error page')
            except Exception as ex:
                # Means we could not get the error page object and we fine
                return
        # Means that we gone through all retries and still hitting error page
        raise Exception(
            f'Tried: {retry_times} with url: {url} without success...')

    def save_data(self, data):
        print(
            f'[F_{self.fifa_no}]Saving match from {data[1]}: {data[3]} vs {data[4]}')
        with open(f'results/match_stats/match_and_players_{self.fifa_no}.csv', 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow(data)

    def write_exception(self, url, date, ex):
        print(
            f'[F_{self.fifa_no}] ERROR while: Saving match: {url}')
        with open(f'results/match_stats/errors/match_and_players_{self.fifa_no}.csv', 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow([url, date, str(ex)])

    def __get_element_text_with_retry(self, xpath, retry_times=3):
        home_lineup_ele = self.driver.find_element_by_xpath(xpath)
        for i in range(0, retry_times):
            if home_lineup_ele != None and home_lineup_ele.get_attribute("textContent") != None:
                return home_lineup_ele.get_attribute("textContent")
            else:
                time.sleep(0.5 * i)
        raise Exception(
            f'Could not obtain element: {xpath} after {retry_times}.')

    def obtain_all_for_match_url(self, match_url, date, is_recovery=False):
        try:
            self.__get_url_with_retry(match_url)
            home_lineup = self.__get_element_text_with_retry(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/header/div/a[1]/div/div[2]')

            away_lineup = self.__get_element_text_with_retry(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[1]/article/header/div/a[2]/div/div[2]')

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

            venue_name = str(self.__get_element_text_with_retry(
                '/html/body/div[5]/section/section/div/div/div/div/div[1]/div[2]/article/div/ul[1]/li/div')).replace('VENUE: ', '')

            match_date = str(self.__get_element_text_with_retry(
                '/html/head/title')).replace(' - ESPN', '')
            match_date = match_date[match_date.rfind('-') + 2:]

            home_team_name = self.__get_element_text_with_retry(
                '/html/body/div[5]/section/div[1]/header/div[2]/div[1]/div/div[2]/div[1]/div/a/span[2]')
            away_team_name = self.__get_element_text_with_retry(
                '/html/body/div[5]/section/div[1]/header/div[2]/div[3]/div/div[3]/div[2]/div/a/span[2]')

            data_to_save = [match_url, match_date, venue_name, home_team_name, away_team_name, home_lineup,
                            away_lineup, home_players_data, away_players_data, home_subplayers_data, away_subplayers_data]
            if all(v is not None for v in data_to_save):
                self.save_data(data_to_save)
            else:
                raise Exception("Object not full error")
        except Exception as ex:
            if is_recovery:
                raise ex
            else:
                self.write_exception(match_url, date, ex)

    def obtain_all_for_date_url(self, date_url, date, is_recovery=False):
        match_urls_for_date = self.__obtain_game_urls_from_date(
            date_url, date, is_recovery)
        for url in match_urls_for_date:
            self.obtain_all_for_match_url(url, date)

    def start_requests(self):
        for date in self.dates:
            date_url = self.__create_date_url(date)
            self.obtain_all_for_date_url(date_url, date)


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

    def __all_mondays(self, year, date_range=None):
        before = datetime.datetime(year-1, 8, 2)
        after = datetime.datetime(year + 1, 6, 22)
        if date_range:
            before, after = date_range[0], date_range[1]
        rr = rrule.rrule(
            rrule.WEEKLY, byweekday=relativedelta.SU, dtstart=before)
        return rr.between(before, after, inc=True)

    def __init__(self, fifa_no, spider_obj, date_range=None):
        self.fifa_no = fifa_no
        self.spider_model = spider_obj
        self.dates = self.__all_mondays(int('20' + str(fifa_no)), date_range)

    def run_single(self, dates=None):
        if dates == None:
            dates = self.dates
        spider = self.spider_model(dates, self.fifa_no)
        spider.start_requests()


def all_mondays_between(before, after):
    rr = rrule.rrule(rrule.WEEKLY, byweekday=relativedelta.SU, dtstart=before)
    return rr.between(before, after, inc=True)


class RecoverySpiderRunner():

    def __init__(self, fifa_no, spider_obj):
        self.fifa_no = fifa_no
        self.spider_model = spider_obj

    def __get_first_from_csv(self):
        first_row = None
        with open(f'results/match_stats/errors/match_and_players_{self.fifa_no}.csv', 'r') as f1, open(f'results/match_stats/errors/match_and_players_{self.fifa_no}_updated.csv', 'w') as f2:
            r = csv.reader(f1)
            for i, line in enumerate(r):
                if line == None:
                    return None
                if i == 0:
                    first_row = line
                else:
                    csv.writer(f2).writerow(line)
        os.remove(
            f'results/match_stats/errors/match_and_players_{self.fifa_no}.csv')
        os.rename(
            f'results/match_stats/errors/match_and_players_{self.fifa_no}_updated.csv', f'results/match_stats/errors/match_and_players_{self.fifa_no}.csv')
        return first_row

    def __write_row_back(self, row):
        with open(f'results/match_stats/errors/match_and_players_{self.fifa_no}.csv', 'a', newline='') as f:
            csv.writer(f).writerow(row)

    def run_single(self):
        spider = self.spider_model(None, self.fifa_no)
        row = self.__get_first_from_csv()
        while row != None:
            url, date = row[0], row[1]
            try:
                if 'fixtures/_/date' in url:
                    spider.obtain_all_for_date_url(url, date, is_recovery=True)
                elif 'match?gameId' in url:
                    spider.obtain_all_for_match_url(
                        url, date, is_recovery=True)
                else:
                    raise Exception('Unrecognised format')
            except Exception as ex:
                if 'Browsing context has been discarded' in str(ex):
                    print('terminated...')
                    exit()
                print(
                    f'[F_{self.fifa_no}]Error while processing: {row[0]}, adding back to file. \n\tEx: {ex}')
                self.__write_row_back(row)
            finally:
                row = self.__get_first_from_csv()


# runner = SpiderRunner(16, ObtainMatchLineupsSpider)
# start_16, end_16 = datetime.datetime(
#     2015, 8, 2), datetime.datetime(2016, 5, 18)
# runner.run_single(all_mondays_between(start_16, end_16))
# print('done_16')
# recovery = RecoverySpiderRunner(16, ObtainMatchLineupsSpider)
# recovery.run_single()

# runner = SpiderRunner(17, ObtainMatchLineupsSpider)
# start_17, end_17 = datetime.datetime(
#     2016, 8, 8), datetime.datetime(2017, 5, 22)
# runner.run_single(all_mondays_between(start_17, end_17))
# print('done_17')
# recovery = RecoverySpiderRunner(17, ObtainMatchLineupsSpider)
# recovery.run_single()

runner = SpiderRunner(18, ObtainMatchLineupsSpider)
start_18, end_18 = datetime.datetime(
    2017, 8, 7), datetime.datetime(2018, 5, 14)
runner.run_single(all_mondays_between(start_18, end_18))
print('done_18')
# recovery = RecoverySpiderRunner(18, ObtainMatchLineupsSpider)
# recovery.run_single()

# runner = SpiderRunner(19, ObtainMatchLineupsSpider)
# start_19, end_19 = datetime.datetime(
#     2018, 8, 6), datetime.datetime(2019, 5, 13)
# runner.run_single(all_mondays_between(start_19, end_19))
# print('done_19')
# recovery = RecoverySpiderRunner(19, ObtainMatchLineupsSpider)
# recovery.run_single()

# runner = SpiderRunner(20, ObtainMatchLineupsSpider)
# start_20, end_20 = datetime.datetime(
#     2019, 8, 5), datetime.datetime(2020, 3, 10)
# runner.run_single(all_mondays_between(start_20, end_20))
# print('done_20_v1')

# runner = SpiderRunner(20, ObtainMatchLineupsSpider)
# start_20, end_20 = datetime.datetime(
#     2020, 6, 15), datetime.datetime(2020, 7, 27)
# runner.run_single(all_mondays_between(start_20, end_20))
# print('done_20_v2')
