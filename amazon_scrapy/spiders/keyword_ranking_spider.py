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
    # 开启日志
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
        self.max_page = 5   # 查看多少页
        # 通过信号,调用函数
        dispatcher.connect(self.init_scrapy, signals.engine_started)
        #dispatcher.connect(self.close_scrapy, signals.engine_stopped)

    def start_requests(self):
        for keyword, poll in self.keyword_pool.items():
            url = ('https://www.amazon.com/s/?field-keywords=%s&t=' + Helper.random_str(10)) % keyword
            yield scrapy.Request(url, self.load_first_page, meta={'items': poll})

    def reviews_detail(self, response):
        # 获取产品名称
        item = response.meta['item']
        product = response.css('.product-title h1 a::text').extract()
        item['item_name'] = product[0]
        # 获取产品 商家
        item['shop_name']= response.css('.product-by-line a::text').extract()[0]
        item['item_pic'] = response.css('.product-image img::attr(src)').extract()[0]
        yield item

        # 获取各星评价百分比数
        # review_summary = response.css('.reviewNumericalSummary .histogram '
        #                               '#histogramTable tr td:last-child').re(r'\d{1,3}\%')
        #
        # pct = list(map(lambda x: x[0:-1], review_summary))
        #
        # item['pct_five'] = pct[0]
        # item['pct_four'] = pct[1]
        # item['pct_three'] = pct[2]
        # item['pct_two'] = pct[3]
        # item['pct_one'] = pct[4]


    def parse(self, response):
        project_name = response.meta['items'][0]['project_name']
        result_li = response.xpath('//li[@data-asin]')
        # for item in response.meta['items']:
        #     if len(result_li) == 0:
        #         self.found[item['id']] = 'none'
        #         logging.warning("[keyword none]  url: [%s] skwd_id:[%s] asin:[%s] \r\n body: %s" % (response.url, item['id'],item['asin'], response.body))
        #     else:
        for result in result_li:
            item = KeywordRankingItem()
            item['project_name'] = project_name
            item['skwd_id'] = result.xpath('./@data-asin').extract()[0]

            data_id = result.xpath('./@id').extract()[0]
            item['rank'] = int(data_id.split('_')[1])

            item['date']  = Helper.get_now_date()

            prices = result.css('.a-offscreen')
            min_price = max_price = 0
            for p in prices:

                tmp_p = p.re('>(.*)<')
                if tmp_p:
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

            item['low_price'] =min_price
            item['high_price'] = max_price


            stars = result.css('.a-icon-alt').re(">(.*)out of 5 stars")
            if stars:
                item['stars'] = float(stars[0].strip())
            else:
                item['stars'] = -1

            reviews = result.css('.a-row').xpath('./a[@class="a-size-small a-link-normal a-text-normal"]').re('Reviews">(.*)<')
            if reviews:
                item['reviews'] = int(reviews[0].strip().replace(',', ''))
            else:
                item['reviews'] = -1

            yield scrapy.Request(
                'https://www.amazon.com/product-reviews/%s' % item['skwd_id'],
                callback=self.reviews_detail,
                meta={'item': item}
            )

    def load_first_page(self, response):
        # 分页寻找
        page = response.css('#bottomBar span.pagnDisabled::text').extract()
        page = 1 if len(page) == 0 else int(page[0])
        page_num = 1
        while page_num <= page:
            # yield scrapy.Request(response.url + '&page=%s' % page_num, self.parse, meta={'asin': response.meta['item']['asin'],
            #                                                                              'skwd_id': response.meta['item']['id']})
            yield scrapy.Request(response.url + '&page=%s' % page_num, self.parse, meta={'items': response.meta['items']})
            page_num += 1
            if page_num > self.max_page:
                break

    def init_scrapy(self):
        # 输入关键词,TODO:从数据库读取关键词
        #self.items = RankingSql.fetch_keywords_ranking()
        # asin 可以查找商品asin号,看它在这个关键词里面排行
        self.items = [{'id': 1, 'asin': 'B017198D8S', 'keyword':'Aromatherapy', 'project_name': 'test_project'}]
        for item in self.items:
            if item['keyword'] in self.keyword_pool.keys():
                self.keyword_pool[item['keyword']].append(
                    {'id': item['id'], 'asin': item['asin'], 'project_name': item['project_name']})
            else:
                self.keyword_pool[item['keyword']] = [
                    {'id': item['id'], 'asin': item['asin'], 'project_name': item['project_name']}]

        # 是否找对应的商品
        self.found = {item['id']: False for item in self.items}

    """
    需要查找对应商品才记录的时候，才开启这个功能
    def close_scrapy(self):
    
        print(self.found)
        for skwd_id, is_found in self.found.items():
            # print(is_found)
            if is_found is not True:
                if is_found == 'none':
                    # RankingSql.update_keywords_none_rank(skwd_id)
                    logging.info('[keyword none] skwd_id:[%s]' % skwd_id)
                # else:
                #     RankingSql.update_keywords_expire_rank(skwd_id)
            else:
                keywordrank = KeywordRankingItem()
                keywordrank['skwd_id'] = skwd_id
                keywordrank['rank'] = min(self.store_poll[skwd_id])
                keywordrank['date'] = self.store_date[skwd_id]
                # RankingSql.insert_keyword_ranking(keywordrank)

    """
