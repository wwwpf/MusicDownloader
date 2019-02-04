import time

from PyQt5.QtCore import Qt

from model.table_model import Item, TableModel


class Song(Item):
    def __init__(self):
        super().__init__()

        self.name = ""              # 歌名
        self.singers = []           # 歌手
        self.album = ""             # 专辑
        self.duration = 0           # 时长，单位: 毫秒
        self.available = False      # 歌曲能否播放
        self.id = ""

        self.url = ""
        self.lyrics = ""

    def get_singers(self):
        s = self.singers[0]
        for singer in self.singers[1:]:
            s += "&%s" % (singer)
        return s

    def get_time(self):
        return time.strftime("%M:%S", time.gmtime(int(self.duration / 1000)))

    def __str__(self):
        return "%s - %s in [%s], duration: %s" % (self.get_singers(), self.name, self.album, self.get_time())


class SongModel(TableModel):

    SECLECTION_INDEX = 0
    NAME_INDEX = 1
    SINGERS_INDEX = 2
    ALBUM_INDEX = 3
    DURATION_INDEX = 4

    def __init__(self, parent=None, spider=None):
        super().__init__(parent)

        self.spider = spider
        self.header = ["", "名称", "歌手", "专辑", "时长"]
        self.total_available = 0

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if col == SongModel.NAME_INDEX:
                return self.get_items()[row].name
            elif col == SongModel.SINGERS_INDEX:
                return self.get_items()[row].get_singers()
            elif col == SongModel.ALBUM_INDEX:
                return self.get_items()[row].album
            elif col == SongModel.DURATION_INDEX:
                return self.get_items()[row].get_time()
            elif col == SongModel.SECLECTION_INDEX:
                return self.get_items()[row].selected
            else:
                return super().data(index, role)
        elif role == Qt.ToolTipRole:
            if col == SongModel.NAME_INDEX:
                return self.get_items()[row].name
            elif col == SongModel.SINGERS_INDEX:
                return self.get_items()[row].get_singers()
            elif col == SongModel.ALBUM_INDEX:
                return self.get_items()[row].album
        elif role == Qt.UserRole:
            return self.get_items()[row]

        return super().data(index, role)

    def flags(self, index):
        row = index.row()
        if not self.get_items()[row].available:
            return Qt.NoItemFlags
        return super().flags(index)

    def get_spider(self):
        return self.spider

    def set_spider(self, v):
        self.spider = v

    def set_items(self, v):
        super().set_items(v)
        self.total_available = 0
        for i in self.get_items():
            self.total_available += 1 if i.available else 0

    def is_all_selected(self):
        return self.total_available <= self.current_selected

    def is_all_unselected(self):
        return 0 == self.current_selected

    def set_all(self, flag=True):
        for item in self.get_items():
            if item.available:
                item.selected = flag
        self.current_selected = self.total_available if flag else 0
        if self.SECLECTION_INDEX >= 0:
            begin = self.createIndex(0, self.SECLECTION_INDEX)
            end = self.createIndex(self.rowCount(None), self.SECLECTION_INDEX)
            self.dataChanged.emit(begin, end)
            self.update_selection.emit()
