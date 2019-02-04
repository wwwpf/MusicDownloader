import os

from PyQt5.QtGui import QIcon

from song_spider import *

RESOURCE_PATH = "resources"

NETEASE_CLOUD_MUSIC = "网易云音乐"
QQ_MUSIC = "QQ音乐"

SUPPORED_WEB_SITES = {
    NETEASE_CLOUD_MUSIC: NeteaseSongSpider(),
    QQ_MUSIC: QQSongSpider()
}

class ImageConfig:
    ABOUT_DIALOG_BACKGROUND_FILE = os.path.join(RESOURCE_PATH, "background.gif")


class HttpRequestConfig:
    CHROME_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"


class ButtonConfig:
    BUTTON_WIDTH = 30
    BUTTON_MARGIN = 3

    PLAY_ICON = QIcon(os.path.join(RESOURCE_PATH, "play.svg"))
    PAUSE_ICON = QIcon(os.path.join(RESOURCE_PATH, "pause.svg"))
    STOP_ICON = QIcon(os.path.join(RESOURCE_PATH, "stop.svg"))
    DOWNLOAD_ICON = QIcon(os.path.join(RESOURCE_PATH, "download.svg"))
    FIRST_PAGE_ICON = QIcon(os.path.join(RESOURCE_PATH, "first_button.svg"))
    LAST_PAGE_ICON = QIcon(os.path.join(RESOURCE_PATH, "last_button.svg"))
    PREVIOUS_PAGE_ICON = QIcon(os.path.join(
        RESOURCE_PATH, "previcous_button.svg"))
    NEXT_PAGE_ICON = QIcon(os.path.join(RESOURCE_PATH, "next_button.svg"))
    JUMP_ICON = QIcon(os.path.join(RESOURCE_PATH, "jump_button.svg"))
    SEARCH_ICON = QIcon(os.path.join(RESOURCE_PATH, "search.svg"))
