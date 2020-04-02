#!/usr/bin/env python3
import sys
import argparse
from typing import Tuple, List, Set
from multiprocessing import Pool
import os
import re
from shlex import quote

from bs4 import BeautifulSoup

from util import execute


from convert_to_mp3 import mp3_to_mp4
from pycookiecheat import chrome_cookies
import requests


URL_ACADEMY_BASE = "https://investmentpunk-academy.mykajabi.com"
OUTPUT_DIR_BASE = "/home/kmille/projects/investment-academy-crawler/videos"
POOL_SIZE = 10


cookies = chrome_cookies(URL_ACADEMY_BASE, browser='chromium')
assert cookies is not {}

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0"})
session.cookies.update(cookies)


def get_all_category_ids_for_ueberkategorie(url: str) -> Set[str]:
    # url: https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/1779914
    # returns { '1804058' , ... }
    resp = session.get(url)
    assert resp.status_code == 200
    bs = BeautifulSoup(resp.text, 'html.parser')
    links_html = bs.findAll("div", {'class': 'syllabus__item'}, id=re.compile("^post-"))
    links = [link.find("a")['href'] for link in links_html]
    category_ids = set([get_category_id_of_episode_url(link) for link in links])
    print(f"{category_ids=} ({len(category_ids)})")
    return category_ids


def get_category_id_of_episode_url(url: str) -> str:
    url = url.strip()
    regex = re.search(r'/products/investment-punk-academy/categories/([a-f0-9]+)/posts/', url)
    if regex:
        return regex.group(1)
    else:
        raise Exception("Could not find category_id")


def download_episode(args: Tuple[str, str, str]) -> str:
    category_name, episode_name, download_link = args
    print(f"Downloading {episode_name}")
    output_dir_abs = os.path.join(OUTPUT_DIR_BASE, category_name)
    os.makedirs(output_dir_abs, exist_ok=True)
    file_name = episode_name.replace(":", " -").replace("?", "").strip() + ".mp4"
    output_file_abs = os.path.join(output_dir_abs, file_name)
    if os.path.exists(output_file_abs):
        print(f"Skipping {output_file_abs} - already there")
        return None
    cmd = f"""curl -s -A "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0" {quote(download_link)} -o {quote(output_file_abs)}"""
    execute(cmd, scharf=True)
    print(f"Download finished '{output_file_abs}'")
    return output_dir_abs


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


def get_episode_download_url(url_path: str) -> str:
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


def download_all_episodes_for_category(category_id: str):
    category_name, episodes_data = get_episodes_for_category(category_id)
    tasks = []
    for episode_name, url in episodes_data:
        download_link = get_episode_download_url(url)
        tasks.append((category_name, episode_name, download_link))
    p = Pool(POOL_SIZE)
    output_dirs = p.map(download_episode, tasks)
    print("Download finished")
    for output_dir in output_dirs:
        if output_dir:
            mp3_to_mp4(output_dir)


assert "1768076" == get_category_id_of_episode_url("https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/1768076/posts/6495672")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download videos from Investment Punk Academy')
    parser.add_argument('--video-url', help='Link to a video. Downloads all videos of the series, e.g. https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/1804058/posts/5935041')
    parser.add_argument('--category-url', help='Link to a category. Downloads all videos of _all_ series, e.g. https://investmentpunk-academy.mykajabi.com/products/investment-punk-academy/categories/1779914')

    args = parser.parse_args()
    if args.video_url:
        category_id = get_category_id_of_episode_url(args.video_url)
        download_all_episodes_for_category(category_id)

    if args.category_url:
        category_ids = get_all_category_ids_for_ueberkategorie(args.category_url)
        for category_id in category_id:
            download_all_episodes_for_category(category_id)
