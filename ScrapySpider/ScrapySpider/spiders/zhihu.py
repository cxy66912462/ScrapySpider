# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time
from datetime import  datetime
from PIL import Image
import requests
from urllib import parse
from scrapy.loader import ItemLoader
from ScrapySpider.items import ZhihuAnswerItem,ZhihuQuestionItem,ZhihuAuthorItem
from ScrapySpider.settings import SQL_DATETIME_FORMAT,SQL_DATE_FORMAT


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}'

    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'HOST': "www.zhihu.com",
        'Referer': "https://www.zhihu.com",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36'
    }

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    def parse(self, response):
        # 提取html所有的url,并跟踪这些url进一步爬取
        # 如果url格式匹配/question/xxxx 就进行下载,进行解析函数
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.search('(.*zhihu.com/question/(\d+))(/|$).*', url)
            # match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果是question页面,进行下载,并调用callback函数进行提取item
                request_url = match_obj.group(1)
                question_id = int(match_obj.group(2))
                yield scrapy.Request(request_url, meta={'question_id': question_id, 'request_url': request_url},
                                     headers=self.header, callback=self.parse_question)
            else:
                # 如果不是question页面,继续执行parse函数提取url
                yield scrapy.Request(url, headers=self.header, callback=self.parse)

    def parse_question(self, response):
        # 处理question页面,从页面中提取出question item
        print(response.url)
        if 'QuestionHeader-title' in response.text:
            question_id = response.meta.get('question_id')
            # 处理新版本
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css('title', 'h1.QuestionHeader-title::text')
            item_loader.add_css('content', '.QuestionHeader-detail')
            item_loader.add_value('url', response.url)
            item_loader.add_value('id', question_id)
            item_loader.add_css('answer_num', '.List-headerText span::text')
            item_loader.add_css('comment_num', '.QuestionHeader-Comment button::text')
            item_loader.add_css('guanzhu_num', '.NumberBoard-value::text')
            item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')

            question_item = item_loader.load_item()
        else:
            # 处理老
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            # item_loader.add_css("title", ".zh-question-title h2 a::text")
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("id", question_id)
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comment_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            # item_loader.add_css("watch_user_num", "#zh-question-side-header-wrap::text")
            item_loader.add_xpath("guanzhu_num",
                                  "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

            question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.header,
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        # 处理answer,提取answer item
        answer_json = json.loads(response.text)
        is_end = answer_json['paging']['is_end']
        totals_answer = answer_json['paging']['totals']
        next_url = answer_json['paging']['next']
        # 提取answer数据到item
        for answer in answer_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['id'] = answer['id']
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comment_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawel_time"] = datetime.now().strftime(SQL_DATETIME_FORMAT)

            author_item = ZhihuAuthorItem()
            author = answer['author']
            user_id = author['id'] if 'id' in author else None
            if user_id is not None:
                author_item['user_id'] = user_id
                author_item['name'] = author['name']
                author_item['user_type'] =author['user_type']
                author_item['url'] =author['url']
                author_item['avatar_url'] =author['avatar_url']
                author_item['is_org'] =author['is_org']
                author_item['is_advertiser'] =author['is_advertiser']
                author_item['headline'] =author['headline']
                author_item['follower_count'] =author['follower_count'] if 'follower_count' in author else 0
                author_item['url_token'] =author['url_token']
                print(datetime.now().strftime(SQL_DATETIME_FORMAT))
                author_item['crawl_time'] = datetime.now().strftime(SQL_DATETIME_FORMAT)
                yield author_item

            yield answer_item

        if not is_end:
            # 如果is_end =false 说明还有数据,继续请求answer
            yield scrapy.Request(next_url, headers=self.header, callback=self.parse_answer)
            pass
        pass

    # 1.爬取知乎第一步,登录
    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.header, callback=self.login)]

    def login(self, response):
        print('手机号码登录')
        post_data = {
            '_xsrf': self.get_xsrf(response.text),
            'phone_num': '17896063030',
            'password': 'qweasdzxc123',
            'captcha': ''
        }

        # 重点技巧
        t = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
        yield scrapy.Request(captcha_url, headers=self.header, meta={'post_data': post_data},
                             callback=self.login_after_captcha)

    def get_xsrf(self, response_text):
        match_obj2 = re.search('.*name="_xsrf" value="(.*?)"', response_text)
        if match_obj2:
            return match_obj2.group(1)
        else:
            return ''

    def login_after_captcha(self, response):
        with open('captcha.gif', 'wb') as f:
            f.write(response.body)
            f.close()
        im = Image.open('captcha.gif')
        im.show()
        im.close()
        captcha = input("please input the captcha\n>")
        post_data = response.meta.get('post_data', {})
        post_data['captcha'] = captcha
        return [scrapy.FormRequest(
            url='https://www.zhihu.com/login/phone_num',
            formdata=post_data,
            headers=self.header,
            callback=self.check_login
        )]

    def check_login(self, response):
        # 验证是否登录成功
        text_json = json.loads(response.text)
        print('验证是否登录', text_json)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.header)

        pass
