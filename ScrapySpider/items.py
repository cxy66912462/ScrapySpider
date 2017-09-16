# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy,re
from scrapy.loader.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader
from datetime import  datetime
from ScrapySpider.utils.common import extract_num,get_md5
from ScrapySpider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from w3lib.html import remove_tags
from ScrapySpider.models import es_types
from ScrapySpider.models.es_types import ArticleType
from elasticsearch_dsl.connections import connections
import redis

es = connections.create_connection(ArticleType._doc_type.using)
redis_cli = redis.StrictRedis(host='139.199.21.227',password='chaoxingyu')

class ScrapyspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

def add_jobbole(value):
    return value + '-jobbole'

def date_convert(value):
    try:
        value=value.strip().replace("·", "").strip()
        if value == '' :
            create_date = datetime.now().date()
        else:
            create_date = datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.now().date()
        print('时间转换出错', e)
    return create_date

class ArticleItemLoader(ItemLoader):
    # 自定义Loader设置默认list取第一个
    default_output_processor = TakeFirst()

def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums

def remove_comment_tags(value):
    #去掉tag中提取的评论
    if '评论' in value:
        return ''
    else:
        return value

def return_value(value):
    return  value

def gen_suggests(index, info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            # words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter': ["lowercase"]}, body=text)
            # words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter': ["lowercase"]}, body=text)
            print(text)
            # words = es.indices.analyze(index=index,body=text, params={'analyzer':'ik_max_word','filter':'lowercase'})
            words = es.indices.analyze(index=index,body=None,params={'analyzer':'ik_smart','filter':'lowercase','text':text})
            # words = es.indices.analyze(index=index,body=text,analyzer="ik_max_word")
            print(words)
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1])
            new_words = anylyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words), "weight":weight})

    return suggests

def remove_splash(value):
    #去掉工作城市的斜线
    return value.replace("/","")

def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip()!="查看地图"]
    return "".join(addr_list)

class JobBoleArticleItem(scrapy.Item):
    title=scrapy.Field(
        input_processor = MapCompose(add_jobbole)
    )
    create_date=scrapy.Field(
        input_processor = MapCompose(date_convert)
    )
    img_url=scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    url=scrapy.Field()
    url_obj_id = scrapy.Field()
    img_path=scrapy.Field()
    praise_count=scrapy.Field(
        input_processor = MapCompose(get_nums)
    )
    comment_count=scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    collect_count=scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    content=scrapy.Field()
    tags=scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor = Join(',')
    )

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO jobbole_article(title,img_url,url,url_obj_id
            ,praise_count,comment_count,collect_count,content,tags,create_date,create_time
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
        """
        #填充参数
        params =(self['title'], self['img_url'][0], self['url'], self['url_obj_id'], self['praise_count']
                 , self['comment_count'], self['collect_count'],self['content'], self['tags'], self['create_date'])
        return insert_sql,params
    pass

    def save_to_es(self):
        article = ArticleType()
        article.title = self['title']
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"])
        article.img_url = self["img_url"]
        if "img_path" in self:
            article.img_path = self["img_path"]
        article.praise_count = self["praise_count"]
        article.collect_count = self["collect_count"]
        article.comment_count = self["comment_count"]
        article.url = self["url"]
        article.tags = self["tags"]
        article.meta.id = self["url_obj_id"]

        article.suggest = gen_suggests(ArticleType._doc_type.index, ((article.title, 10), (article.tags, 7)))

        article.save()
        redis_cli.incr("jobbole_count")

        return

class ZhihuQuestionItem(scrapy.Item):
    id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comment_num = scrapy.Field()
    guanzhu_num = scrapy.Field()
    click_num = scrapy.Field()
    crawel_time = scrapy.Field()
    crawel_update_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_question(id, topics, url, title, content, answer_num, comment_num,
                guanzhu_num, click_num, crawel_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comment_num=VALUES(comment_num),
            guanzhu_num=VALUES(guanzhu_num), click_num=VALUES(click_num)
        """
        #ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comment_num=VALUES(comment_num),
        #        watch_user_num=VALUES(guanzhu_num), click_num=VALUES(click_num)
        #填充参数
        id = self['id'][0]
        topics = ",".join(self['topics'])
        url = self['url'][0]
        title = "".join(self['title'][0])
        answer_num = extract_num("".join(self['answer_num']))
        if len(self["guanzhu_num"]) == 2:
            guanzhu_num = int(self["guanzhu_num"][0])
            click_num = int(self["guanzhu_num"][1])
        else:
            guanzhu_num = int(self["guanzhu_num"][0])
            click_num = 0
        comment_num = extract_num("".join(self['comment_num']))
        crawel_time = datetime.now().strftime(SQL_DATETIME_FORMAT)
        content= "".join(self['content'])
        params = (id, topics, url, title, content, answer_num, comment_num,
                guanzhu_num, click_num, crawel_time)

        return insert_sql,params
    pass


class ZhihuAnswerItem(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comment_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawel_time = scrapy.Field()
    crawel_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = '''
            INSERT INTO zhihu_answer (id,url,question_id,author_id,content,praise_num,comment_num,create_time 
            ,update_time,crawel_time) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), comment_num=VALUES(comment_num), praise_num=VALUES(praise_num),
            update_time=VALUES(update_time)
        '''
        create_time = datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        crawel_time = self['crawel_time']
        params = (
            self["id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["praise_num"],
            self["comment_num"], create_time, update_time,
            self["crawel_time"]
        )
        return insert_sql,params

class ZhihuAuthorItem(scrapy.Item):
    user_id = scrapy.Field()
    name = scrapy.Field()
    user_type = scrapy.Field()
    url = scrapy.Field()
    avatar_url = scrapy.Field()
    is_org = scrapy.Field()
    is_advertiser = scrapy.Field()
    headline = scrapy.Field()
    follower_count = scrapy.Field()
    url_token = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = '''
            INSERT INTO zhihu_author(user_id,`name`,user_type,url,avatar_url,is_org,is_advertiser
            ,headline,follower_count,url_token,crawl_time )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE headline=VALUES(headline), follower_count=VALUES(follower_count)
            , name=VALUES(name)
        '''
        params = (
            self["user_id"], self["name"], self["user_type"],
            self["url"], self["avatar_url"], self["is_org"],
            self["is_advertiser"], self["headline"],self["follower_count"],self["url_token"]
            ,self["crawl_time"]
        )
        return insert_sql,params

class LagouJobItemLoader(ItemLoader):
    # 自定义Loader设置默认list取第一个
    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item):
    #拉勾网职位信息
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_years = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    tags = scrapy.Field(
        input_processor = Join(",")
    )
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(title, url, url_obj_id, salary, job_city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_name, company_url,
            tags, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc)
        """
        params = (
            self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"],
            self["work_years"], self["degree_need"], self["job_type"],
            self["publish_time"], self["job_advantage"], self["job_desc"],
            self["job_addr"], self["company_name"], self["company_url"],
            self["job_addr"], self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
        # insert_sql = """
        # insert into lagou_job(title, url, url_obj_id, salary, job_city, work_years, degree_need,
        # job_type, publish_time, job_advantage, job_desc, job_addr, company_name, company_url,
        # tags, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        # """
        # params = ('1','1','1','1','1','1','1','1','1','1','1','1','1','1','1','1')
        return insert_sql, params
