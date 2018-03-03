# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy



class CateItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    level = scrapy.Field()
    pid = scrapy.Field()


class AsinBestItem(scrapy.Item):
    asin = scrapy.Field()
    cid = scrapy.Field()
    rank = scrapy.Field()


class DetailItem(scrapy.Item):
    asin = scrapy.Field()
    image = scrapy.Field()
    title = scrapy.Field()
    star = scrapy.Field()
    reviews = scrapy.Field()
    seller_price = scrapy.Field()
    amazon_price = scrapy.Field()


class ReviewProfileItem(scrapy.Item):
    asin = scrapy.Field()
    product = scrapy.Field()
    brand = scrapy.Field()
    seller = scrapy.Field()
    image = scrapy.Field()
    review_total = scrapy.Field()
    review_rate = scrapy.Field()
    pct_five = scrapy.Field()
    pct_four = scrapy.Field()
    pct_three = scrapy.Field()
    pct_two = scrapy.Field()
    pct_one = scrapy.Field()


class ReviewDetailItem(scrapy.Item):
    asin = scrapy.Field()
    review_id = scrapy.Field()
    reviewer = scrapy.Field()
    review_url = scrapy.Field()
    star = scrapy.Field()
    date = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()


class KeywordRankingItem(scrapy.Item):
    skwd_id = scrapy.Field()
    rank = scrapy.Field()
    date = scrapy.Field()
    currency = scrapy.Field()
    low_price = scrapy.Field()
    high_price = scrapy.Field()
    stars = scrapy.Field()
    reviews = scrapy.Field()
    project_name = scrapy.Field()
    shop_name = scrapy.Field()
    item_pic = scrapy.Field()
    item_name = scrapy.Field()


class SalesRankingItem(scrapy.Item):
    rank = scrapy.Field()
    classify = scrapy.Field()
    asin = scrapy.Field()