"""
Copyright (C) 2025-2026 Johannes Habel
Licensed under LGPLv3

If you have not received a license with this library, see: https://www.gnu.org/licenses/lgpl-3.0.en.html
"""
try:
    from modules.consts import *
    from .modules.errors import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.errors import *


import os
import logging
import asyncio
import traceback
import threading

from bs4 import BeautifulSoup
from curl_cffi import Response
from typing import Optional, Literal
from functools import cached_property
from base_api import BaseCore, setup_logger
from base_api.modules.errors import NetworkingError, InvalidProxy, BotProtectionDetected, UnknownError

try:
    import lxml
    parser = "lxml"

except (ModuleNotFoundError, ImportError):
    parser = "html.parser"


async def get_html_content(core: BaseCore, url: str) -> str | None:
    # What should I do here?
    try:
        content = await core.fetch(url)
        if isinstance(content, str):
            return content

        if isinstance(content, Response):
            if content.status_code == 404:
                raise NotFound(f"Server returned 404 for: {url}")

    except NetworkingError:
        raise NetworkError from NetworkingError

    except InvalidProxy:
        raise ProxyError from InvalidProxy

    except BotProtectionDetected:
        raise BotDetection from BotProtectionDetected

    except UnknownError:
        raise UnknownNetworkError from UnknownError


class Video:
    def __init__(self, url: str, core: BaseCore):
        self.url = url
        self.core = core
        self.logger = setup_logger(name="Porngo API - [Video]", log_file=None, level=logging.ERROR)
        self.html_content = None
        self.metadata_containers: Optional[list] = None
        self._soup: BeautifulSoup | None = None

    async def init(self):
        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=self.url)
            assert isinstance(self.html_content, str)

        self._soup = BeautifulSoup(self.html_content, parser)
        self.metadata_containers = self.soup.find("div", class_="video-links").find_all("div", class_="video-links__row")
        return self

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call: .init() ")

        return self._soup

    def enable_logging(self, log_file: str | None = None, level=None, log_ip: str | None = None, log_port: int | None = None):
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
        return self.soup.find("meta", property="og:image").get("content")

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

    @cached_property
    def video_qualities(self) -> list:
        # This might not be perfectly accurate, but I just need this working for Porn Fetch, so this is fine

        if len(self.direct_download_urls) == 2:
            qualities = [480, 720] # HD should include 480 and 720 as to my definitions of what "HD" is

        elif len(self.direct_download_urls) == 1:
            qualities = [480] # SD should be like 480 idk

        else:
            qualities = []

        return qualities

    async def download(self, quality: Literal["480p", "720p"] = "720p", path="./", callback=None, no_title=False,
                 stop_event: threading.Event | None = None) -> bool:

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
            await self.core.legacy_download(url=download_url, path=path, callback=callback, stop_event=stop_event)
            return True

        except Exception:
            error = traceback.format_exc()
            self.logger.error(error)
            return False


class Client:
    def __init__(self, core: BaseCore = BaseCore()):
        self.core = core
        self.core.initialize_session()
        self.logger = setup_logger(name="Porngo API - [Client]", log_file=None, level=logging.ERROR)

    def enable_logging(self, log_file: str | None = None, level=None, log_ip: str | None = None, log_port: int | None = None):
        self.logger = setup_logger(name="Porngo API - [Client]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    async def get_video(self, url: str) -> Video:
        """
        :param url: (str) The video URL
        :return: (Video) The video object
        """
        video = Video(url, core=self.core)
        return await video.init()
