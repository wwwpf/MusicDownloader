import base64
import json
from urllib.parse import unquote

import execjs
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES

from model.song_model import Song
from spider.spider_def import SongSpider
from utils import logging_wrap


@logging_wrap
def decrypt_json(encrypted_json, gs, btd7W):
    ctx = execjs.compile(js_code)
    r = ctx.call("decrypt", encrypted_json, "undefined" + gs + btd7W)
    r = unquote(r)
    return r


def parse_song(json_song):
    song = Song()
    song.name = json_song["name"]
    song.album = json_song["al"]["name"]
    song.duration = int(json_song["dt"])
    song.id = json_song["id"]
    song.available = test_song_available(json_song)

    for json_singer in json_song["ar"]:
        song.singers.append(json_singer["name"])
    return song


def AES_encrypt(plain_text, key):
    '''本函数为以下js代码的python版本
    function b(a, b) {
        var c = CryptoJS.enc.Utf8.parse(b)
          , d = CryptoJS.enc.Utf8.parse("0102030405060708")
          , e = CryptoJS.enc.Utf8.parse(a)
          , f = CryptoJS.AES.encrypt(e, c, {
            iv: d,
            mode: CryptoJS.mode.CBC
        });
        return f.toString()
    }
    js中返回的密文是实际AES加密后再经过base64编码的数据。
    '''

    key_data = key.encode("utf-8")
    IV = "0102030405060708".encode("utf-8")
    cryptor = AES.new(key_data, AES.MODE_CBC, IV)

    padding_len = 16 - (len(plain_text) & 0xf)
    plain_data = (plain_text + chr(padding_len) * padding_len).encode("utf-8")
    cipher_data = cryptor.encrypt(plain_data)
    return base64.b64encode(cipher_data).decode("utf-8")


def get_encrypted_data(raw_data):
    json_str = json.dumps(raw_data)
    g = "0CoJUm6Qyw8W8jud"
    i = "7Sqn81qnWueMIrue"
    h = {}
    h["encText"] = AES_encrypt(json_str, g)
    h["encText"] = AES_encrypt(h["encText"], i)
    h["encSecKey"] = "22f32d9a7de53e27c16de2c9d47ee1fc1f4a9781e7732443c31b994421521ac8756431c7b6605de714fe909c2ff4c3db32ad31fb1d46e957e64377f88fb37bb2bc02770c146f99d5bd76fa3039bb1aa30e22618eb3e4f29f1184f106c25f33aa6cc65c065231794d09ac011555628e55029eb3ce72c10e07c71aad126a921ed6"

    return h


def get_encrypted_post_data(raw_data):
    h = get_encrypted_data(raw_data)
    post_data = {
        "params": h["encText"],
        "encSecKey": h["encSecKey"]
    }

    return post_data


def get_permission(json_song):
    if not json_song:
        return 0
    keys = ["privilege", "pv"]
    privilege = None
    for key in keys:
        if key in json_song:
            privilege = json_song[key]
            break
    if "program" in json_song and json_song["program"]:
        return 0
    if privilege:
        if privilege["st"] and privilege["st"] < 0:
            return 100
        elif privilege["fee"] > 0 and privilege["fee"] != 8 and privilege["payed"] == 0 and privilege["pl"] <= 0:
            return 10
        elif privilege["fee"] == 16 or privilege["fee"] == 4 and (privilege["flag"] & 2048):
            return 11
        elif (privilege["fee"] == 0 or privilege["payed"]) and privilege["pl"] > 0 and privilege["dl"] == 0:
            return 1000
        elif privilege["pl"] == 0 and privilege["dl"] == 0:
            return 100
        return 0
    else:
        if "status" in json_song and json_song["status"] >= 0:
            return 0
        if "fee" in json_song and json_song["fee"] > 0:
            return 10
        return 100


def test_song_available(json_song):
    permission = get_permission(json_song)
    if permission == 10:
        return False
    elif permission == 100:
        return False
    elif permission == 11:
        return False
    return True


class NeteaseSongSpider(SongSpider):

    DEFAULT_QUERY_NUM = 30

    def __init__(self):
        super().__init__()

        self.headers["Host"] = "music.163.com"
        self.headers["Origin"] = "https://music.163.com"
        self.headers["Referer"] = "https://music.163.com"

    def get_songs(self, query, offset=0, count=DEFAULT_QUERY_NUM):
        if not query or len(query) == 0:
            return [], 0
        search_url = "https://music.163.com/weapi/cloudsearch/get/web"
        raw_data = {
            "csrf_token": "",
            "hlposttag": "</span>",
            "hlpretag": "<span class=\"s-fc7\">",
            # 最大为100
            "limit": "%s" % (count if count else NeteaseSongSpider.DEFAULT_QUERY_NUM),
            "offset": "%s" % offset,
            "s": query,
            "total": "true",
            "type": "1"
        }
        post_data = get_encrypted_post_data(raw_data)

        resp = requests.post(search_url, data=post_data, headers=self.headers)
        json = resp.json()
        result = []
        total_count = 0

        if "result" not in json or not json["result"] or "songs" not in json["result"]:
            return result, total_count

        for json_song in json["result"]["songs"]:
            result.append(parse_song(json_song))

        if "songCount" in json["result"]:
            total_count = json["result"]["songCount"]

        return result, total_count

    def _get_song_url(self, song):
        url = "https://music.163.com/weapi/song/enhance/player/url"
        raw_data = {
            # "br": 128000,
            "br": 320000,   # 比特率
            "csrf_token": "",
            "ids": "[%s]" % song.id
        }
        post_data = get_encrypted_post_data(raw_data)
        r = requests.post(url, data=post_data, headers=self.headers)
        json_data = r.json()
        song_url = json_data["data"][0]["url"]

        return song_url

    def _get_song_lyrics(self, song):
        lyric_url = "https://music.163.com/weapi/song/lyric"
        raw_data = {
            "csrf_token": "",
            "id": song.id,
            "lv": -1,
            "tv": -1
        }
        post_data = get_encrypted_post_data(raw_data)
        r = requests.post(lyric_url, data=post_data, headers=self.headers)
        json_data = r.json()

        lyric = ""
        if "lrc" in json_data and "lyric" in json_data["lrc"]:
            lyric = json_data["lrc"]["lyric"]

        return lyric

    @logging_wrap
    def get_playlist(self, id):
        playlist_url = "https://music.163.com/playlist"
        data = {
            "id": "%s" % id
        }
        r = requests.get(playlist_url, params=data, headers=self.headers)

        bs_obj = BeautifulSoup(r.text, "html.parser")
        empty_result = ([], 0)
        img_obj = bs_obj.find("img", {"class": "j-img"})
        if not img_obj:
            return empty_result

        gs = img_obj["data-key"]

        div_obj = bs_obj.find("div", {"id": "song-list-pre-cache"})
        if not div_obj:
            return empty_result
        ul_obj = div_obj.find("ul", {"class": "f-hide"})
        if not ul_obj:
            return empty_result
        li_obj = ul_obj.find("li")
        if not li_obj:
            return empty_result
        a_obj = li_obj.find("a")
        if not a_obj:
            return empty_result
        btd7W = a_obj["href"][9:12]

        textarea = bs_obj.find("textarea", {"id": "song-list-pre-data"})
        if not textarea:
            return empty_result

        encrypted_json = textarea.text
        json_str = decrypt_json(encrypted_json, gs, btd7W)
        json_data = json.loads(json_str)
        songs = []
        for json_song in json_data:
            songs.append(parse_song(json_song))
        return songs, len(songs)


js_code = r"""
var NC7v = 64;
var bbB1x = 64;
var bTm5r = 4;
var csF0x = [82, 9, 106, -43, 48, 54, -91, 56, -65, 64, -93, -98, -127, -13, -41, -5, 124, -29, 57, -126, -101, 47, -1, -121, 52, -114, 67, 68, -60, -34, -23, -53, 84, 123, -108, 50, -90, -62, 35, 61, -18, 76, -107, 11, 66, -6, -61, 78, 8, 46, -95, 102, 40, -39, 36, -78, 118, 91, -94, 73, 109, -117, -47, 37, 114, -8, -10, 100, -122, 104, -104, 22, -44, -92, 92, -52, 93, 101, -74, -110, 108, 112, 72, 80, -3, -19, -71, -38, 94, 21, 70, 87, -89, -115, -99, -124, -112, -40, -85, 0, -116, -68, -45, 10, -9, -28, 88, 5, -72, -77, 69, 6, -48, 44, 30, -113, -54, 63, 15, 2, -63, -81, -67, 3, 1, 19, -118, 107, 58, -111, 17, 65, 79, 103, -36, -22, -105, -14, -49, -50, -16, -76, -26, 115, -106, -84, 116, 34, -25, -83, 53, -123, -30, -7, 55, -24, 28, 117, -33, 110, 71, -15, 26, 113, 29, 41, -59, -119, 111, -73, 98, 14, -86, 24, -66, 27, -4, 86, 62, 75, -58, -46, 121, 32, -102, -37, -64, -2, 120, -51, 90, -12, 31, -35, -88, 51, -120, 7, -57, 49, -79, 18, 16, 89, 39, -128, -20, 95, 96, 81, 127, -87, 25, -75, 74, 13, 45, -27, 122, -97, -109, -55, -100, -17, -96, -32, 59, 77, -82, 42, -11, -80, -56, -21, -69, 60, -125, 83, -103, 97, 23, 43, 4, 126, -70, 119, -42, 38, -31, 105, 20, 99, 85, 33, 12, 125];

var CO4S = function (ir8j) {
    if (ir8j < -128) {
        return CO4S(128 - (-128 - ir8j))
    } else if (ir8j >= -128 && ir8j <= 127) {
        return ir8j
    } else if (ir8j > 127) {
        return CO4S(-129 + ir8j - 127)
    } else {
        throw new Error("1001")
    }
};

var bXF6z = function () {
    var sM1x = /\n|\r|=/g;
    var Hf5k = { "A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7, "I": 8, "J": 9, "K": 10, "L": 11, "M": 12, "N": 13, "O": 14, "P": 15, "Q": 16, "R": 17, "S": 18, "T": 19, "U": 20, "V": 21, "W": 22, "X": 23, "Y": 24, "Z": 25, "a": 26, "b": 27, "c": 28, "d": 29, "e": 30, "f": 31, "g": 32, "h": 33, "i": 34, "j": 35, "k": 36, "l": 37, "m": 38, "n": 39, "o": 40, "p": 41, "q": 42, "r": 43, "s": 44, "t": 45, "u": 46, "v": 47, "w": 48, "x": 49, "y": 50, "z": 51, "0": 52, "1": 53, "2": 54, "3": 55, "4": 56, "5": 57, "6": 58, "7": 59, "8": 60, "9": 61, "+": 62, "/": 63 }
    return function (i5n) {
        var r5w = 0
            , m5r = [];
        i5n = i5n.replace(sM1x, "");
        for (var i = 0, l = i5n.length; i < l; i += 4)
            m5r.push(Hf5k[i5n.charAt(i)] << 2 | Hf5k[i5n.charAt(i + 1)] >> 4, (Hf5k[i5n.charAt(i + 1)] & 15) << 4 | Hf5k[i5n.charAt(i + 2)] >> 2, (Hf5k[i5n.charAt(i + 2)] & 3) << 6 | Hf5k[i5n.charAt(i + 3)]);
        var bs5x = m5r.length
            , eJ7C = i5n.length % 4;
        if (eJ7C == 2)
            m5r = m5r.slice(0, bs5x - 2);
        if (eJ7C == 3)
            m5r = m5r.slice(0, bs5x - 1);
        return m5r
    }
}();

var cDx3x = function (i5n) {
    var iP8H = bXF6z(i5n), dA6u = iP8H.length, iV8N;
    var r5w = 0;
    while (iV8N = iP8H[r5w]) {
        if (iV8N > 128) {
            iP8H[r5w] = iV8N - 256
        }
        r5w++
    }
    return iP8H
};

var csG0x = function (bs5x) {
    var bv5A = [];
    for (var i = 0; i < bs5x; i++) {
        bv5A[i] = 0
    }
    return bv5A
};

var csL0x = function (cZ6T, bmH6B, bs5x) {
    var dK6E = [];
    if (cZ6T == null || cZ6T.length == 0) {
        return dK6E
    }
    if (cZ6T.length < bs5x) {
        throw new Error("1003")
    }
    for (var i = 0; i < bs5x; i++) {
        dK6E[i] = cZ6T[bmH6B + i]
    }
    return dK6E
};

var csD0x = function (rE1x) {
    var bTk4o = [];
    if (rE1x == null || rE1x == undefined || rE1x.length == 0) {
        return csG0x(bbB1x)
    }
    if (rE1x.length >= bbB1x) {
        return csL0x(rE1x, 0, bbB1x)
    } else {
        for (var i = 0; i < bbB1x; i++) {
            bTk4o[i] = rE1x[i % rE1x.length]
        }
    }
    return bTk4o
};

var csy0x = function (bbP1x) {
    if (bbP1x == null || bbP1x.length % NC7v != 0) {
        throw new Error("1005")
    }
    var bnr6l = [];
    var bj5o = 0;
    var csx0x = bbP1x.length / NC7v;
    for (var i = 0; i < csx0x; i++) {
        bnr6l[i] = [];
        for (var j = 0; j < NC7v; j++) {
            bnr6l[i][j] = bbP1x[bj5o++]
        }
    }
    return bnr6l
};

var csw0x = function (bTi4m) {
    var pA0x = bTi4m >>> 4 & 15;
    var pi0x = bTi4m & 15;
    var bj5o = pA0x * 16 + pi0x;
    return csF0x[bj5o]
};

var bTh4l = function (bnE6y) {
    if (bnE6y == null) {
        return null
    }
    var bTg4k = [];
    for (var i = 0, bs5x = bnE6y.length; i < bs5x; i++) {
        bTg4k[i] = csw0x(bnE6y[i])
    }
    return bTg4k
};

var ctq0x = function (blO5T, UK9B) {
    blO5T = CO4S(blO5T);
    UK9B = CO4S(UK9B);
    return CO4S(blO5T ^ UK9B)
};

var bTL5Q = function (UJ9A, blX5c) {
    if (UJ9A == null || blX5c == null || UJ9A.length != blX5c.length) {
        return UJ9A
    }
    var rs1x = [];
    var cto0x = UJ9A.length;
    for (var i = 0, bs5x = cto0x; i < bs5x; i++) {
        rs1x[i] = ctq0x(UJ9A[i], blX5c[i])
    }
    return rs1x
};

var cup1x = function (ir8j, bj5o) {
    return CO4S(ir8j + bj5o)
};

var ctU1x = function (bbb1x, blz5E) {
    if (bbb1x == null) {
        return null
    }
    if (blz5E == null) {
        return bbb1x
    }
    var rs1x = [];
    var ctK1x = blz5E.length;
    for (var i = 0, bs5x = bbb1x.length; i < bs5x; i++) {
        rs1x[i] = cup1x(bbb1x[i], blz5E[i % ctK1x])
    }
    return rs1x
};

var ctJ1x = function (bbf1x) {
    if (bbf1x == null) {
        return bbf1x
    }
    var rs1x = [];
    var ctv0x = bbf1x.length;
    for (var i = 0, bs5x = ctv0x; i < bs5x; i++) {
        rs1x[i] = CO4S(0 - bbf1x[i])
    }
    return rs1x
};

var ctq0x = function (blO5T, UK9B) {
    blO5T = CO4S(blO5T);
    UK9B = CO4S(UK9B);
    return CO4S(blO5T ^ UK9B)
};

var bTL5Q = function (UJ9A, blX5c) {
    if (UJ9A == null || blX5c == null || UJ9A.length != blX5c.length) {
        return UJ9A
    }
    var rs1x = [];
    var cto0x = UJ9A.length;
    for (var i = 0, bs5x = cto0x; i < bs5x; i++) {
        rs1x[i] = ctq0x(UJ9A[i], blX5c[i])
    }
    return rs1x
};

var bmI6C = function (cZ6T, bmH6B, sW1x, csH0x, bs5x) {
    if (cZ6T == null || cZ6T.length == 0) {
        return sW1x
    }
    if (sW1x == null) {
        throw new Error("1004")
    }
    if (cZ6T.length < bs5x) {
        throw new Error("1003")
    }
    for (var i = 0; i < bs5x; i++) {
        sW1x[csH0x + i] = cZ6T[bmH6B + i]
    }
    return sW1x
};

var csN0x = function (yn3x) {
    var bd5i = 0;
    bd5i += (yn3x[0] & 255) << 24;
    bd5i += (yn3x[1] & 255) << 16;
    bd5i += (yn3x[2] & 255) << 8;
    bd5i += yn3x[3] & 255;
    return bd5i
};

var bTJ5O = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"];

var ctk0x = function (dq6k) {
    var Nv7o = [];
    Nv7o.push(bTJ5O[dq6k >>> 4 & 15]);
    Nv7o.push(bTJ5O[dq6k & 15]);
    return Nv7o.join("")
};

var bTE5J = function (xz2x) {
    var bs5x = xz2x.length;
    if (xz2x == null || bs5x < 0) {
        return new String("")
    }
    var Nv7o = [];
    for (var i = 0; i < bs5x; i++) {
        Nv7o.push(ctk0x(xz2x[i]))
    }
    return Nv7o.join("")
};

var bTf4j = function (NE7x, rE1x) {
    if (NE7x == null) {
        return null
    }
    if (NE7x.length == 0) {
        return []
    }
    if (NE7x.length % NC7v != 0) {
        throw new Error("1005," + NE7x.length + "," + NC7v)
    }
    rE1x = csD0x(rE1x);
    var bnI6C = rE1x;
    var bnJ6D = csy0x(NE7x);
    var Uf9W = [];
    var csl0x = bnJ6D.length;
    for (var i = 0; i < csl0x; i++) {
        var bnO6I = bTh4l(bnJ6D[i]);
        bnO6I = bTh4l(bnO6I);
        var bnQ6K = bTL5Q(bnO6I, bnI6C);
        var csf0x = ctU1x(bnQ6K, ctJ1x(bnI6C));
        bnQ6K = bTL5Q(csf0x, rE1x);
        bmI6C(bnQ6K, 0, Uf9W, i * NC7v, NC7v);
        bnI6C = bnJ6D[i]
    }
    var bTa4e = [];
    bmI6C(Uf9W, Uf9W.length - bTm5r, bTa4e, 0, bTm5r);
    var bs5x = csN0x(bTa4e);
    if (bs5x > Uf9W.length) {
        throw new Error("1006")
    }
    var rs1x = [];
    bmI6C(Uf9W, 0, rs1x, 0, bs5x);
    return rs1x
};

var bTu5z = function (bbw1x) {
    if (bbw1x == null || bbw1x.length == 0) {
        return bbw1x
    }
    var bmr5w = new String(bbw1x);
    var rs1x = [];
    var bs5x = bmr5w.length / 2;
    var bj5o = 0;
    for (var i = 0; i < bs5x; i++) {
        var pA0x = parseInt(bmr5w.charAt(bj5o++), 16) << 4;
        var pi0x = parseInt(bmr5w.charAt(bj5o++), 16);
        rs1x[i] = CO4S(pA0x + pi0x)
    }
    return rs1x
};

var bTt5y = function (cQ6K) {
    if (cQ6K == null || cQ6K == undefined) {
        return cQ6K
    }
    var Ur9i = encodeURIComponent(cQ6K);
    var xz2x = [];
    var bTp5u = Ur9i.length;
    for (var i = 0; i < bTp5u; i++) {
        if (Ur9i.charAt(i) == "%") {
            if (i + 2 < bTp5u) {
                xz2x.push(bTu5z(Ur9i.charAt(++i) + "" + Ur9i.charAt(++i))[0])
            } else {
                throw new Error("1009")
            }
        } else {
            xz2x.push(Ur9i.charCodeAt(i))
        }
    }
    return xz2x
};

var crP0x = function (bok6e, K5P) {
    var bog6a = bTf4j(bXF6z(bok6e), bTt5y(K5P));
    var Jr6l = new String(bTE5J(bog6a));
    var zU3x = [];
    var boj6d = Jr6l.length / 2;
    var bj5o = 0;
    for (var i = 0; i < boj6d; i++) {
        zU3x.push("%");
        zU3x.push(Jr6l.charAt(bj5o++));
        zU3x.push(Jr6l.charAt(bj5o++))
    }
    return zU3x.join("")
};

var decrypt = function (encrypted_json, k) {
    c = encrypted_json;
    c = crP0x(c, k);
    return c
};
"""
