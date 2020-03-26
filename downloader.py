#!/usr/bin/env python3
from subprocess import Popen, PIPE
from typing import Tuple, List
import os
import re
from shlex import quote

from bs4 import BeautifulSoup



#with open("categories.html") as f:
#    bs = BeautifulSoup(f.read(), 'html.parser')
#
#kategorie = bs.find("h5", {"class": "syllabus__heading"}).text.strip()
#bs.find_all("div", {"class":"syllabus__item"})

#with open("posts.html") as f:
#    html = f.read()
#ids = re.search(r'_wq.push\({"([a-z0-9]+)"', html).group(1)

#with open("videos.html") as f:
#    html = f.read()
#re.findall(r'https://embed-ssl.wistia.com/deliveries/[a-f0-9]+', html)

from pycookiecheat import chrome_cookies
import requests




cookies = chrome_cookies("https://investmentpunk-academy.mykajabi.com", browser='chromium')

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0"})
session.cookies.update(cookies)


def execute(cmd: str, scharf: bool = False):
    #cmd = quote(cmd)
    print(f"{cmd}")
    if scharf:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        p.wait()
        if p.returncode != 0:
            print(p.communicate())


def parse_playlist(categorie: str, post: str) -> Tuple[str, str, List[str]]:
    #resp = session.get("https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/1767837/posts/5929586")
    resp = session.get(f"https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/{categorie}/posts/{post}")
    assert resp.status_code == 200
    bs = BeautifulSoup(resp.text, 'html.parser')
    chapter_name = bs.find("h5").text
    lections = [l.text for l in bs.find_all("p", {"class": "track__title"})]
    regex = re.search(r'_wq.push\({"([a-z0-9]+)"', resp.text)
    if regex:
        chapter_id = regex.group(1)
    else:
        raise Exception("Regex failed")
    print(f"Got: {chapter_name=} {chapter_id} with {lections=}")
    return chapter_name, chapter_id, lections


def get_download_lings_for_playlist(chapter_id: str) -> List[str]:
    resp = session.get(f"https://fast.wistia.com/embed/medias/{chapter_id}.json?callback=wistiajson1")
    assert resp.status_code == 200
    download_links = re.findall(r'https://embed-ssl.wistia.com/deliveries/[a-f0-9]+', resp.text)
    print(f"Found {len(download_links)} download links")
    return download_links


def download_playlist(download_links: List[str], chapter_name: str, lections: List[str]):
    for i, link in enumerate(download_links):
        file_name = f"{lections[i]}.mkv"
        execute(f"mkdir -p {quote(chapter_name)}")
        out_abs = f"{chapter_name}/{file_name}"
        if os.path.exists(out_abs):
            print(f"File exists. Skipping '{out_abs}")
            continue
        cmd = f"""curl -A "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0" -s {link} -o '{chapter_name}/{file_name}'"""
        execute(cmd)
        exit()


if __name__ == '__main__':
    categorie = "1767837"
    posts = "5929586"
    chapter_name, chapter_id, lections = parse_playlist(categorie, posts)
    download_links = get_download_lings_for_playlist(chapter_id)
    download_playlist(download_links, chapter_name, lections)
