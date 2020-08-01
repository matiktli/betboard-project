import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.selector import Selector
import csv
import re
from multiprocessing import Process, Queue
from twisted.internet import reactor
import os


class ObtainPlayerStatsSpider(scrapy.Spider):
    name = "obtain_player_stats_with_dates"

    def __init__(self, url_batch, fifa_no, partition):
        self.url_batch = url_batch
        self.fifa_no = fifa_no
        self.partition = partition

    def start_requests(self):
        print(
            f'Running spider {self.fifa_no}_{self.partition} witch batch size: {len(self.url_batch)} {self.url_batch[0]}')
        for url in self.url_batch:
            yield scrapy.Request(url=url, callback=self.parse)

    PLAYER_STATS_GRIDS_CSS_PART = 'body > main > div > div:nth-child(3) > div.col-lg-8 > div.row.grid > div > div'
    DATE_CSS_PART = 'body > main > div > div:nth-child(3) > div.col-lg-8 > nav > ol > li:nth-child(3) > a ::text'

    def parse(self, response):
        with open(f'results/player_stats/playerid_date_stats_{self.fifa_no}_{self.partition}.csv', 'a', newline='') as f:
            w = csv.writer(f)
            date = response.css(
                ObtainPlayerStatsSpider.DATE_CSS_PART).get()
            url = response.url.replace('https://www.fifaindex.com/player/', '')
            player_id = url[:url.find('/')]

            player_stat_grids_css = response.css(
                ObtainPlayerStatsSpider.PLAYER_STATS_GRIDS_CSS_PART).getall()

            stats = []
            for stats_grid in player_stat_grids_css:
                stats_g = Selector(text=stats_grid)
                parent_stat_name = stats_g.css(
                    'div > h5 ::text').get()
                stat_obj = {'name': parent_stat_name,
                            'value': {}}
                stats_and_names = stats_g.css('div > p ::text').getall()
                if parent_stat_name == 'Traits':
                    for trait in stats_and_names:
                        stat_obj['value'][trait] = trait
                else:
                    def grouped(iterable, n=2):
                        return zip(*[iter(iterable)] * n)
                    for (sub_stat_name, stat_val) in grouped(stats_and_names):
                        stat_obj['value'][sub_stat_name] = stat_val
                stats.append(stat_obj)

            w.writerow([player_id, date, stats[0], stats[1], stats[2],
                        stats[3], stats[4], stats[5], stats[6], stats[7] if len(stats) == 8 else {}])


def run_spider(batch, fifa_no, partition):
    def f(q):
        try:
            runner = CrawlerRunner()
            deferred = runner.crawl(
                ObtainPlayerStatsSpider, url_batch=batch, fifa_no=fifa_no, partition=partition)
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


def batches(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def run_spiders(fifa_no):
    for f in sorted(os.listdir('results/player')):
        if f'url_{fifa_no}' in f:
            urls = []
            with open('results/player/' + f) as csvfile:
                spamreader = csv.reader(csvfile)
                for row in spamreader:
                    url = row[3]
                    urls.append(url)

            partition_no = f[f.rfind("_")+1:f.rfind(".csv")]
            for u in batches(urls, 20):
                run_spider(u, fifa_no, partition_no)
