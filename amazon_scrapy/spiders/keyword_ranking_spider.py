import logging

import scrapy
from pydispatch import dispatcher
from scrapy import signals
from amazon_scrapy.helper import Helper
from amazon_scrapy.items import KeywordRankingItem
#from amazon_scrapy.sql import RankingSql

# https://github.com/dynamohuang/amazon-scrapy/tree/master/amazon

class KeywordRankingSpider(scrapy.Spider):
    name = 'keyword_ranking'
    # custom_settings = {
    #     'LOG_LEVEL': 'ERROR',
    #     'LOG_FILE': 'keyword_ranking.json',
    #     'LOG_ENABLED': True,
    #     'LOG_STDOUT': True,
    #     'CONCURRENT_REQUESTS_PER_DOMAIN': 30
    # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = {}
        self.found = {}
        self.keyword_pool = {}
        self.store_poll = {}
        self.store_date = {}
        # 通过信号,调用函数
        dispatcher.connect(self.init_scrapy, signals.engine_started)
        #dispatcher.connect(self.close_scrapy, signals.engine_stopped)

    def start_requests(self):
        for keyword, poll in self.keyword_pool.items():
            url = ('https://www.amazon.com/s/?field-keywords=%s&t=' + Helper.random_str(10)) % keyword
            yield scrapy.Request(url, self.load_first_page, meta={'items': poll})

    def parse(self, response):
        result_li = response.xpath('//li[@data-asin]')
        # for item in response.meta['items']:
        #     if len(result_li) == 0:
        #         self.found[item['id']] = 'none'
        #         logging.warning("[keyword none]  url: [%s] skwd_id:[%s] asin:[%s] \r\n body: %s" % (response.url, item['id'],item['asin'], response.body))
        #     else:
        for result in result_li:
            item = KeywordRankingItem()
            item['skwd_id'] = result.xpath('./@data-asin').extract()[0]

            data_id = result.xpath('./@id').extract()[0]
            item['skwd_id'] = data_id.split('_')[1]

            item['date']  = Helper.get_now_date()

            prices = result.css('.a-offscreen')
            min_price = max_price = 0
            for p in prices:

                tmp_p = p.re('>(.*)<')
                if len(tmp_p) >0:
                    tmp_p = tmp_p[0]
                    if '[' in tmp_p:
                        continue

                    item['currency'] = tmp_p[0]

                    if '-' in tmp_p:
                        min_price, max_price = tmp_p.split('-')
                        min_price = float(min_price.strip()[1:])
                        max_price = float(max_price.strip()[1:])
                    else:
                        tmp_p = float(tmp_p[1:])
                        if tmp_p < min_price and min_price > 0:
                            min_price = tmp_p

                        if tmp_p > max_price:
                            max_price = tmp_p

            if min_price != 0:
                item['low_price'] =min_price
            if max_price != 0:
                item['high_price'] = max_price

            print(item)
            #stars = result.css('.a-icon-alt').extract()
            #print(stars)

            #reviews = result.css('.a-row').xpath('./a[@class="a-size-small a-link-normal a-text-normal"]').extract()
            #print(reviews)



    def load_first_page(self, response):
        page = response.css('#bottomBar span.pagnDisabled::text').extract()
        page = 1 if len(page) == 0 else int(page[0])
        page_num = 1
        while page_num <= page:
            # yield scrapy.Request(response.url + '&page=%s' % page_num, self.parse, meta={'asin': response.meta['item']['asin'],
            #                                                                              'skwd_id': response.meta['item']['id']})
            yield scrapy.Request(response.url + '&page=%s' % page_num, self.parse, meta={'items': response.meta['items']})
            page_num += 1
            break

    def init_scrapy(self):
        #self.items = RankingSql.fetch_keywords_ranking()
        self.items = [{'id': 1, 'asin': 'B017198D8S', 'keyword':'GoYoga'},
                      {'id': 2, 'asin': 'B0748BSHN5', 'keyword':'Fitbit'}]
        for item in self.items:
            if item['keyword'] in self.keyword_pool.keys():
                self.keyword_pool[item['keyword']].append({'id': item['id'], 'asin': item['asin']})
            else:
                self.keyword_pool[item['keyword']] = [{'id': item['id'], 'asin': item['asin']}]


        self.found = {item['id']: False for item in self.items}

    # def close_scrapy(self):
    #     print(self.found)
    #     for skwd_id, is_found in self.found.items():
    #         # print(is_found)
    #         if is_found is not True:
    #             if is_found == 'none':
    #                 # RankingSql.update_keywords_none_rank(skwd_id)
    #                 logging.info('[keyword none] skwd_id:[%s]' % skwd_id)
    #             # else:
    #             #     RankingSql.update_keywords_expire_rank(skwd_id)
    #         else:
    #             keywordrank = KeywordRankingItem()
    #             keywordrank['skwd_id'] = skwd_id
    #             keywordrank['rank'] = min(self.store_poll[skwd_id])
    #             keywordrank['date'] = self.store_date[skwd_id]
    #             # RankingSql.insert_keyword_ranking(keywordrank)


