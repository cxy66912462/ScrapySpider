# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from urllib import parse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ScrapySpider.items import LagouJobItem,LagouJobItemLoader
from datetime import datetime
from ScrapySpider.utils.common import get_md5

class Lagou2Spider(scrapy.Spider):
    name = 'lagou2'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    # 收集拉勾所有302的url以及302页面数
    # handle_httpstatus_list = [302]

    # def __init__(self, **kwargs):
    #     self.redirect_urls = []
    #     dispatcher.connect(self.handle_spider_closed, signals.spider_closed)
    #
    # def handle_spider_closed(self, spider, reason):
    #     self.crawler.stats.set_value("redirect_urls", ",".join(self.fail_urls))


    def parse(self, response):
        # 收集302页面url和数量
        # if response.status == 302:
        #     self.fail_urls.append(response.url)
        #     self.crawler.stats.inc_value("failed_url")
        menu_box_list = response.css('div.menu_box')
        for menu_box in menu_box_list:
            job_url_list = menu_box.css('.menu_main .category-list')
            for job_url in job_url_list:
                category_url = job_url.css('a::attr(href)').extract_first("")
                yield Request(url=parse.urljoin(response.url, category_url), callback=self.parse_category)
            job_url_list2 = menu_box.css('menu_sub dl dd ')
            for job_url in job_url_list2:
                category_url = job_url.css('::attr(href)').extract_first("")
                yield Request(url=parse.urljoin(response.url, category_url), callback=self.parse_category)
        pass


    def parse_category(self,response):
        job_url_list = response.css('#s_position_list ul li')
        for job_url in job_url_list:
            url = job_url.css('div.p_top a::attr(href)').extract_first('')
            yield Request(url=parse.urljoin(response.url, url), callback=self.parse_job)

        next_url_node = response.css('.pager_container a')[-1:]
        if '下一页' in next_url_node.css('::text').extract_first():
            next_url = next_url_node.css('::attr(href)').extract_first()
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse_category)

    def parse_job(self, response):
        # 解析拉勾网的职位
        print(response.url)
        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", ".job-name::attr(title)")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("salary", ".job_request .salary::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")

        item_loader.add_css("tags", '.position-label li::text')
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")
        item_loader.add_css("company_name", "#job_company dt a img::attr(alt)")
        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_value("crawl_time", datetime.now())

        job_item = item_loader.load_item()
        job_item = item_loader.load_item()

        return job_item