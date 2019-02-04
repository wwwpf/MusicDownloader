import logging

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication


def get_center_rect(rect):
    w = min(rect.width(), rect.height())
    center_x = (rect.left() + rect.right()) >> 1
    center_y = (rect.top() + rect.bottom()) >> 1
    return QRect(center_x - (w >> 1), center_y - (w >> 1), w, w)


def get_screen_center_rect(current_rect):
    screen_center = QApplication.desktop().availableGeometry().center()
    current_rect.moveCenter(screen_center)
    return current_rect


def logging_wrap(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            logging.exception(e)
    return wrapper


def init_logging():
    FILE_NAME = "log.txt"
    file_handler = logging.FileHandler(FILE_NAME, encoding="utf-8")
    FORMAT = "%(asctime)s %(filename)s[line:%(lineno)d]\t"\
        "%(levelname)s\t%(message)s"
    logging.basicConfig(handlers=[file_handler],
                        level=logging.INFO, format=FORMAT)
