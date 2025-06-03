import os
import re
import json
import requests
import parsel

# 网页请求头
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
}


# 网页URL
SEARCH_URL = "https://www.gequbao.com/s/"
MUSIC_URL = "https://www.gequbao.com/music/"
API_URL = "https://www.gequbao.com/api/play-url"


class MySpider:
    def __init__(self):
        pass

    # 获取搜索内容
    @staticmethod
    def get_music_list(keyword):
        music_list = list()
        try:
            # 发送请求
            with requests.get(SEARCH_URL + keyword, headers=HEADERS) as search_response:
                search_response.raise_for_status()

                # 解析网页
                selector = parsel.Selector(search_response.text)
                music_rows = selector.css(".row")[2:-1]

                for row in music_rows:
                    # 提取歌曲信息
                    music_id = row.css(".music-link::attr(href)").get().split("/")[-1]
                    music_title = row.css(".text-primary span::text").get()
                    music_artist = row.css(".text-jade::text").get().strip()

                    # 将歌曲信息保存到字典
                    music_info = {
                        "歌名": music_title,
                        "歌手": music_artist,
                        "ID": music_id,
                    }
                    music_list.append(music_info)
                print(f"{keyword} 搜索成功")
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误：{e}")
        except Exception as e:
            print(f"搜索歌曲时发生错误：{e}")

        return music_list

    # 获取歌曲url
    @staticmethod
    def get_music_url(music_dict):
        music_title = music_dict["歌名"]
        music_artist = music_dict["歌手"]
        music_id = music_dict["ID"]
        try:
            # 请求歌曲页面
            with requests.get(MUSIC_URL + music_id, headers=HEADERS) as music_response:
                music_response.raise_for_status()

                # 提取歌曲信息
                app_data = re.findall("window.appData = (.*?);", music_response.text)[0]
                app_data_dict = json.loads(app_data)
                play_id = app_data_dict["play_id"]

                # 获取歌曲音频链接
                with requests.post(
                    API_URL, data={"id": play_id}, headers=HEADERS
                ) as api_response:
                    api_response.raise_for_status()
                    api_data = api_response.json()
                    music_file_url = api_data["data"]["url"]

                    print(f"{music_title}-{music_artist} 获取url成功！")
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误：{e}")
        except Exception as e:
            print(f"下载歌曲时发生错误：{e}")
        return music_file_url

    # 指定下载歌曲
    @staticmethod
    def download_music(music_dict_list, MUSIC_SAVE_FOLDER):
        for music_dict in music_dict_list:
            music_title = music_dict["歌名"]
            music_artist = music_dict["歌手"]
            music_id = music_dict["ID"]
            try:
                # 请求歌曲页面获取详细信息
                with requests.get(
                    MUSIC_URL + music_id, headers=HEADERS
                ) as music_response:
                    music_response.raise_for_status()

                    # 提取歌曲信息
                    app_data = re.findall(
                        "window.appData = (.*?);", music_response.text
                    )[0]
                    app_data_dict = json.loads(app_data)

                    play_id = app_data_dict["play_id"]
                    cover_url = app_data_dict["mp3_cover"]
                    lyrics_data = re.search(
                        '<div class="content-lrc mt-1" id="content-lrc">(.*?)</div>',
                        music_response.text,
                        re.S,
                    )

                    # 修正歌词中的时间戳格式
                    if lyrics_data:
                        lyrics_content = lyrics_data.group(1).replace("<br />", "")
                        lyrics_content = re.sub(
                            r"\[(\d+:\d+)\.(\d{2})\d*\]",
                            lambda match: f"[{match.group(1)}.{match.group(2)}]",
                            lyrics_content,
                        )
                        lyrics_content = lyrics_content.replace("\r\n", "\n")
                    else:
                        lyrics_content = "暂无歌词信息"

                    # 获取歌曲音频链接
                    with requests.post(
                        API_URL, data={"id": play_id}, headers=HEADERS
                    ) as api_response:
                        api_response.raise_for_status()
                        api_data = api_response.json()
                        music_file_url = api_data["data"]["url"]

                        # 创建保存文件夹
                        # save_folder = os.path.join(
                        #     MUSIC_SAVE_FOLDER, f"{music_title}-{music_artist}"
                        # )
                        # if not os.path.exists(save_folder):
                        #     os.makedirs(save_folder)

                        # 下载歌曲音频
                        with requests.get(
                            music_file_url, headers=HEADERS, stream=True
                        ) as music_content:
                            music_content.raise_for_status()

                            with open(
                                os.path.join(
                                    MUSIC_SAVE_FOLDER,
                                    f"{music_title}-{music_artist}.mp3",
                                ),
                                "wb",
                            ) as f:
                                f.write(music_content.content)

                        # 下载封面图片
                        if cover_url and cover_url != "/static/img/music_cover3.png":
                            with requests.get(
                                cover_url, headers=HEADERS
                            ) as cover_response:
                                cover_response.raise_for_status()
                                with open(
                                    os.path.join(
                                        MUSIC_SAVE_FOLDER,
                                        f"{music_title}-{music_artist}.jpg",
                                    ),
                                    "wb",
                                ) as f:
                                    f.write(cover_response.content)

                        # 保存歌词
                        with open(
                            os.path.join(
                                MUSIC_SAVE_FOLDER, f"{music_title}-{music_artist}.lrc"
                            ),
                            "w",
                            encoding="utf-8",
                        ) as f:
                            f.write(lyrics_content)
                        print(f"歌曲 {music_title}-{music_artist} 下载成功！")
            except requests.exceptions.RequestException as e:
                print(f"网络请求错误：{e}")
            except Exception as e:
                print(f"下载歌曲时发生错误：{e}")

        print("全部下载成功")

    # 模糊下载歌曲
    @staticmethod
    def batch_download_music(music_title_list, MUSIC_SAVE_FOLDER):
        for music_title in music_title_list:
            music_dict_list = MySpider.get_music_list(music_title)
            if not len(music_dict_list):
                print(f"{music_title} 查无此歌")
                continue
            # 默认第一首
            music_dict = music_dict_list[0]
            MySpider.download_music(music_dict, MUSIC_SAVE_FOLDER)
        print("全部下载成功")


# 测试功能
if __name__ == "__main__":

    # music_dict = {"歌名": "暮色回响", "歌手": "吉星出租", "ID": "273"}
    # music_list = myspider.get_music_list("暮色回响")
    # MySpider.download_music(MySpider.get_music_list("告白气球")[0])
    # print(MySpider.get_music_url(music_dict))
    music_title_list = [
        "我从草原来",
        "一生的爱",
        "会过去的",
        "熟能生巧",
        "蓝眼泪",
        "十年",
        "世上最懂我的",
        "踏古",
        "该死的温柔",
        "大城小爱",
        "彼得与狼",
        "马头琴的诉说",
        "独家记忆",
        "童话镇",
        "只有喜欢",
        "GraceKellyBlues",
        "军中绿花",
        "火力全开",
        "今生爱上你",
        "画",
        "恋红尘",
        "知否知否",
        "三年二班",
        " 改不掉",
        "乔克叔叔",
        "断点",
        "魔鬼中的天使",
        "一生无悔",
        "千千阙歌",
        "爱如潮水",
    ]
    MySpider.batch_download_music(music_title_list, r"Music\Recommend")
    # music_title_list = [
    #     "爱人错过",
    #     "半岛铁盒",
    #     "错位时空",
    #     "带我去找夜生活",
    #     "多情种",
    #     "多幸运",
    #     "红色高跟鞋",
    #     "画",
    #     "金玉良缘",
    #     "旧词",
    #     "戒不掉",
    #     "Letting Go",
    #     "淋雨一直走",
    #     "罗生门",
    #     "你的",
    #     "平凡之路",
    #     "See you again",
    #     "shadow of th sun",
    #     "someone you loved",
    #     "something just like this",
    #     "山外小楼夜听雨",
    #     "身骑白马",
    #     "水星记",
    #     "take me hand",
    #     "天若有情",
    #     "为你唱这首歌",
    #     "我记得",
    #     "无名之辈",
    #     "向云端",
    #     "勋章",
    #     "you are beatuiful",
    #     "一百万个可能",
    #     "一万次悲伤",
    #     "越来越不懂",
    #     "在你的身边",
    #     "最后的道别",
    #     "最美的期待",
    # ]
    # MySpider.batch_download_music(music_title_list, r"Music\Local")
