# encoding: utf-8
#@author: chaoxingyu
#@file: test.py
#@time: 2017/9/4 13:57

import requests
import urllib.request


def test():
    response = urllib.request.urlopen('http://python.org/')
    html = response.read()
    print(html)


if __name__ == '__main__':
    print('123')
    response = urllib.request.urlopen(new_url)
    if response.getcode() != 200:
        print('url:%s 响应失败' % new_url)