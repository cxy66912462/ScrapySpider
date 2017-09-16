# -*- coding: utf-8 -*-

import  requests
from scrapy.selector import Selector
import MySQLdb

conn = MySQLdb.connect(host='127.0.0.1',user='root',passwd='root',db='scrapy_db',charset='utf8')
cursor = conn.cursor()



def crawl_ips():
    # 爬取西刺免费代理
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}
    for i in range(2333):
        re = requests.get('http://www.xicidaili.com/nn/{0}'.format(i),headers=headers)
        selector = Selector(text=re.text)
        all_trs = selector.css('#ip_list tr')
        ip_list = []
        for tr in  all_trs[1:]:
            speed_str = tr.css('.bar::attr(title)').extract()[0]
            if speed_str:
                speed_str = float(speed_str.split('秒')[0])
            all_texts = tr.css('td::text').extract()
            ip = all_texts[0]
            port=all_texts[1]
            proxy_type=all_texts[5]
            if proxy_type == 'HTTPS':
                continue
            ip_list.append((ip,port,proxy_type,speed_str))
            print(ip,port,proxy_type,speed_str)
        for ip_info in ip_list:
            try:
                cursor.execute(
                    "insert into proxy_ip(ip,port,proxy_type,speed) values('{0}','{1}','{2}',{3})".format(
                        ip_info[0], ip_info[1],ip_info[2],ip_info[3]
                    )
                )
            except Exception as e:
                continue
            conn.commit()

class GetIP(object):
    def delete_ip(self):
        #删除无效ip
        sql = "delete from proxy_ip where ip = '{0}'".format(ip)
        cursor.execute(sql)
        conn.commit()
        return True

    def judge_ip(self,ip,port):
        #判断ip是否可用
        http_url = 'https://www.baidu.com'
        proxy_url = 'http://{0}:{1}'.format(ip,port)
        try:
            proxt_dict = {
                'http':proxy_url,
            }
            response = requests.get(http_url,proxies=proxt_dict)
        except Exception as e:
            print(ip,'代理不可用')
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code>=200 and code<=300:
                print(ip,'代理可用')
                return True
            else:
                print(ip,'代理不可用')
                self.delete_ip(ip)
                return False
    def get_random_ip(self):
        #从数据库中随机获取ip
        sql = 'select ip,port from proxy_ip order by Rand() LIMIT 1'
        result = cursor.execute(sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port=ip_info[1]

            judge_result = self.judge_ip(ip,port)
            if judge_result:
                return "http://{0}:{1}".format(ip,port)
            else:
                return self.get_random_ip()

# print(crawl_ips())
if __name__ == '__main__':
    crawl_ips()
    #get_ip = GetIP()
    #get_ip.get_random_ip()