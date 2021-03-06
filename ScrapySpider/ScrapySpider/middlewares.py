# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from fake_useragent import  UserAgent
from ScrapySpider.tools.crawl_xici_ips import GetIP
from selenium import webdriver
from scrapy.http import HtmlResponse

class ScrapyspiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentMiddlware(object):
    #随机更换user-agent
    def __init__(self,crawelr):
        super(RandomUserAgentMiddlware,self).__init__()
        # self.user_agent_list = crawel.settints.get('user_agent_list')
        self.ua = UserAgent()
        self.ua_type = crawelr.settings.get('RANDOM_UA_TYPE','random')

    @classmethod
    def from_crawler(cls,crawelr):
        return cls(crawelr)

    def process_request(self,request,spider):
        def get_ua():
            return getattr(self.ua, self.ua_type)

        r = get_ua()
        request.headers.setdefault('User-Agent',get_ua())
        #ip代理  西刺免费代理
        # request.mata['proxy'] = 'http://61.135.155.82:443'

class RandomProxyMiddleware(object):
    # 动态设置ip代理
    def process_request(self, request, spider):
        get_ip = GetIP()
        ip= get_ip.get_random_ip()
        request.meta["proxy"] = ip

class JSPageMiddleware(object):
    def __init__(self, crawler):
        super(RandomUserAgentMiddlware, self).__init__()
        browser = webdriver.Chrome(executable_path="D:/Temp/chromedriver.exe")
        super(JSPageMiddleware, self).__init__()
    # 通过chrome请求动态网页
    def process_request(self, request, spider):
        if spider == 'jobbole':
            # browser = webdriver.Chrome(executable_path="D:/Temp/chromedriver.exe")
            spider.browser.get(request.url)
            import time
            time.sleep(3)
            print("访问:{0}".format(request.url))
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source, encoding="utf-8",
                                request=request)

# from pyvirtualdisplay import Display
# display = Display(visible=0, size=(800, 600))
# display.start()
#
# browser = webdriver.Chrome()
# browser.get()
