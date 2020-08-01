import scrapy
from scrapy.crawler import CrawlerRunner
import csv
import re
from multiprocessing import Process, Queue
from twisted.internet import reactor


class ObtainPlayerUrlsForTeamSpider(scrapy.Spider):
    name = "obtain_player_urls_with_dates_for_team"

    def __init__(self, url_batch, fifa_no, partition):
        self.url_batch = url_batch
        self.fifa_no = fifa_no
        self.partition = partition

    def start_requests(self):
        print(
            f'Running spider {self.fifa_no}_{self.partition} witch batch size: {len(self.url_batch)}')
        for url in self.url_batch:
            yield scrapy.Request(url=url, callback=self.parse)

    PLAYERS_GRID_CSS_PART = 'body > main > div > div:nth-child(3) > div.col-lg-8 > div:nth-child(6) > table > tbody > tr'
    TEAM_NAME_CSS_PART = 'body > main > div > div:nth-child(3) > div.col-lg-8 > div.row.pt-3 > div.col-sm-6.col-md-7 > div.d-flex.mb-3.align-items-center > div.pl-3 > h1 ::text'
    DATE_CSS_PART = 'body > main > div > div:nth-child(3) > div.col-lg-8 > nav > ol > li:nth-child(3) > a ::text'

    def parse(self, response):
        with open(f'results/player/team_player_date_url_{self.fifa_no}_{self.partition}.csv', 'w', newline='') as f:
            w = csv.writer(f)
            team_name = response.css(
                ObtainPlayerUrlsForTeamSpider.TEAM_NAME_CSS_PART).get().strip()
            date = response.css(
                ObtainPlayerUrlsForTeamSpider.DATE_CSS_PART).get()

            players_css = response.css(
                ObtainPlayerUrlsForTeamSpider.PLAYERS_GRID_CSS_PART)

            for player_css in players_css:
                simple_stat_css = player_css.css('td')
                player_number = simple_stat_css[0].css('::text').get()
                player_position = simple_stat_css[1].css('::text').get()
                player_name = simple_stat_css[5].css('::text').get()
                player_link = 'https://www.fifaindex.com' + \
                    simple_stat_css[5].css('a::attr(href)').get()
                w.writerow([team_name, player_name, date,
                            player_link, player_number, player_position])
                


def run_spider(batch, fifa_no, partition):
    def f(q):
        try:
            runner = CrawlerRunner()
            deferred = runner.crawl(
                ObtainPlayerUrlsForTeamSpider, url_batch=batch, fifa_no=fifa_no, partition=partition)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result


def run_spiders(fifa_no):
    urls = []
    with open(f'results/team/team_date_url_{fifa_no}.csv') as csvfile:
        spamreader = csv.reader(csvfile)
        for row in spamreader:
            url = row[2]
            urls.append(url)

    def batches(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    counter = 0
    for batch in batches(urls, 1):
        run_spider(batch, fifa_no, counter)
        counter += 1
