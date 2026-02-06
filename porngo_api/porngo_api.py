"""
Copyright (C) 2025-2026 Johannes Habel
Licensed under LGPLv3

If you have not received a license with this library, see: https://www.gnu.org/licenses/lgpl-3.0.en.html
"""
try:
    from modules.consts import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *


import os
import logging
import traceback
import threading

from bs4 import BeautifulSoup
from typing import Optional, Literal
from functools import cached_property
from base_api import BaseCore, setup_logger

try:
    import lxml
    parser = "lxml"

except (ModuleNotFoundError, ImportError):
    parser = "html.parser"


class Video:
    def __init__(self, url: str, core: Optional[BaseCore] = None):
        self.url = url
        self.core = core
        self.logger = setup_logger(name="Porngo API - [Video]", log_file=None, level=logging.ERROR)
        self.html_content = self.core.fetch(self.url)
        self.soup = BeautifulSoup(self.html_content, parser)
        self.metadata_containers = self.soup.find("div", class_="video-links").find_all("div", class_="video-links__row")

    def enable_logging(self, log_file: str = None, level=None, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="Porngo API - [Video]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    @cached_property
    def title(self) -> str:
        return self.soup.find("h1", class_="headline__title").text.strip()

    @cached_property
    def views(self) -> str:
        return self.soup.find("span", class_="video-info__text").text.strip()

    @cached_property # TODO: Implement Pornstar support
    def pornstars(self) -> list:
        _pornstars = self.metadata_containers[1].find_all("a", class_="video-links__link")
        urls = [a.get("href") for a in _pornstars]
        return urls

    @cached_property
    def categories(self) -> list:
        _categories = self.metadata_containers[2].find_all("a", class_="video-links__link")
        categories = [a.text for a in _categories]
        return categories

    @cached_property
    def author(self) -> str:
        return self.metadata_containers[3].find_all("span")[1].text.strip()

    @cached_property
    def thumbnail(self) -> str:
        return self.soup.find("meta", property="og:image")["content"]

    @cached_property
    def likes(self) -> str:
        return self.soup.find_all("span", class_="rating__count")[0].text.strip()

    @cached_property
    def dislikes(self) -> str:
        return self.soup.find_all("span", class_="rating__count")[1].text.strip()

    @cached_property
    def direct_download_urls(self) -> list:
        link_tags = self.metadata_containers[4].find_all("a", class_="video-links__link")
        direct_download_urls = [a.get("href") for a in link_tags]

        return direct_download_urls


    def download(self, quality: Literal["480p", "720p"] = "720p", path="./", callback=None, no_title=False,
                 stop_event: threading.Event = None) -> bool:

        if quality == "480p":
            download_url = self.direct_download_urls[0]

        elif quality == "720p":
            try:
                download_url = self.direct_download_urls[1]

            except IndexError:
                self.logger.error("The specified quality: 720p is not available, using 480 instead...")
                download_url = self.direct_download_urls[0]

        else:
            self.logger.error("Invalid quality specified!")
            return False

        if no_title is False:
            path = os.path.join(path, f"{self.title}.mp4")

        try:
            self.core.legacy_download(url=download_url, path=path, callback=callback, stop_event=stop_event)
            return True

        except Exception:
            error = traceback.format_exc()
            self.logger.error(error)
            return False


class Client:
    def __init__(self, core: Optional[BaseCore] = None):
        self.core = core or BaseCore()
        self.core.initialize_session()
        self.logger = setup_logger(name="Porngo API - [Client]", log_file=None, level=logging.ERROR)

    def enable_logging(self, log_file: str = None, level=None, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="Porngo API - [Client]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    def get_video(self, url: str) -> Video:
        """
        :param url: (str) The video URL
        :return: (Video) The video object
        """
        return Video(url, core=self.core)

