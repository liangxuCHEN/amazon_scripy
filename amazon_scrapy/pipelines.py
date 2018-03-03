# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from amazon_scrapy.items import CateItem, ReviewProfileItem, ReviewDetailItem, SalesRankingItem, KeywordRankingItem
from amazon_scrapy.db.dbhelper import AmazonCateModel, AmazonKeyWordRankModel, DBSession

class AmazonScrapyPipeline(object):
    def open_spider(self, spider):
        self.session = DBSession()

    def process_item(self, item, spider):
        if isinstance(item, CateItem):
            print('save category: ' + item['title'])

            cate = AmazonCateModel(
                title=item["title"],
                link=item["link"],
                level=item["level"],
                pid=item["pid"]
            )
            self.session.add(cate)

        if isinstance(item, KeywordRankingItem):
            key_item = AmazonKeyWordRankModel(**item)
            self.session.add(key_item)

        self.session.commit()

    def close_spider(self, spider):
        self.session.close()

