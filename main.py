# encoding: utf-8
#@author: chaoxingyu
#@file: main.py
#@time: 2017/8/9 17:03

from scrapy.cmdline import execute
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy','crawl','jobbole'])
#execute(["scrapy", "crawl", "zhihu"])
# execute(["scrapy", "crawl", "lagou2"])
# execute(["scrapy", "crawl", "lagou"])