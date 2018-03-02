import scrapy
import json

class ChinaproxySpider(scrapy.Spider):
    name = "chinaproxy"
    # custom_settings = {
    #     'LOG_LEVEL': 'ERROR',
    #     'LOG_ENABLED': True,
    #     'LOG_STDOUT': True
    # }


    def start_requests(self):

        self.headers = {
            'Host': 'www.xicidaili.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:52.0) Gecko/20100101 Firefox/52.0',
        }

        url = "http://www.xicidaili.com/nt/"
        yield scrapy.Request(url=url, callback=self.parse, meta={})

    def parse(self, response):
        ips = response.xpath('//*[@id="ip_list"]/tr')

        ip_table = list()
        for ip in ips:
            tmp_ip = ip.xpath('./td[2]').re("([0-9]{1,4}.[0-9]{1,4}.[0-9]{1,4}.[0-9]{1,4})")
            tmp_port = ip.xpath('./td[3]').re("([0-9]{1,4})")
            if tmp_ip and tmp_port:
                ip_table.append('{}:{}'.format(tmp_ip[0], tmp_port[0]))

        with open('proxy_china.json', 'w') as f:
            json.dump(ip_table, f)
