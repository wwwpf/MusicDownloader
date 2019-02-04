import math

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLabel, QPushButton, QSpinBox

from config import ButtonConfig


class SearchManager(QObject):

    def __init__(self, model, page_layout, spider=None, query=None,
                 total=0, current_songs=[], parent=None):
        super().__init__()

        self.model = model
        self.page_layout = page_layout

        self.total_song = total
        self.current_page = 0

        self.songs = {}
        self.songs[self.current_page] = current_songs

        self.spider = spider

        self.page_num = self.get_page_num()

        self.query = query

        self.parent = parent

        self.paint_buttons()

    def get_page_num(self):
        return math.ceil(self.total_song / self.spider.get_query_num())\
                            if self.spider else\
                            0

    def search_changed(self, spider, query, total, current_songs):
        self.total_song = total
        self.spider = spider
        self.model.set_spider(spider)
        self.query = query
        self.page_num = self.get_page_num()
        if self.page_layout.indexOf(self.current_page_label) < 0:
            self.page_layout.insertWidget(self.page_layout.indexOf(
                self.go_to_next_button), self.current_page_label)
        self.songs.clear()
        self.songs[0] = current_songs
        self.set_page(0)
        self.page_input.setRange(1, self.page_num)

    def get_display_page(self):
        return "%2d" % (self.current_page + 1)

    def paint_buttons(self):

        # 设置跳转按钮
        self.page_input = QSpinBox(self.parent)
        self.page_input.setRange(1, self.page_num)
        self.page_input.setSingleStep(1)
        self.page_input.setValue(1)
        self.page_input.editingFinished.connect(lambda: self.go_to_page(None))
        self.page_input.valueChanged.connect(self.change_jumo_button_state)
        self.go_to_button = QPushButton(
            ButtonConfig.JUMP_ICON, "", self.parent)
        self.go_to_button.clicked.connect(lambda: self.go_to_page(None))
        self.go_to_button.setEnabled(False)

        # 设置首页、末页、上一页、下一页按钮
        self.go_to_first_button = QPushButton(
            ButtonConfig.FIRST_PAGE_ICON, "", self.parent)
        self.go_to_first_button.clicked.connect(self.go_to_first_page)
        self.go_to_first_button.setEnabled(False)
        self.go_to_last_button = QPushButton(
            ButtonConfig.LAST_PAGE_ICON, "", self.parent)
        self.go_to_last_button.clicked.connect(self.go_to_last_page)
        self.go_to_last_button.setEnabled(False)
        self.go_to_previous_button = QPushButton(
            ButtonConfig.PREVIOUS_PAGE_ICON, "", self.parent)
        self.go_to_previous_button.clicked.connect(self.go_to_previous_page)
        self.go_to_previous_button.setEnabled(False)
        self.go_to_next_button = QPushButton(
            ButtonConfig.NEXT_PAGE_ICON, "", self.parent)
        self.go_to_next_button.clicked.connect(self.go_to_next_page)
        self.go_to_next_button.setEnabled(False)

        # 设置显示当前页的QLabel
        self.current_page_label = QLabel(
            self.get_display_page(), self.parent)
        self.current_page_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # 添加按钮
        self.page_layout.addWidget(self.go_to_first_button)
        self.page_layout.addWidget(self.go_to_previous_button)
        if self.page_num > 0:
            self.page_layout.addWidget(self.current_page_label)
        self.page_layout.addWidget(self.go_to_next_button)
        self.page_layout.addWidget(self.go_to_last_button)
        self.page_layout.addWidget(self.page_input)
        self.page_layout.addWidget(self.go_to_button)

    def set_page(self, p):
        self.current_page = p
        self.page_input.setValue(p + 1)
        self.current_page_label.setText(self.get_display_page())
        if p not in self.songs:
            offset = p * self.spider.DEFAULT_QUERY_NUM
            self.songs[p], _ = self.spider.get_songs(
                self.query, offset, self.spider.DEFAULT_QUERY_NUM)
        self.model.set_items(self.songs[p])

        self.go_to_first_button.setEnabled(p > 0)
        self.go_to_previous_button.setEnabled(p > 0)
        self.go_to_last_button.setEnabled(p < self.page_num - 1)
        self.go_to_next_button.setEnabled(p < self.page_num - 1)

    def change_jumo_button_state(self):
        self.go_to_button.setEnabled(
            self.current_page + 1 != self.page_input.value())

    def go_to_page(self, p=None):
        if p is None:
            p = self.page_input.value() - 1
        if p >= 0 and p < self.page_num:
            if self.current_page != p:
                self.set_page(p)

    def go_to_first_page(self):
        self.go_to_page(0)

    def go_to_last_page(self):
        self.go_to_page(self.page_num - 1)

    def go_to_previous_page(self):
        self.go_to_page(self.current_page - 1)

    def go_to_next_page(self):
        self.go_to_page(self.current_page + 1)
