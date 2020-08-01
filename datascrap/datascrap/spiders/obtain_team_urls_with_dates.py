import scrapy
import csv
import re


class ObtainTeamUrlsWithDatesSpider(scrapy.Spider):
    name = "obtain_team_urls_with_dates"

    def start_requests(self):
        urls = [
            'https://www.fifaindex.com/teams/fifa20/?league=13'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    TEAM_CSS_PART = 'body > main > div > div > div.col-lg-8 > div.responsive-table.table-rounded > table > tbody > tr > td:nth-child(2) > a'
    FIFA_UPDATES_PART = 'body > main > div > div:nth-child(3) > div.col-lg-8 > nav:nth-child(1) > ol > li:nth-child(3) > div > a'

    def parse(self, response):
        with open('results/team/team_date_url.csv', 'w', newline='') as f:
            w = csv.writer(f)
            teams_css = response.css(
                ObtainTeamUrlsWithDatesSpider.TEAM_CSS_PART)
            updates_css = response.css(
                ObtainTeamUrlsWithDatesSpider.FIFA_UPDATES_PART)

            update_paths_and_dates = self.__extract_fifa_update_paths_with_dates(
                updates_css)

            for team_css in teams_css:
                team_name = team_css.css('::text').get()
                team_path = team_css.css('::attr(href)').get()
                team_path = re.sub(r'fifa.*', '', team_path)

                for (update_path, date) in update_paths_and_dates:
                    url = 'https://www.fifaindex.com' + team_path + update_path
                    w.writerow([team_name, date, url])

    def __extract_fifa_update_paths_with_dates(self, updates_css):
        result = []
        for u in updates_css:
            path = u.css('::attr(href)').get().replace(
                '/teams/', '').replace('/', '')
            date = u.css('::text').get()
            result.append((path, date))
        return result
