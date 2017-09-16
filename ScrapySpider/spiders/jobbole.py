
import scrapy,re
from scrapy.http import Request
from urllib import parse
from ScrapySpider.items import JobBoleArticleItem,ArticleItemLoader
from ScrapySpider.utils.common import get_md5
from datetime import datetime
from scrapy.loader import ItemLoader
import time
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']
    # start_urls = ['http://blog.jobbole.com/112127/']

    # def __init__(self):
    #     self.browser = webdriver.Chrome(executable_path="D:/Temp/chromedriver.exe")
    #     super(JobboleSpider, self).__init__()
    #     dispatcher.connect(self.spider_closed, signals.spider_closed)
    #
    # def spider_closed(self, spider):
    #     #当爬虫退出的时候关闭chrome
    #     print ("spider closed")
    #     self.browser.quit()

    # 收集伯乐在线所有404的url以及404页面数
    handle_httpstatus_list = [404]

    def __init__(self, **kwargs):
        self.fail_urls = []
        dispatcher.connect(self.handle_spider_closed, signals.spider_closed)

    def handle_spider_closed(self, spider, reason):
        self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))

    '''
    1.获取文章列表页的文章url
    2.获取下一页url交给scrapy进行下载
    '''
    def parse(self, response):
        #收集404页面url和数量
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")

        # 解析列表页中的所有文章url并交给scrapy下载后进行解析
        # post_urls=response.css('#archive .floated-thumb .post-thumb a::attr(href)').extract()
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')
        for post_node in post_nodes:
            img_url = post_node.css('img::attr(src)').extract_first("")
            post_url = post_node.css('::attr(href)').extract_first("")
            print(post_url)
            # 加上yield scrapy就会下载并解析
            yield Request(url=parse.urljoin(response.url, post_url), meta={'img_url': img_url},
                          callback=self.parse_detail)

        # 提取下一页url并交给scrapy下载
        next_urls = response.css('.next.page-numbers::attr(href)').extract_first('')
        if next_urls:
            print('*******************************************************')
            yield Request(url=parse.urljoin(response.url, next_urls), callback=self.parse)

    # 使用xpath和css语法练习
    def parse_detail(self, response):
        # 使用item
        # article_item = JobBoleArticleItem()
        # title = response.css('.entry-header h1::text').extract()[0]
        # create_date = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·", "").strip()
        # praise_count = response.css('.vote-post-up h10::text').extract()[0]
        # if len(praise_count) == 0:
        #     praise_count = 0
        # else:
        #     praise_count = praise_count[0]
        # match_str = '.*(\d+).*'
        # collect_count = response.css('.bookmark-btn i::text').extract()
        # if len(collect_count) == 0:
        #     collect_count = 0
        # else:
        #     collect_count = collect_count[0]
        # comment_count = response.css('a[href="#article-comment"] span i::text').extract()
        # if len(comment_count) == 0:
        #     comment_count = 0
        # else:
        #     comment_count = comment_count[0]
        # tag_list = response.css('.entry-meta-hide-on-mobile a::text').extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ','.join(tag_list)
        # img_url = response.meta.get('img_url','')
        # content = response.css('div.entry').extract()[0]
        # article_item['title']=title
        # article_item['url']=response.url
        # try:
        #     create_date = datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date=datetime.now().date()
        #     print('时间转换出错',e)
        # article_item['create_date']=create_date
        # article_item['img_url']=[img_url]
        # article_item['url_obj_id']= get_md5(response.url)
        # article_item['comment_count'] = comment_count
        # article_item['collect_count']=collect_count
        # article_item['praise_count']=praise_count
        # article_item['tags']=tags
        # article_item['content']=content

        # 通过ItemLoader加载item
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css('title', '.entry-header h1::text')
        item_loader.add_value('url', response.url)
        item_loader.add_value("url_obj_id", get_md5(response.url))
        t = response.css('p.entry-meta-hide-on-mobile::text').extract()[0].strip().replace("·", "").strip()
        print(t)
        # item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("create_date", [t])
        img_url = response.meta.get("img_url", "")  # 文章封面图
        item_loader.add_value("img_url", [img_url])
        item_loader.add_css("praise_count", ".vote-post-up h10::text")
        item_loader.add_css("comment_count", "a[href='#article-comment'] span::text")
        item_loader.add_css("collect_count", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        print('开始======================================')
        article_item = item_loader.load_item()
        print('结束========================================')
        # 这里yield article_item会传递到pipelines里面
        yield article_item

        # css提取文章具体字段信息
        # title_css = response.css('.entry-header h1::text').extract()[0]
        # create_time_css = response.css('p.entry-meta-hide-on-mobile::text').extract()[0].strip().replace('·','')
        # praise_count_css = response.css('.vote-post-up h10::text').extract()[0]
        # if len(praise_count_css) == 0:
        #     praise_count_css = 0
        # else:
        #     praise_count_css = praise_count_css[0]
        # match_str = '.*(\d+).*'
        # collect_count_css = response.css('.bookmark-btn i::text').extract()
        # if len(collect_count_css) == 0:
        #     collect_count_css = 0
        # else:
        #     collect_count_css = collect_count_css[0]
        # comment_count_css = response.css('a[href="#article-comment"] span i::text').extract()
        # if len(comment_count_css) == 0:
        #     comment_count_css = 0
        # else:
        #     comment_count_css = comment_count_css[0]
        #
        # tag_list_css = response.css('.entry-meta-hide-on-mobile a::text').extract()
        # tags_css = ','.join(tag_list_css)
        # img_url = response.meta.get('img_url','')
        # print('css===============================================')
        # print('标题:', title)
        # print('发布时间:', create_date)
        # print('标签:', tags)
        # print('收藏:%s | 点赞:%s | 评论:%s' % (collect_count, praise_count, comment_count))

        # xpath提取文章具体字段信息
        # title1=response.xpath('/html/body/div[1]/div[3]/div[1]/div[1]/h1')
        # title2=response.xpath('//*[@id="post-112127"]/div[1]/h1/text()')
        # title3=response.xpath('//div[@class="entry-header"]/h1/text()')
        # title=response.xpath("//div[@class='entry-header']/h1/text()").extract()[0]
        #  create_time=response.xpath('//*[@id="post-112127"]/div[2]/p/text()[1]').extract()[0].strip().replace('·','').strip()
        # praise_count=response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract()[0]
        # collect_count=re.match(match_str, response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract()[0]).group(1)
        # try:
        #     comment_count=re.match(match_str,response.xpath('//a[@href="#article-comment"]/span/text()').extract()[0]).group(1)
        # except Exception as e:
        #     comment_count =0
        # content= response.xpath('//div[@class="entry"]').extract()[0]
        # tag_list = response.xpath('//*[@id="post-112127"]/div[2]/p/a/text()').extract()
        # tag_list=[element for element in tag_list if not element.endswith('评论')]
        # tags=','.join(tag_list)
        # if match_str:
        #     collect_count=re.match(match_str,collect_count)
        # print('标题:',title)
        # print('发布时间:',create_time)
        # print('标签:',tags)
        # print('收藏:%s | 点赞:%s | 评论:%s' % (collect_count,praise_count,comment_count))


        pass
