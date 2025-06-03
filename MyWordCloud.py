import jieba
import re
from wordcloud import WordCloud
import numpy as np
from PIL import Image
from matplotlib import colors
import datetime

SAVE_FILE_PATH = r"asset\wordcloud"

music_dict_list = [
    {"歌名": "爱错", "歌手": "王力宏", "专辑": "心中的日月", "时长": "03:58"},
    {"歌名": "成都", "歌手": "赵雷", "专辑": "成都", "时长": "05:28"},
    {"歌名": "盗将行", "歌手": "花粥&马雨阳", "专辑": "粥请客 (二)", "时长": "03:18"},
]


class MyWordCloud:
    def __init__(self):
        pass

    @staticmethod
    def get_wordcloude(music_dict_list, MUSIC_FILE_PATH):
        text = ""

        for dict in music_dict_list:
            # 读取文件
            f = open(
                rf"{MUSIC_FILE_PATH}\{dict['歌名']}-{dict['歌手']}.lrc",
                "r",
                encoding="utf-8",
            )
            text += "\n" + re.sub(r"\[.+]", "", f.read())
            f.close()

        # 分词
        wordlist_jieba = jieba.lcut(text)

        # 读取停用表
        stop = ["\n"]
        with open(r"asset\stop.txt", "r", encoding="utf-8") as f:
            for line in f:
                stop.append(line.replace("\n", ""))
        f.close()

        # 统计词频
        word_dict = {}
        for key in wordlist_jieba:
            word_dict[key] = word_dict.get(key, 0) + 1

        # 去除停用词
        for key in list(word_dict.keys()):
            if stop.count(key):
                del word_dict[key]

        # 排序打印
        sorted(word_dict.items(), key=lambda d: d[1], reverse=True)

        # 词云图背景
        background_image = np.array(Image.open(r"asset\background.jpg"))

        # 词云图颜色
        colormaps = colors.ListedColormap(
            ["#871A84", "#BC0F6A", "#BC0F60", "#CC5F6A", "#AC1F4A"]
        )

        # 生成词云图
        wordcloud = WordCloud(
            font_path=r"asset\SIMLI.TTF",
            prefer_horizontal=0.99,
            background_color="white",
            max_words=100,
            max_font_size=100,
            stopwords=stop,
            mask=background_image,
            # colormap=colormaps,
            collocations=False,
        ).fit_words(word_dict)

        path = (
            rf'{SAVE_FILE_PATH}\{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        wordcloud.to_file(path)
        print("词云图生成成功")

        # 读取图片
        image = Image.open(path)

        # 显示图片
        image.show()


if __name__ == "__main__":
    MyWordCloud.get_wordcloude(music_dict_list, r"Music\Local")
