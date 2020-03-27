#!/usr/bin/env python3
import sys
from typing import Tuple, List
import os
import re
from shlex import quote

from bs4 import BeautifulSoup

from util import execute

from pycookiecheat import chrome_cookies
import requests


URL_ACADEMY_BASE = "https://investmentpunk-academy.mykajabi.com"
OUTPUT_DIR_BASE = "/home/kmille/projects/investment-academy-crawler/videos"


cookies = chrome_cookies(URL_ACADEMY_BASE, browser='chromium')
assert cookies is not {}

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0"})
session.cookies.update(cookies)


def get_category_id_of_episode_url(url: str) -> str:
    url = url.strip()
    regex = re.search(r'https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/([a-f0-9]+)/posts/', url)
    if regex:
        return regex.group(1)
    else:
        raise Exception("Could not find category_id")


def download_episode(category_name: str, episode_name: str, download_link: str):
    print(f"Downloading {episode_name}")
    output_dir_abs = os.path.join(OUTPUT_DIR_BASE, category_name)
    if not os.path.exists(output_dir_abs):
        os.makedirs(output_dir_abs)
    file_name = episode_name + ".mp4"
    output_file_abs = os.path.join(output_dir_abs, file_name)
    if os.path.exists(output_file_abs):
        print(f"Skipping {output_file_abs} - already there")
        return
    cmd = f"""curl -A "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0" {quote(download_link)} -o {quote(output_file_abs)}"""
    execute(cmd, scharf=True)


def get_episodes_for_category(category_id: str) -> Tuple[str, List[Tuple[str, str]]]:
    episodes: List[Tuple[str, str]] = []
    for page in range(1, 1000):
        resp = session.get(f"{URL_ACADEMY_BASE}/products/investment-punk-academy/categories/{category_id}?page={page}")
        assert resp.status_code == 200
        bs = BeautifulSoup(resp.text, 'html.parser')
        category_name = bs.find("h5", {"class": "syllabus__heading"}).text.strip()
        episodes_meta = bs.findAll("div", {"class": "syllabus__item"})
        if not episodes_meta:
            return category_name, episodes
        print(f"Got {len(episodes_meta)} episodes on page {page}")
        for episode_meta in episodes_meta:
            name = episode_meta.find("p", {"class": "syllabus__title"}).text
            url = episode_meta.find("a")['href']
            episodes.append((name, url))
    return category_name, episodes


def get_episode_download_url(url_path: str):
    resp = session.get(f"{URL_ACADEMY_BASE}{url_path}")
    assert resp.status_code == 200
    regex = re.search(r'_wq.push\({"([a-z0-9]+)"', resp.text)
    if regex:
        chapter_id = regex.group(1)
    else:
        raise Exception("Regex failed")
    resp = session.get(f"https://fast.wistia.com/embed/medias/{chapter_id}.json?callback=wistiajson1")
    assert resp.status_code == 200
    still_shit = re.search(r'height":720(.+?)\.bin', resp.text.replace("\n", "")).group()
    download_url = re.search(r'https://embed-ssl.wistia.com/deliveries/[a-f0-9]+', still_shit).group()
    return download_url


def download_all_episodes_of_category(category_id: str):
    category_name, episodes_data = get_episodes_for_category(category_id)
    for episode_name, url in episodes_data:
        download_link = get_episode_download_url(url)
        download_episode(category_name, episode_name, download_link)

    
assert "1768076" == get_category_id_of_episode_url("https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/1768076/posts/6495672")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(f"{sys.argv[0]} <url of a video>")
        sys.exit(1)
    category_id = get_category_id_of_episode_url(sys.argv[1])
    #download_all_episodes_of_category("1767837")
    download_all_episodes_of_category(category_id)
