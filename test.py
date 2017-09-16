# encoding: utf-8
#@author: chaoxingyu
#@file: test.py
#@time: 2017/9/4 14:29
import urllib.request

def url_t():
    for i in range(20):
        response = urllib.request.urlopen('https://www.lagou.com/zhaopin/iOS/')
        print(response.code)

if __name__ == '__main__':
    url_t()
    print(123)