from model.song_model import Song


class SongSpider(object):

    DEFAULT_QUERY_NUM = 1

    def __init__(self):
        super().__init__()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
        }

        self.query_num = self.DEFAULT_QUERY_NUM

    def get_query_num(self):
        return self.query_num

    def set_query_num(self, v):
        if v > 0:
            self.query_num = v

    def get_songs(self, query, offset=None, count=None):
        '''获取从 offset 开始的 count 首歌曲
        Returns:
            获取到的歌曲 及 搜索结果数目
        '''
        return [], 0

    def get_song_url(self, song):
        song.url = self._get_song_url(song)
        return song.url

    def _get_song_url(self, song):
        return ""

    def get_song_lyrics(self, song):
        song.lyrics = self._get_song_lyrics(song)
        return song.lyrics

    def _get_song_lyrics(self, song):
        return ""
