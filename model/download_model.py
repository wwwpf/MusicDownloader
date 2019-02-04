import math
import time

from PyQt5.QtCore import QModelIndex, Qt

from model.table_model import Item, TableModel


def get_human_read(s):
    post_fix = ["B", "KB", "MB", "GB"]
    n = int(math.log(s, 1024)) if s > 0 else 0
    n = min(n, 3)
    return "%.2f" % (s / (1 << (10*n))) + post_fix[n]


class DownloadItem(Item):
    def __init__(self, song=None, row=0):
        super().__init__()

        self.song = song
        self.file_size = math.inf   # 文件大小，单位: KB
        self.progress = 0.0         # 下载进度
        self.speed = 0.0            # 下载速度
        self.current_size = 0       # 已下载大小，单位: KB
        self.row = row

    def get_song_str(self):
        return "%s - %s" % (self.song.get_singers(), self.song.name)

    def get_file_size(self):
        if self.file_size is math.inf:
            return "未知"
        return get_human_read(self.file_size)

    def finished(self):
        return self.current_size >= self.file_size

    def get_speed(self):
        if not self.finished():
            return get_human_read(self.speed) + "/s"
        else:
            return "已完成"

    def get_remain_time(self):
        if self.speed < 1e-6 or self.file_size is math.inf:
            return "--:--"
        if not self.finished():
            t = (self.file_size - self.current_size) / self.speed
            return time.strftime("%M:%S", time.gmtime(t))
        return "已完成"


class DownloadModel(TableModel):

    SONG_INDEX = 0
    DURATION_INDEX = 1
    PROGRESS_INDEX = 2
    SPEED_INDEX = 3
    REMAIN_TIME_INDEX = 4
    FILE_SIZE_INDEX = 5

    def __init__(self):
        super().__init__()

        self.header = ["歌曲", "时长", "进度", "下载速度", "剩余时间", "文件大小"]

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if col == self.SONG_INDEX:
                return self.get_items()[row].get_song_str()
            elif col == self.DURATION_INDEX:
                return self.get_items()[row].song.get_time()
            elif col == self.PROGRESS_INDEX:
                return self.get_items()[row].progress
            elif col == self.SPEED_INDEX:
                return self.get_items()[row].get_speed()
            elif col == self.REMAIN_TIME_INDEX:
                return self.get_items()[row].get_remain_time()
            elif col == self.FILE_SIZE_INDEX:
                return self.get_items()[row].get_file_size()
        elif role == Qt.ToolTipRole:
            if col == self.SONG_INDEX:
                return self.get_items()[row].get_song_str()
        return super().data(index, role)

    def update_row(self, row):
        begin = self.createIndex(row, 0)
        end = self.createIndex(row, self.columnCount(None))
        self.dataChanged.emit(begin, end)

    def add_item(self, v):
        self.beginInsertRows(QModelIndex(), v.row, v.row)
        self.get_items().append(v)
        self.endInsertRows()

    def remove_all_item(self):
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount(None))
        self.get_items().clear()
        self.endRemoveRows()
