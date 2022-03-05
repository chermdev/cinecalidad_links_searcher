from typing import List
from dataclasses import dataclass
from difflib import SequenceMatcher
from configparser import ConfigParser
from src.exceptions import *
import os
import bs4
import requests
import urllib.parse
import urllib.request

config = ConfigParser()
config.read('config.ini')


@dataclass
class MovieObj:
    title: str
    duration: str
    categories: list
    description: str
    url: str
    coincidence: float

    @property
    def download_options(self):
        if not getattr(self, '_download_options', None):
            self._download_options = _get_download_links_from_movie_page(
                self.url)
        return self._download_options

    @download_options.setter
    def download_options(self, val):
        self._download_options = val

    def get_download_link(self, server='torrent'):
        servers = {}
        for download_opt in self.download_options:
            servers[download_opt.name] = download_opt.link

        if server not in servers:
            raise DownloadServerNotFound(
                f"Not found a download server for: {server}")

        return servers[server]


def _encode_search_value(value):
    search = urllib.parse.quote(value)
    search_txt = search.lower().replace("%20", "+")
    return search_txt


def _get_html_from_url(url, html_save_path):

    save_html = (True if 'True' in config['config']['save_htmls'] else False)
    replace_html = (
        True if 'True' in config['config']['replace_htmls'] else False)

    if save_html:
        if not replace_html:
            if os.path.exists(html_save_path):
                with open(html_save_path, "r", encoding="utf-8") as f:
                    html_code = f.read()
                    return html_code
        opener = urllib.request.build_opener()
        opener.addheaders = [("User-Agent",
                              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36")]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url.replace(" ", "%20"), html_save_path)
        with open(html_save_path, "r", encoding="utf-8") as f:
            html_code = f.read()
            return html_code
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
        }
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise Exception(res.status_code, res.reason)
        return res.text


def _get_search_page_html(movie_search):
    search_page_html_path = config['path']['search_page_html_path']
    host = config['config']['host']
    search_url = "/?s="
    search_txt = _encode_search_value(movie_search)
    url = host + search_url + search_txt
    return _get_html_from_url(url,
                              search_page_html_path)


def _get_movie_objs(html_code, search_movie) -> List[MovieObj]:
    soup = bs4.BeautifulSoup(html_code, features="lxml")
    articles = soup.find_all("article")
    movies = []
    for article in articles:
        movie_title = (
            article.find("header").find("h2").contents[0]
            if len(article.find("header").find("h2").contents) > 0
            else ""
        )
        duration = (
            article.find("header").find_all("span")[0].contents[0]
            if len(article.find("header").find_all("span")[0].contents) > 0
            else ""
        )
        categories = (
            [
                category.strip()
                for category in article.find("header")
                .find_all("span")[2]
                .contents[0]
                .split("/")
            ]
            if len(article.find("header").find_all("span")[2].contents) > 0
            else []
        )
        description = (
            article.find("header").find("div").find("p").contents[0]
            if len(article.find("header").find("div").find("p").contents) > 0
            else ""
        )
        url = article.find_all("p")[2].find("a").get("href")
        coincidence = SequenceMatcher(None, search_movie, movie_title).ratio()
        if search_movie.lower() in movie_title.lower():
            movies.append(
                MovieObj(movie_title,
                         duration,
                         categories,
                         description,
                         url,
                         coincidence)
            )

    if len(movies) == 0:
        raise MovieNotFound(
            f"0 Movies were found with the title: {search_movie}")

    # movies.sort(key=lambda x: x.coincidence,  reverse=True)
    return movies


def _get_link_from_protected_download_page(url):

    protected_link_page_html_path = config['path']['protected_link_page_html_path']

    protected_link_html = _get_html_from_url(url,
                                             html_save_path=protected_link_page_html_path)
    soup = bs4.BeautifulSoup(
        protected_link_html, features="lxml")
    if not soup.find('header').find('input'):
        download_link = soup.find('header').find_all('p')[
            1].find('a').get('href')
    else:
        download_link = soup.find('header').find('input').get('value')
    return download_link


@dataclass
class DownloadLinkProtected:
    name: str
    link: str


def _get_download_links_from_movie_page(url) -> List[DownloadLinkProtected]:

    movie_page_html_path = config['path']['movie_page_html_path']

    html_downloads_code = _get_html_from_url(url,
                                             html_save_path=movie_page_html_path)
    soup = bs4.BeautifulSoup(html_downloads_code, features="lxml")

    download_opts = []
    for download_btn in soup.find('div', class_="downloads-lst").find_all('a'):
        download_name = download_btn.find_all('span')[1].contents[0].split()[-1] if len(
            download_btn.find_all('span')[1].contents) > 0 else ""

        download_opts.append(
            DownloadLinkProtected(
                download_name,
                _get_link_from_protected_download_page(
                    download_btn.get('href'))
            )
        )

    if len(download_opts) == 0:
        raise DownloadOptionsNotFound('0 Download options were not found.')

    return download_opts


def search_movie(movie_title: str):
    search_page_html_code = _get_search_page_html(movie_title)
    movies_found = _get_movie_objs(search_page_html_code, movie_title)
    return movies_found
