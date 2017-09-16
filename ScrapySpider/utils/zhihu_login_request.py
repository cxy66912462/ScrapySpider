# encoding: utf-8
#@author: chaoxingyu
#@file: zhihu_login_request.py
#@time: 2017/8/16 10:39

import requests
#cookie读取本地cookie文件赋值给requests
try:
    import cookielib
except:
    import  http.cookiejar as cookielib
import re
import time
from PIL import Image

#不使用requests连接,使用session,长连接,不需要每次request都创建新连接
session = requests.session()
#让session 可以执行save方法
session.cookies = cookielib.LWPCookieJar(filename='cookies.txt')
#先加载cookie
try:
    session.cookies.load(ignore_discard=True)
except:
    print ("cookie未能加载")

#Mozilla/5.0 (Windows NT 6.1; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0
#Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36
#设置请求头,模拟浏览器请求
agent='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'
#agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
header={
    # "HOST":"www.zhihu.com",
    # "Referer": "https://www.zhizhu.com",
    # 'User-Agent': agent
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'HOST': "www.zhihu.com",
    'Referer': "https://www.zhihu.com",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36'
}

def is_login():
    #通过个人中心页面返回状态码来判断是否为登录状态
    index_url = "https://www.zhihu.com/question/56250357/answer/148534773"
    response = session.get(index_url, headers=header, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True

def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=header)
    with open('captcha.gif', 'wb') as f:
        f.write(r.content)
        f.close()
    im = Image.open('captcha.gif')
    im.show()
    im.close()
    captcha = input("please input the captcha\n>")
    return captcha

#使用requests模拟登陆知乎
def get_xsrf():
    response = session.get("https://www.zhihu.com", headers=header)
    # print(response.text)
    text= '<input type="hidden" name="_xsrf" value="55a2d4c8d459aea5bbfb9424df7b77a1"/>'
    match_obj = re.match('.*name="_xsrf" value="(.*?)"', text)
    match_obj2 = re.search('.*name="_xsrf" value="(.*?)"',response.text)
    if match_obj2:
        print(match_obj2.group(1))
        return match_obj2.group(1)
    else:
        return ''

def get_index():
    response = session.get('https://www.zhihu.com', headers=header)
    with open('index_page.html','wb') as f:
        f.write(response.text.encode('utf-8'))
    print("ok")

def zhihu_login(account,password):
    #知乎模拟登录
    if re.match('1\d{10}',account):
        #手机号登录
        print('手机号码登录')
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data ={
            '_xsrf':get_xsrf(),
            'phone_num':account,
            'password':password,
            "captcha": get_captcha()
        }
    else:
        if '@' in account:
            #email登录
            print('手机号码登录')
            post_url = 'https://www.zhihu.com/login/email'
            post_data = {
                "captcha": get_captcha(),
                '_xsrf': get_xsrf(),
                'phone_num': account,
                'password': password
            }
    print(post_data)
    response_text = session.post(post_url, data=post_data, headers=header)
    session.cookies.save()

# get_xsrf()
#zhihu_login("17896063030", "qweasdzxc123")
get_index()