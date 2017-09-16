# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
# 与open最大区别在于文件编码,帮我们做了
import codecs
import json
from scrapy.exporters import JsonItemExporter
import MySQLdb
from twisted.enterprise import adbapi
import MySQLdb.cursors
from ScrapySpider.models.es_types import ArticleType
from w3lib.html import remove_tags

class ScrapyspiderPipeline(object):
    def process_item(self, item, spider):
        return item

class JsonWithEncodingPipeline(object):
    #自定义json文件导出
    def __init__(self):
        self.file=codecs.open('article.json','w',encoding='utf-8')
    def process_item(self, item, spider):
        lines = json.dumps(dict(item),ensure_ascii=False)+'\n'
        self.file.write(lines)
        return item
    def spider_closed(self,spider):
        self.file.close()


class JsonExporterPipeline(object):
    #调用scrapy提供的exporter导出json文件
    def __init__(self):
        self.file = open('article_exporter.json','wb')
        self.exporter = JsonItemExporter(self.file,encoding='utf-8',ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect('localhost', 'root', 'root', 'scrapy_db', charset="utf8", use_unicode=True)
        self.cursor= self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            INSERT INTO jobbole_article(title,img_url,url,url_obj_id
              ,praise_count,comment_count,collect_count,content,tags,create_date,create_time
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
        """
        self.cursor.execute(insert_sql, (item['title'],item['img_url'][0],item['url'],item['url_obj_id']
                                         ,item['praise_count'],item['comment_count'],item['collect_count'],item['content']
                                         , item['tags'], item['create_date']))
        self.conn.commit()
        return item

class MysqlTwistedPipeline(object):

    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):
        dbparams = dict(
            host = settings['MYSQL_HOST'],
            database=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset = 'utf8',
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True
        )
        dbpool = adbapi.ConnectionPool('MySQLdb',**dbparams)
        return cls(dbpool)

    # 使用twisted将mysql插入变成异步执行
    def process_item(self, item, spider):
        # 第一个参数方法,将这个方法变成异步执行
        query=self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常
        return item

    # 执行具体插入操作
    def do_insert(self,cursor,item):
        #根据不同的item,构建不同的sql语句
        #技巧:将sql语句放到item的方法去构建
        insert_sql,params = item.get_insert_sql()
        print(insert_sql)
        print(params)
        cursor.execute(insert_sql, params)

    def handle_error(self,failure,item,spider):
        #处理异步插入异常
        print('异步插入异常:',failure)
        # exit(0)




class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'img_url' in item:
            for ok,value in results:
                image_file_path = value['path']
            item['img_path']=image_file_path

        return item

class ElasticsearchPipeline(object):
    #将数据写入es  elasticsearch-dsl
    def process_item(self, item, spider):
        #将item转成es的数据
        item.save_to_es()
        pass
