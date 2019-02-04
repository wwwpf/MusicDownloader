import os
import time
from urllib.parse import urlparse

import requests
from PyQt5.QtCore import (QMutex, QObject, QRunnable, QThreadPool, pyqtSignal,
                          pyqtSlot)

from config import HttpRequestConfig
from model.download_model import DownloadItem

CHUNK_SIZE = 1024 * 256


def get_base_name(basename, extension):
    i = 1
    while True:
        new_basename = "%s(%d)" % (basename, i)
        new_filename = "%s.%s" % (new_basename, extension)
        if not os.path.exists(new_filename):
            return new_basename
        i += 1


class DownloadSingal(QObject):
    update = pyqtSignal(int)

    def __init__(self, model):
        super().__init__()

        self.update.connect(model.update_row)


class DownloadTask(QRunnable):

    TIMEOUT = 2 * 60
    mutex = QMutex()

    HEADERS = {"User-Agent": HttpRequestConfig.CHROME_USER_AGENT}

    def __init__(self, download_item, spider, download_singal):
        super().__init__()

        self.spider = spider
        self.download_item = download_item

        self.singal = download_singal

        self.should_run = True

    def stop(self):
        self.should_run = False

    @pyqtSlot()
    def run(self):
        if not self.should_run:
            return

        url = self.spider.get_song_url(self.download_item.song)
        if not url or len(url) == 0:
            return

        self.download_item.song.url = url

        prefix = "%s - %s" % (self.download_item.song.get_singers(),
                              self.download_item.song.name)
        path = urlparse(url).path
        extension = "mp3"
        index = path.rfind(".")
        if index >= 0:
            extension = path[index + 1:]
        song_file = "%s.%s" % (prefix, extension)
        self.mutex.lock()
        if os.path.exists(song_file):
            prefix = get_base_name(prefix, extension)
        self.mutex.unlock()
        song_file = "%s.%s" % (prefix, extension)
        with open(song_file, "wb") as fout:
            with requests.get(url, stream=True, headers=self.HEADERS, timeout=self.TIMEOUT) as r:
                if not self.should_run:
                    return

                for k in r.headers.keys():
                    if "content-length" in k.lower():
                        self.download_item.file_size = int(r.headers[k])

                previous_time = time.time()
                for data in r.iter_content(CHUNK_SIZE):
                    if not self.should_run:
                        return

                    current_time = time.time()
                    cost_time = current_time - previous_time
                    previous_time = current_time
                    if cost_time > 1e-6:
                        self.download_item.speed = len(data) / cost_time
                    self.download_item.current_size += len(data)
                    self.download_item.progress = self.download_item.current_size / \
                        self.download_item.file_size
                    self.singal.update.emit(self.download_item.row)
                    fout.write(data)

        if not self.should_run:
            return

        lyrics = self.spider.get_song_lyrics(self.download_item.song)
        if not lyrics or len(lyrics) == 0:
            return
        self.download_item.song.lyrics = lyrics
        lyrics_file = "%s.%s" % (prefix, "lrc")
        with open(lyrics_file, "w", encoding="utf-8") as fout:
            fout.write(lyrics)


class DownloadManager(QObject):
    def __init__(self, model, worker_thread_num=5):
        super().__init__()

        self.model = model
        self.thread_pool = QThreadPool.globalInstance()

        self.tasks = []

    def add_download(self, spider, song):
        download_item = DownloadItem(song, self.model.rowCount(None))
        self.model.add_item(download_item)

        download_task = DownloadTask(
            download_item, spider, DownloadSingal(self.model))
        self.tasks.append(download_task)
        self.thread_pool.start(download_task)

    @pyqtSlot()
    def cancel_all_download(self):
        if self.thread_pool.activeThreadCount() > 0:
            self.thread_pool.clear()
            for task in self.tasks:
                task.stop()
            self.model.remove_all_item()
