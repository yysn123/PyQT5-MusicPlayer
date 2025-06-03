# 获取本地音乐信息
import os
import re
from mutagen.mp3 import MP3
from prettytable import PrettyTable
from pypinyin import pinyin, Style


class MusicInfo:
    def __init__(self):
        pass

    # 获取音乐信息
    @staticmethod
    def get_music_dict_list(MUSIC_FILE_PATH):
        music_info_dict_list = list()
        for filename in os.listdir(MUSIC_FILE_PATH):
            match = re.match(r"(.*)-(.*).mp3", filename)
            if match:
                audio = MP3(os.path.join(MUSIC_FILE_PATH, filename))

                # 获取歌名信息
                title = match.group(1)

                # 获取歌手信息
                artist = match.group(2)

                # 获取专辑信息
                try:
                    album = audio["TALB"].text[0]
                except KeyError:
                    album = "未知专辑"

                if album == "空":
                    album = "未知专辑"

                # 获取歌曲时长
                duration = audio.info.length
                time = f"{int(duration / 60):02}:{int(duration) % 60:02}"

                music_info_dict = {
                    "歌名": title,
                    "歌手": artist,
                    "专辑": album,
                    "时长": time,
                }
                music_info_dict_list.append(music_info_dict)
        # 按歌名排序
        # 按拼音排序
        music_info_dict_list.sort(
            key=lambda keys: [pinyin(i, style=Style.TONE3) for i in keys["歌名"]]
        )

        return music_info_dict_list


if __name__ == "__main__":
    print(MusicInfo.get_music_dict_list(r"Music\Recommend"))
