# coding:utf-8


import scrape_top
import os
import re
import mechanize
import ConfigParser
from bs4 import BeautifulSoup
import pandas as pd
import sys
reload(sys)  
sys.setdefaultencoding('utf8')


TOP_URL = "https://wellness.sfc.keio.ac.jp/v3/"


def chack_event(event, dayofweeks, period):
    """

    自分の希望する授業に空きがあるかチェックする
    空きがなければexit

    """
    df = scrape_top.main()
    event = event.decode("utf-8")
    dayofweeks = dayofweeks.decode("utf-8")
    period = period.decode("utf-8")
    df["dayofweeks"] = [pickupdow(i) for i in df["day"]]# 曜日の列を作成
    
    df = df[df["name"] == event]
    if dayofweeks:
        df = df[df["dayofweeks"] == dayofweeks]
    if period:
        df = df[df["period"] == period]

    if df.empty:
        print("空きがないか授業が存在しません(曜日や時限を確認してください)")
        sys.exit(1)
    print df
    return df


def login(name, password):
    """
    
    ログインする

    input:id,password
    output:ログイン後のbrowserとhtml
    
    """
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open(TOP_URL)
    br.select_form(nr=0)
    br.form['login'] = name
    br.form['password'] = password
    res = br.submit()
    res_html = res.read()
    soup = BeautifulSoup(res_html, "html.parser")
    res_error = soup.find("em", attrs={"class": "error"}).string

    if res_error is u"login名またはパスワードが異なります．":
        print(res_error)
        sys.exit(1)
        return False
    else:
        print(res_error)
        return br, res_html


def get_status(br, res_html, event):
    """

    予約したい授業の予約ボタンを取得する

    input:ログイン後のbrowser, html，予約したい科目
    output:browser, テーブルから取得した予約したい科目のrows(複数)，現在のurl
    
    """
    top_soup = BeautifulSoup(res_html, "html.parser")
    menu = top_soup.findAll("ul", attrs={"class":"menu"})[0]# メニューの抽出

    """メニューの予約進む"""
    for link in menu.findAll("a"):
        if "reserve" in link.get("href"):
            yoyaku_url = link.get("href")# 予約のurlを取得
    yoyaku_url = TOP_URL[:-4] + yoyaku_url
    yoyaku_res = br.open(yoyaku_url)
    yoyaku_html = yoyaku_res.read()
    yoyaku_soup = BeautifulSoup(yoyaku_html, "html.parser")# 予約画面のsoup

    """2週間分の予約空き授業を全て表示"""
    urls = yoyaku_soup.findAll("ul", attrs={"class": "cool"})[0]
    for link in urls.findAll("a"):
        if "reserve" in link.get("href"):
            free_url = link.get("href")
    free_url = "/".join(yoyaku_url.split("/")[:-1]) + "/"  + free_url
    free_res = br.open(free_url)
    free_html = free_res.read()
    free_soup = BeautifulSoup(free_html, "html.parser")# 2週間分のsoup

    """予約テーブルから抽出"""
    table = free_soup.findAll("table", attrs={"class": "cool"})[0]
    rows = table.findAll("tr")
    event_rows = []
    for row in rows:
        for cell in row.findAll(['td', 'th']):
            text = cell.get_text()
            matchOB = re.search(event.decode("utf-8") , text)
            if matchOB:
                event_rows.append(row)
    return br, event_rows, free_url


def register(br, event_row, free_url):
    """

    予約する
    
    input:getstatus()後のbrowser，テーブルから取得した予約したい科目のrow(一つ)，現在のurl
    
    """
    reserve_url = event_row.find("a", attrs={"class": "reserve"}).get("href")
    target_url = "/".join(free_url.split("/")[:-1]) + "/" + reserve_url
    res = br.open(target_url.decode("utf-8"))
    br.select_form(nr=1)# 予約確認ボタンを選択
    res = br.submit()
    res_html = res.read()
    soup = BeautifulSoup(res_html, "html.parser")

    res_error = soup.findAll("p", attrs={"class": "error"})[0].text
    res_error = res_error.strip()

    if res_error == u"同じ週に予約し出席(欠席)できるのは2コマまでです．":
        print(res_error)
        return False
    elif res_error == u"すでに予約済みです．":
        print(res_error)
        return False
    else:
        br.select_form(nr=1)
        br.submit()# 予約確定
        print("予約しました")


def pickupdow(day):
    ex = "7月 4日(火)"
    dow = day[-2]
    return dow


if __name__== '__main__':
    # config.txtの読み込み
    config = ConfigParser.SafeConfigParser()
    conf = os.path.join(os.path.dirname(__file__),'config.ini')
    config.read([os.path.expanduser(conf)])
    name = config.get('config', 'name')
    pwd = config.get('config', 'password')
    event = config.get('config', 'event')
    dayofweeks = config.get('config', 'day_of_week')
    period = config.get('config', 'period')
    
    # 自分が予約したい授業が空いてるか確認
    freedf = chack_event(event, dayofweeks, period)

    # ログイン
    br, res_html = login(name, pwd)
    # 予約ボタンの取得
    br, event_rows, free_url = get_status(br, res_html, event)

    # 全予約ボタンから空いてる授業のみ選択
    #event_rows = select_class(freedf, event_rows)

    # 予約
    #複数空きがあればループする
    for event_row in event_rows:
        register(br, event_row, free_url)
