import base64
import copy
import json
import random
from urllib.parse import urljoin

import requests

from model.song_model import Song
from spider.spider_def import SongSpider


class QQSong(Song):
    def __init__(self):
        super().__init__()

        self.mid = ""  # 用于 QQ 音乐
        self.type = 0


def get_guid():
    return random.randrange(0, 1e10)


def test_song_available(json_song):
    '''参见 https://y.gtimg.cn/music/portal/js/common/pkg/common_397951d.js?:formatted，主要代码如下：
        e["switch"] || (e["switch"] = 403);
        var n = e["switch"].toString(2).split("");
        n.pop(),
        n.reverse();
        var o = ["play_lq", "play_hq", "play_sq", "down_lq", "down_hq", "down_sq", "soso", "fav", "share"bgm", "ring", "sing", "radio", "try", "give"];
        e.action = {};
        for (var a = 0; a < o.length; a++)
            e.action[o[a]] = parseInt(n[a], 10) || 0;
        e.pay = e.pay || {},
        e.preview = e.preview || {},
        e.playTime = makePlayTime(e.interval),
        e.action.play = 0,
        (e.action.play_lq || e.action.play_hq || e.action.play_sq) && (e.action.play = 1),
    '''

    o = ["play_lq", "play_hq", "play_sq", "down_lq", "down_hq", "down_sq",
         "soso", "fav", "share", "bgm", "ring", "sing", "radio", "try", "give"]
    if "action" in json_song and "switch" in json_song["action"]:
        n = json_song["action"]["switch"]
    else:
        n = 403
    bin_n = str(bin(n))
    bin_n = bin_n[2:-1]
    switch = bin_n[::-1]
    actions = {"play": 0}
    for i in range(len(o)):
        actions[o[i]] = int(switch[i]) or 0
    if actions["play_lq"] or actions["play_hq"] or actions["play_sq"]:
        actions["play"] = 1

    return actions["play"]


class QQSongSpider(SongSpider):

    DEFAULT_QUERY_NUM = 20

    def __init__(self):
        super().__init__()

    def get_songs(self, query, offset=0, count=DEFAULT_QUERY_NUM):
        '''获取从 offset 开始的 count 首歌曲
        Returns:
            获取到的歌曲 及 搜索结果数目
        '''

        search_url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
        payload = {
            "p": int(offset / self.DEFAULT_QUERY_NUM) + 1,
            "n": count if count else self.DEFAULT_QUERY_NUM,
            "w": query,
            "format": "json",
            "cr": 1,
            "new_json": 1
        }
        headers = copy.deepcopy(self.headers)
        headers["referer"] = "https://y.qq.com/portal/search.html"

        resp = requests.get(search_url, params=payload, headers=headers)
        json_resp = resp.json()
        result = []
        total_count = 0

        if json_resp["code"] != 0:
            return result, total_count

        for json_song in json_resp["data"]["song"]["list"]:
            song = QQSong()
            song.name = json_song["name"]
            song.album = json_song["album"]["name"]
            song.duration = int(json_song["interval"]) * 1000
            song.id = json_song["id"]
            song.mid = ""
            if "mid" in json_song:
                song.mid = json_song["mid"]
            elif "file" in json_song and "strMediaMid" in json_song["file"]:
                song.mid = json_song["file"]["strMediaMid"]

            song.type = json_song["type"]

            song.available = test_song_available(json_song)

            for json_singer in json_song["singer"]:
                song.singers.append(json_singer["name"])

            result.append(song)

        if "totalnum" in json_resp["data"]["song"]:
            total_count = json_resp["data"]["song"]["totalnum"]

        return result, total_count

    def _get_song_url(self, song):
        # 2019.01.01: m4a 可用，mp3, flac, ape 禁止访问

        url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
        req_0 = {
            "module": "vkey.GetVkeyServer",
            "method": "CgiGetVkey",
            "param": {
                "guid": "%s" % get_guid(),
                "songmid": [song.mid],
                "songtype": [song.type],
                "uin": "0",
                "loginflag": 1,
                "platform": "20"
            }
        }

        comm = {
            "uin": 0,
            "format": "json",
            "ct": 20,
            "cv": 0
        }
        data = {"req_0": req_0, "comm": comm}
        payload = {
            "loginUin": "0",
            "hostUin": "0",
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
            "notice": "0",
            "platform": "yqq.json",
            "needNewCode": "0",
            "data": json.dumps(data, separators=(",", ":"))
        }
        r = requests.get(url, params=payload)
        json_data = r.json()
        req_0_data = json_data["req_0"]["data"]
        host = ""
        for i in req_0_data["sip"]:
            if len(i) > 0:
                host = i
                break
        song_url = req_0_data["midurlinfo"][0]["purl"]
        song_url = urljoin(host, song_url)

        return song_url

    def _get_song_lyrics(self, song):
        url = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
        payload = {
            "songmid": song.mid,
            "loginUin": "0",
            "hostUin": "0",
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
            "notice": "0",
            "platform": "yqq.json",
            "needNewCode": "0"
        }
        headers = copy.deepcopy(self.headers)
        headers["referer"] = "https://y.qq.com/portal/player.html"
        r = requests.get(url, params=payload, headers=headers)
        json_data = r.json()
        lyric = json_data["lyric"]
        lyric = base64.b64decode(lyric).decode("utf-8")

        return lyric

    def download_song(self, song):
        return
