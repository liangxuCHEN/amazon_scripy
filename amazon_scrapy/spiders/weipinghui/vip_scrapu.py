import scrapy
from amazon_scrapy.items import VipDataItem
import re
from datetime import datetime


from amazon_scrapy.db.dbhelper import engine, ProjectModel
from sqlalchemy.orm import sessionmaker



Session_Class = sessionmaker(bind=engine)  # 创建与数据库的会话，Session_Class为一个类

Session = Session_Class()  # 实例化与数据库的会话

#
# search_parameter = [
#     {'project_name':'20180408_car', 'market': '唯品汇', 'min_price':'', 'max_price':'', 'key_word': '男士T恤', 'page_number': 1}
# ]


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

            # 更新状态
            vip_project.status = 'finish'
            Session.commit()

    def mainpage(self, response):
        all_data = re.findall(r',"products":(\[.*?\])', response.text)
        data = eval(all_data[0])
        # print(len(data))
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
            yield item


    # def getid(self,response):
    #     #分析一个分类下品牌信息，找出品牌id，组成品牌店铺url和店铺下所有商品ID的url
    #     print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', response.text)
    #     data = re.findall(r'"success","data":(\[.*?\]),"info":', response.text)[0]
    #     print('xxxxxxx', data)
    #     for x in eval(data):
    #         mm = Sql.select_pp(x['brand_id'])#判断该品牌是否已经保存
    #         if mm == 1:
    #             print('该品牌数据已经保存')
    #         else:
    #             name_url = 'http://list.vip.com/%s.html' %x['brand_id'] #获取品牌名称的
    #             data_url ='http://list.vip.com/api-ajax.php?callback=getMerchandiseIds&getPart=getMerchandiseRankList&r=%s' %x['brand_id']
    #             yield scrapy.Request(name_url,callback=self.getname,meta={'brand_id':x['brand_id'],'fl_name':response.meta['fl_name']})
    #             yield scrapy.Request(data_url,callback=self.getdata_url,meta={'brand_id':x['brand_id']})
    #
    # def getname(self,response):
    #     #获取品牌的名称，构造品牌收藏数所在的页面url
    #     name = response.xpath('//meta[@name="keywords"]/@content').extract()[0]
    #     scs_url = 'http://fav.vip.com/api/fav/sales/isfavanducount?callback=inquiryFavStatusAmountCB&business=VIPSALES&brand_id='+str(response.meta['brand_id'])
    #     yield scrapy.Request(
    #             scs_url,
    #             callback=self.getshoucang,
    #             meta={
    #                 'name':name,
    #                 'brand_id':response.meta['brand_id'],
    #                 'fl_name':response.meta['fl_name']},
    #             headers={
    #                 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    #                 'Referer':response.url})
    #     #注意，收藏数所在的页面，在请求的时候请求头需要加上Referer，否则为空
    #
    # def getshoucang(self,response):
    #     #获取品牌的收藏数，构造店铺商品数量统计的页面url
    #     shoucang = re.findall(r'"ucount":(.*?),"brandfav"', response.text)[0]
    #     lei_url = 'http://list.vip.com/api-ajax.php?callback=getCategoryListCB&getPart=getCategoryList&r='+str(response.meta['brand_id'])
    #     yield scrapy.Request(lei_url,callback=self.getlei,meta={'name':response.meta['name'],'brand_id':response.meta['brand_id'],'shoucang':shoucang,'fl_name':response.meta['fl_name']})
    #
    # def getlei(self,response):
    #     #获取商品总数，并且返回数据品牌相关的数据，传给pipelines保存到数据库
    #     item = VipItem()
    #     lei = 0
    #     for x in eval(re.findall(r'{"category":(\[.*?\]),"size":', response.text)[0]):
    #         lei =lei + int(x['total'])
    #     item['pp_name'] = response.meta['name']
    #     item['fl_name'] = response.meta['fl_name']
    #     item['pp_shoucang'] = response.meta['shoucang']
    #     item['pp_url'] = 'http://list.vip.com/%s.html' %response.meta['brand_id']
    #     item['pp_id'] = response.meta['brand_id']
    #     item['pp_shu'] = lei
    #     yield item
    #
    #
    # def getdata_url(self,response):
    #     #获取店铺所有商品的id，由于每一次请求商品详情，最多只能50个，故以for循环进行分割，构造多个商品详情列表所在页面的url
    #     data =eval(re.findall(r'"products":(\[.*?\]),"keepTime"', response.text)[0])
    #     if data==[]:
    #         print('已经抢购一空')
    #     else:
    #         b =[data[i:i+50] for i in range(0,len(data),50)]
    #         for u in [",".join(x) for x in b]:
    #             url = 'http://list.vip.com/api-ajax.php?callback=getMerchandiseDroplets1&getPart=getMerchandiseInfoList&productIds=%s&r=%s' %(u,str(response.meta['brand_id']))
    #             yield scrapy.Request(url,callback=self.getdata,meta={'brand_id':response.meta['brand_id']})
    #
    # def getdata(self,response):
    #     #获取商品信息，传给pipelines保存到数据库
    #     item = VipDataItem()
    #     null = ''
    #     data =eval(re.findall(r'"merchandiseInfoList":(\[.*?\])', response.text)[0])
    #     for d in data:
    #         item['data_pp_id'] = response.meta['brand_id']
    #         item['data_id'] = d['mid']
    #         item['data_name'] = d['productName']
    #         item['data_url'] = d['detailUrl'].replace('\/','/')
    #         item['data_jiage'] = d['vipshopPrice']
    #         mm = Sql.select_data(d['mid'])
    #         if mm == 1:
    #             print('该商品已经存在')
    #         else:
    #             yield item

