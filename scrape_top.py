# coding:utf-8


import sys
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import mechanize


TOP_URL = "https://wellness.sfc.keio.ac.jp/v3/"


def main():
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open(TOP_URL)
    html = urllib2.urlopen(TOP_URL)
    soup = BeautifulSoup(html, "html.parser")

    """2週間分の予約空き授業を全て表示"""
    urls = soup.findAll("ul", attrs={"class": "cool"})[-1]
    for link in urls.findAll("a"):
        if "Hidden" in link.get("href"):
            free_url = link.get("href")
    
    free_url = TOP_URL + free_url
    free_res = br.open(free_url)
    free_html = free_res.read()
    free_soup = BeautifulSoup(free_html, "html.parser")# 2週間分のsoup

    table = free_soup.findAll("table",{"class":"cool"})[0]
    rows = table.findAll("tr")
    
    all_text = []
    for row in rows:
        for cell in row.findAll(['td', 'th']):
            text = cell.get_text()
            all_text.append(text)
    
    group_by = 6
    group_text = [all_text[i:i + group_by] for i in range(0, len(all_text), group_by)]
    
    day    = [i[0] for i in group_text]
    period = [i[1] for i in group_text]
    name   = [i[2] for i in group_text]
    tname  = [i[3] for i in group_text]
    free   = [i[5] for i in group_text]
    
    
    df = pd.DataFrame({
            'day' : day[1:],
            'period' : period[1:],
            'name' : name[1:],
            'tname' :tname[1:],
            'free' : free[1:]
        })
    
    return df


if __name__ == "__main__":
    df = main()
    print df
