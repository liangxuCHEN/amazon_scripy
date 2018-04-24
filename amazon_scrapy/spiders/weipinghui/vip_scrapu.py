import scrapy
from amazon_scrapy.items import VipDataItem, VipBandItem
import re
from datetime import datetime
import requests
import time

from amazon_scrapy.db.dbhelper import ProjectModel, DBSession

Session = DBSession()  # 实例化与数据库的会话

def get_project():
    entity = Session.query(ProjectModel).filter(
        (ProjectModel.status=='new') &
        (ProjectModel.market=='唯品会')).all()
    return [e.to_json() for e in entity]


class VipSpider(scrapy.Spider):
    name = 'vip'
    allowed_domains = ['vip.com']
    start_urls = ['http://category.vip.com']


    def parse(self, response):
        search_parameter = get_project()
        for data in search_parameter:
            vip_project = Session.query(ProjectModel).filter_by(id=data['id']).first()
            vip_project.status = 'running'
            Session.commit()
            current_time = datetime.now().strftime('%Y%m%d')

            key = str(data['key_word'])
            if ' ' in key:
                key = ''.join(key.split())

            for i in range(0,int(data['page_number'])):
                temp_url = "http://category.vip.com/suggest.php?keyword={key}&page={page}&count=50".format(key=key,page=i)

                yield scrapy.Request(
                    url=temp_url,
                    callback=self.mainpage,
                    meta={'created': current_time, 'project_name': data['project_name']})

            #更新状态
            vip_project.status = 'finish'
            Session.commit()

    def mainpage(self, response):
        all_data = re.findall(r',"products":(\[.*?\])', response.text)
        data = eval(all_data[0])
        brand_list = set()

        for vip_data in data:
            vip_data['market_price_of_min_sell_price'] = vip_data['price_info']['market_price_of_min_sell_price']
            if vip_data['market_price_of_min_sell_price'] == '':
                vip_data['market_price_of_min_sell_price'] = -1

            vip_data['sell_price_min_tips'] = vip_data['price_info']['sell_price_min_tips']
            if vip_data['sell_price_min_tips'] == '':
                vip_data['sell_price_min_tips'] = -1

            vip_data['discount_index_min_tips'] = vip_data['price_info']['discount_index_min_tips']
            del(vip_data['price_info'])

            item = VipDataItem(**vip_data)
            item['project_name'] = response.meta['project_name']
            item['created'] = response.meta['created']
            item['small_image'] = item['small_image'].replace('\\','')[2:]

            brand_list.add(item['brand_id'])
            yield item

        for brand_id in brand_list:
            brand_url = "https://list.vip.com/{brand_id}.html".format(brand_id=brand_id)
            yield scrapy.Request(
                brand_url,
                callback=self.get_brand_detail,
                meta={'brand_id':brand_id, 'brand_url': brand_url}
            )


    def get_brand_detail(self,response):
        # 获取品牌相关的数据
        item = VipBandItem()
        item['brand_id'] = response.meta['brand_id']

        brand_data_url = 'http://list.vip.com/api-ajax.php?callback=getCategoryListCB&getPart=getCategoryList&r={brand_id}'.format(
            brand_id=response.meta['brand_id'])

        brand_data_result = requests.get(brand_data_url)

        try:
            content = re.findall(r'getCategoryListCB(\(.*?\))', brand_data_result.text)
            content = content[0][1:-1].replace('null', '""')
            brand_data_result = eval(content)
            item['detail_json'] = brand_data_result.get('data', {'data': 'empty'})
        except Exception as e:
            print('获取品牌信息出错', e)
            item['detail_json'] = {'data': 'empty'}


        brand_name = response.xpath('//*[@id="J_pro_list_fav"]/dl/dt/text()').extract()

        if brand_name:
            item['brand_name'] = brand_name[0]
        else:
            item['brand_name'] = ''

        fav_session = requests.Session()
        fav_session.headers.update({'referer': response.meta['brand_url']})

        fav_url = "https://fav.vip.com/api/fav/sales/isfavanducount?callback=inquiryFavStatusAmountCB&business=VIPSALES&brand_id={brand_id}&_={post_time}"
        fav_url = fav_url.format(
            brand_id=item['brand_id'],
            post_time=str(int(time.time()*1000))
        )
        fav_result = fav_session.get(fav_url)
        try:
            content = re.findall(r'inquiryFavStatusAmountCB(\(.*?\))', fav_result.text)
            fav_result = eval(content[0])
            item['fav_person_number'] = int(fav_result['data']['ucount'])
        except Exception as e:
            print('获取品牌关注数量出错', e)
            item['fav_person_number'] = -1

        discount = response.xpath('//*[@id="J_pro_list_fav"]/dl/dd/span/text()').extract()

        if discount:
            item['discount_index_min_tips'] = float(discount[0])
        else:
            item['discount_index_min_tips'] = ''

        yield item
