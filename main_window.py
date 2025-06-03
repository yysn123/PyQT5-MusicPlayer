import re
import os
import images_rc
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtMultimedia import *
from MusicInfo import MusicInfo
from MySpider import MySpider
from MyWordCloud import MyWordCloud
from MyImage import MyImage
from pypinyin import pinyin, Style
from prettytable import PrettyTable, PLAIN_COLUMNS

# UI文件路径
UI_FILE_PATH = r"main_window.ui"

# 音乐文件
MUSIC_FILE_PATH = [r"Music\Temp", r"Music\Recommend", r"Music\Local", r"MV"]
# 播放源判断
PLAY_SOURCE = 2


# 搜索线程
class SearchThread(QThread):
    search_result_signal = pyqtSignal(list)

    def __init__(self, search_text):
        super().__init__()
        self.search_text = search_text

    def run(self):
        search_results = MySpider.get_music_list(self.search_text)
        self.search_result_signal.emit(search_results)


# 下载线程
class DownloadThread(QThread):
    def __init__(self, music_dict_list, save_path):
        super().__init__()
        self.music_dict_list = music_dict_list
        self.save_path = save_path

    def run(self):
        MySpider.download_music(self.music_dict_list, self.save_path)


# 播放线程
class PlayThread(QThread):
    play_ready_signal = pyqtSignal(str, str)

    def __init__(self, music_dict, play_path):
        super().__init__()
        self.music_dict = music_dict
        self.play_path = play_path

    def run(self):
        MySpider.download_music([self.music_dict], self.play_path)
        music_title = self.music_dict["歌名"]
        music_artist = self.music_dict["歌手"]
        self.play_ready_signal.emit(music_title, music_artist)


class Main_Window(QWidget):
    # 构造函数
    def __init__(self):
        super().__init__()
        # 播放对象
        self.player = QMediaPlayer(self)
        # 播放对象集
        self.local_playlist = QMediaPlaylist(self)
        self.recommend_playlist = QMediaPlaylist(self)
        self.mv_playlist = QMediaPlaylist(self)
        # 默认集
        self.player.setPlaylist(self.local_playlist)
        # 歌词
        self.lrc_dict_list = list()
        self.ui_init()
        self.signal_init()
        self.playlist_init()

    # ui加载
    def ui_init(self):
        self.ui = uic.loadUi(UI_FILE_PATH)
        self.ui.resize(1600, 1200)
        # 隐藏边框
        self.ui.setWindowFlags(Qt.FramelessWindowHint)
        self.ui.setWindowOpacity(0.85)  # 设置窗口透明度
        self.ui.setAttribute(Qt.WA_TranslucentBackground, False)
        # effect = QGraphicsBlurEffect()
        # effect.setBlurRadius(8)
        # self.ui.mv_widget.setGraphicsEffect(effect)
        # op = QGraphicsOpacityEffect()
        # op.setOpacity(1.0)
        # self.ui.mv_play_widget.setGraphicsEffect(op)
        # self.ui.mv_play_widget.setStyleSheet("background-color: black;")
        # 默认打开页面
        self.ui.stackedWidget.setCurrentIndex(1)

        # 封面固定大小
        self.ui.cover_label.setMinimumSize(150, 150)
        self.ui.cover_label.setMaximumSize(150, 150)
        self.ui.lrc_cover_label.setMinimumSize(500, 500)
        self.ui.lrc_cover_label.setMaximumSize(500, 500)

        radio = 1.6
        self.ui.mv_play_widget.setMinimumSize(int(720 * radio), int(480 * radio))
        self.ui.mv_play_widget.setMaximumSize(int(720 * radio), int(480 * radio))

        self.ui.progress_slider.setEnabled(False)
        self.ui.lrc_widget.hide()
        self.ui.mv_widget.hide()

        # 按键悬浮
        self.ui.volume_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.lrc_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.next_play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.play_pause_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.playmode_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.pre_play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.exit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.max_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.min_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.search_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.set_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.recommend_wordcloud_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.mine_wordcloud_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.mine_delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.about_tabbtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.mine_tabbtn.setCursor(QCursor(Qt.PointingHandCursor))
        # self.ui.mv_tabbtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.recommend_tabbtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.return_btn1.setCursor(QCursor(Qt.PointingHandCursor))
        self.ui.return_btn2.setCursor(QCursor(Qt.PointingHandCursor))

    # 信号绑定
    def signal_init(self):
        # 标题栏信号
        self.ui.exit_btn.clicked.connect(lambda: self.header_btn_func(self.ui.exit_btn))
        self.ui.max_btn.clicked.connect(lambda: self.header_btn_func(self.ui.max_btn))
        self.ui.min_btn.clicked.connect(lambda: self.header_btn_func(self.ui.min_btn))
        self.ui.search_btn.clicked.connect(
            lambda: self.header_btn_func(self.ui.search_btn)
        )
        self.ui.set_btn.clicked.connect(lambda: self.header_btn_func(self.ui.set_btn))
        self.ui.theme_btn.clicked.connect(
            lambda: self.header_btn_func(self.ui.theme_btn)
        )
        # 选项卡信号
        self.ui.mine_tabbtn.clicked.connect(
            lambda: self.tab_btn_func(self.ui.mine_tabbtn)
        )
        self.ui.recommend_tabbtn.clicked.connect(
            lambda: self.tab_btn_func(self.ui.recommend_tabbtn)
        )
        self.ui.about_tabbtn.clicked.connect(
            lambda: self.tab_btn_func(self.ui.about_tabbtn)
        )
        self.ui.mv_tabbtn.clicked.connect(lambda: self.tab_btn_func(self.ui.mv_tabbtn))
        # 控制信号
        self.ui.volume_btn.clicked.connect(
            lambda: self.control_btn_func(self.ui.volume_btn)
        )
        self.ui.pre_play_btn.clicked.connect(
            lambda: self.control_btn_func(self.ui.pre_play_btn)
        )
        self.ui.play_pause_btn.clicked.connect(
            lambda: self.control_btn_func(self.ui.play_pause_btn)
        )
        self.ui.next_play_btn.clicked.connect(
            lambda: self.control_btn_func(self.ui.next_play_btn)
        )
        self.ui.playmode_btn.clicked.connect(
            lambda: self.control_btn_func(self.ui.playmode_btn)
        )
        self.ui.lrc_btn.clicked.connect(lambda: self.control_btn_func(self.ui.lrc_btn))
        # 音乐状态信号
        self.player.durationChanged.connect(self.get_duration_func)
        self.player.positionChanged.connect(self.get_position_func)
        # 滑动进度条
        self.ui.progress_slider.sliderReleased.connect(self.update_position_func)
        self.ui.volume_slider.sliderReleased.connect(self.volume_slider_func)
        # 我的页面信号
        self.ui.mine_music_list_widget.doubleClicked.connect(self.list_play_func)
        self.ui.mine_music_list_widget.itemSelectionChanged.connect(
            self.search_item_func
        )
        self.ui.mine_wordcloud_btn.clicked.connect(self.wordcloud_display)
        self.ui.mine_delete_btn.clicked.connect(self.delete_music)
        # 推荐页面信号
        self.ui.recommend_music_list_widget.doubleClicked.connect(self.list_play_func)
        self.ui.recommend_music_list_widget.itemSelectionChanged.connect(
            self.search_item_func
        )
        self.ui.recommend_wordcloud_btn.clicked.connect(self.wordcloud_display)
        # 搜索页面信号
        self.ui.search_music_list_widget.doubleClicked.connect(self.list_play_func)
        self.ui.search_music_list_widget.itemSelectionChanged.connect(
            self.search_item_func
        )
        self.ui.download_btn.clicked.connect(self.download_func)
        # 返回信号
        self.ui.return_btn1.clicked.connect(lambda: self.myreturn(self.ui.return_btn1))
        self.ui.return_btn2.clicked.connect(lambda: self.myreturn(self.ui.return_btn2))
        # 视频页面信号
        self.ui.mv_list_widget.doubleClicked.connect(self.list_play_func)
        self.ui.mv_list_widget.itemSelectionChanged.connect(self.search_item_func)

    # 窗口返回
    def myreturn(self, btn):
        if btn == self.ui.return_btn1:
            self.ui.lrc_widget.hide()
            self.ui.main_widget.show()
        elif btn == self.ui.return_btn2:
            self.ui.setWindowOpacity(0.85)
            self.ui.mv_widget.hide()
            self.ui.main_widget.show()

    # 歌曲集初始化
    def playlist_init(self):
        self.local_music_dict_list = list()
        self.recommend_music_dict_list = list()
        self.mv_dict_list = list()

        # 获取表数据
        self.local_music_dict_list = MusicInfo.get_music_dict_list(MUSIC_FILE_PATH[2])
        self.recommend_music_dict_list = MusicInfo.get_music_dict_list(
            MUSIC_FILE_PATH[1]
        )
        dirlist = os.listdir(MUSIC_FILE_PATH[3])
        for dir in dirlist:
            match = re.match("(.+) - (.+).mp4", dir)
            if match:
                self.mv_dict_list.append(
                    {"歌名": match.group(1), "歌手": match.group(2)}
                )
        self.mv_dict_list.sort(
            key=lambda keys: [pinyin(i, style=Style.TONE3) for i in keys["歌名"]]
        )

        # 添加媒体
        for music_dict in self.local_music_dict_list:
            self.local_playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(
                        f"{MUSIC_FILE_PATH[2]}/{music_dict['歌名']}-{music_dict['歌手']}.mp3"
                    )
                )
            )
        for music_dict in self.recommend_music_dict_list:
            self.recommend_playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(
                        f"{MUSIC_FILE_PATH[1]}/{music_dict['歌名']}-{music_dict['歌手']}.mp3"
                    )
                )
            )
        for mv_dict in self.mv_dict_list:
            self.mv_playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(
                        f"{MUSIC_FILE_PATH[3]}/{mv_dict['歌名']} - {mv_dict['歌手']}.mp4"
                    )
                )
            )

        # 显示歌曲
        tb = PrettyTable()
        tb.set_style(PLAIN_COLUMNS)
        tb.align = "l"
        tb.field_names = ["序号", "歌名", "歌手", "专辑", "时长"]
        index = 1

        for dict in self.local_music_dict_list:
            tb.add_row(
                [
                    f"{index:02}",
                    dict["歌名"],
                    dict["歌手"],
                    dict["专辑"],
                    dict["时长"],
                ]
            )
            index += 1
        tb_str_list = tb.get_string().splitlines()
        self.ui.mine_music_list_widget.addItems(tb_str_list)
        tb.clear_rows()
        index = 1
        for dict in self.recommend_music_dict_list:
            tb.add_row(
                [
                    f"{index:02}",
                    dict["歌名"],
                    dict["歌手"],
                    dict["专辑"],
                    dict["时长"],
                ]
            )
            index += 1
        tb_str_list = tb.get_string().splitlines()
        self.ui.recommend_music_list_widget.addItems(tb_str_list)

        tb_mv = PrettyTable()
        tb_mv.set_style(PLAIN_COLUMNS)
        tb_mv.align = "l"
        tb_mv.field_names = ["序号", "歌名", "歌手"]
        index = 1
        for dict in self.mv_dict_list:
            tb_mv.add_row([f"{index:02}", dict["歌名"], dict["歌手"]])
            index += 1
        tb_str_list = tb_mv.get_string().splitlines()
        self.ui.mv_list_widget.addItems(tb_str_list)


        # 默认顺序播放
        self.local_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
        self.recommend_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
        self.mv_playlist.setPlaybackMode(QMediaPlaylist.Sequential)

    # 更新本地集
    def update_playlist(self):
        print("更新音乐")
        self.ui.mine_music_list_widget.clear()
        self.local_music_dict_list = list()

        # 获取表数据
        self.local_music_dict_list = MusicInfo.get_music_dict_list(MUSIC_FILE_PATH[2])

        self.local_playlist.clear()
        # 添加媒体
        for music_dict in self.local_music_dict_list:
            self.local_playlist.addMedia(
                QMediaContent(
                    QUrl.fromLocalFile(
                        f"{MUSIC_FILE_PATH[2]}/{music_dict['歌名']}-{music_dict['歌手']}.mp3"
                    )
                )
            )

        # 显示歌曲
        tb = PrettyTable()
        tb.set_style(PLAIN_COLUMNS)
        tb.align = "l"
        tb.field_names = ["序号", "歌名", "歌手", "专辑", "时长"]
        index = 1

        for dict in self.local_music_dict_list:
            tb.add_row(
                [
                    f"{index:02}",
                    dict["歌名"],
                    dict["歌手"],
                    dict["专辑"],
                    dict["时长"],
                ]
            )
            index += 1
        tb_str_list = tb.get_string().splitlines()

        self.ui.mine_music_list_widget.addItems(tb_str_list)
        # 默认顺序播放
        self.local_playlist.setPlaybackMode(QMediaPlaylist.Sequential)

    # 搜索歌曲初始化
    def search_playlist_init(self):
        global PLAY_SOURCE
        PLAY_SOURCE = 0
        search_text = self.ui.search_edit.text()
        if not search_text:
            print("搜索为空")
            return
        # 建立线程
        self.search_thread = SearchThread(search_text)
        # 线程信号绑定
        self.search_thread.search_result_signal.connect(self.search_results_display)
        # 进行线程
        self.search_thread.start()

    # 搜索线程: 展示搜索结果
    def search_results_display(self, search_results):
        self.search_music_dict_list = search_results
        self.ui.search_music_list_widget.clear()
        tb = PrettyTable()
        index = 1
        tb.field_names = ["序号", "歌名", "歌手"]
        for dict in self.search_music_dict_list:
            tb.add_row([f"{index:02}", dict["歌名"], dict["歌手"]])
            index += 1
        tb.set_style(PLAIN_COLUMNS)
        tb.align = "l"
        tb_str_list = tb.get_string().splitlines()
        self.ui.search_music_list_widget.addItems(tb_str_list)
        self.ui.stackedWidget.setCurrentIndex(2)

    # 删除歌曲
    def delete_music(self):
        selected_indices = [
            self.ui.mine_music_list_widget.indexFromItem(item).row() - 1
            for item in self.ui.mine_music_list_widget.selectedItems()
        ]
        if not len(selected_indices):
            print("未选择")
            return

        # 创建一个对话框
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除所选歌曲吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        # 判断用户的选择
        if reply == QMessageBox.Yes:
            for idx in selected_indices:
                music_title = self.local_music_dict_list[idx]["歌名"]
                music_artist = self.local_music_dict_list[idx]["歌手"]
                os.remove(rf"Music\Local\{music_title}-{music_artist}.mp3")
                os.remove(rf"Music\Local\{music_title}-{music_artist}.jpg")
                os.remove(rf"Music\Local\{music_title}-{music_artist}.lrc")
            self.update_playlist()
            self.player.setPlaylist(self.local_playlist)
            print("删除成功")
        else:
            print("取消删除")

    # 生成词云图
    def wordcloud_display(self):
        # 创建一个对话框
        reply = QMessageBox.question(
            self,
            "确认生成",
            "确定要生成所选歌曲词云图吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        # 判断用户的选择
        if reply == QMessageBox.Yes:
            music_dict_list = list()
            if PLAY_SOURCE == 2:
                selected_indices = [
                    self.ui.mine_music_list_widget.indexFromItem(item).row() - 1
                    for item in self.ui.mine_music_list_widget.selectedItems()
                ]
                if not len(selected_indices):
                    print("未选择")
                    return
                for idx in selected_indices:
                    music_dict_list.append(self.local_music_dict_list[idx])
            elif PLAY_SOURCE == 1:
                selected_indices = [
                    self.ui.recommend_music_list_widget.indexFromItem(item).row() - 1
                    for item in self.ui.recommend_music_list_widget.selectedItems()
                ]
                if not len(selected_indices):
                    print("未选择")
                    return
                for idx in selected_indices:
                    music_dict_list.append(self.recommend_music_dict_list[idx])
            MyWordCloud.get_wordcloude(music_dict_list, MUSIC_FILE_PATH[PLAY_SOURCE])

    # 下载音乐
    def download_func(self):
        selected_indices = [
            self.ui.search_music_list_widget.indexFromItem(item).row() - 1
            for item in self.ui.search_music_list_widget.selectedItems()
        ]
        download_dict_list = list()
        for idx in selected_indices:
            music_dict = self.search_music_dict_list[idx]
            download_dict_list.append(music_dict)
        self.download_thread = DownloadThread(download_dict_list, MUSIC_FILE_PATH[2])
        self.download_thread.start()

    # 选中项目
    def search_item_func(self):
        if PLAY_SOURCE == 0:
            selected_indices = [
                self.ui.search_music_list_widget.indexFromItem(item).row()
                for item in self.ui.search_music_list_widget.selectedItems()
            ]
        elif PLAY_SOURCE == 1:
            selected_indices = [
                self.ui.recommend_music_list_widget.indexFromItem(item).row()
                for item in self.ui.recommend_music_list_widget.selectedItems()
            ]
        elif PLAY_SOURCE == 2:
            selected_indices = [
                self.ui.mine_music_list_widget.indexFromItem(item).row()
                for item in self.ui.mine_music_list_widget.selectedItems()
            ]
        elif PLAY_SOURCE == 3:
            selected_indices = [
                self.ui.mv_list_widget.indexFromItem(item).row()
                for item in self.ui.mv_list_widget.selectedItems()
            ]
        print("选中行: ", selected_indices)

    # 音量移动
    def volume_slider_func(self):
        value = self.ui.volume_slider.value()
        self.player.setVolume(value)
        self.ui.volume_label.setText(f"{value}%")
        if value == 0:
            if not self.player.isMuted():
                self.player.setMuted(True)
            self.ui.volume_btn.setIcon(QIcon("images/音量_关.png"))
            print("音量: 静音")
        else:
            if self.player.isMuted():
                self.player.setMuted(False)
            if value in range(0, 30):
                self.ui.volume_btn.setIcon(QIcon("images/音量_低.png"))
            elif value in range(30, 70):
                self.ui.volume_btn.setIcon(QIcon("images/音量_中.png"))
            elif value in range(70, 101):
                self.ui.volume_btn.setIcon(QIcon("images/音量_高.png"))
            print(f"音量: {value}%")

    # 进度条移动
    def update_position_func(self):
        value = self.ui.progress_slider.value()
        self.player.setPosition(value)
        self.ui.current_duration_label.setText(
            f"{int(value/60000):02d}:{(int(value/1000)%60):02d}"
        )
        print(f"移动进度条: {int(value/60000):02d}:{(int(value/1000)%60):02d}")

    # 歌词界面显示
    def lrc_widget_display(self):
        if PLAY_SOURCE == 3:
            return
        elif PLAY_SOURCE == 2:
            index = self.local_playlist.currentIndex()
            music_title = self.local_music_dict_list[index]["歌名"]
            music_artist = self.local_music_dict_list[index]["歌手"]
            music_album = self.local_music_dict_list[index]["专辑"]
        elif PLAY_SOURCE == 1:
            index = self.recommend_playlist.currentIndex()
            music_title = self.recommend_music_dict_list[index]["歌名"]
            music_artist = self.recommend_music_dict_list[index]["歌手"]
            music_album = self.recommend_music_dict_list[index]["专辑"]
        elif PLAY_SOURCE == 0:
            index = self.ui.search_music_list_widget.currentRow() - 1
            music_title = self.search_music_dict_list[index]["歌名"]
            music_artist = self.search_music_dict_list[index]["歌手"]
            music_album = "未知专辑"

        self.ui.lrc_title_label.setText(music_title)
        self.ui.lrc_artist_label.setText(f"歌手: {music_artist}\t专辑: {music_album}")
        cover_path = f"{MUSIC_FILE_PATH[PLAY_SOURCE]}/{music_title}-{music_artist}.jpg"
        self.ui.lrc_cover_label.setPixmap(QPixmap(MyImage.circleImage(cover_path)))
        self.ui.lrc_list_widget.setStyleSheet("font: 45px;")
        self.ui.lrc_list_widget.clear()
        self.lrc_dict_list = list()
        with open(
            f"{MUSIC_FILE_PATH[PLAY_SOURCE]}\{music_title}-{music_artist}.lrc",
            "r",
            encoding="utf-8",
        ) as f:
            lrc_list = f.readlines()
            for line in lrc_list:
                match = re.match(r"\[(\d+):(.+)](.+)", line)
                if match:
                    time = int(
                        (float(match.group(1)) * 60 + float(match.group(2))) * 1000
                    )
                    content = match.group(3)
                    self.lrc_dict_list.append({"time": time, "content": content})
        for i in range(6):
            self.ui.lrc_list_widget.addItem("")
        self.ui.lrc_list_widget.addItems(
            [line["content"] for line in self.lrc_dict_list]
        )

    # 初始化显示
    def get_duration_func(self, total_duration):
        # 本地音乐
        if PLAY_SOURCE == 2:
            index = self.local_playlist.currentIndex()
            music_title = self.local_music_dict_list[index]["歌名"]
            music_artist = self.local_music_dict_list[index]["歌手"]
        elif PLAY_SOURCE == 1:
            index = self.recommend_playlist.currentIndex()
            music_title = self.recommend_music_dict_list[index]["歌名"]
            music_artist = self.recommend_music_dict_list[index]["歌手"]
        elif PLAY_SOURCE == 0:
            index = self.ui.search_music_list_widget.currentRow() - 1
            music_title = self.search_music_dict_list[index]["歌名"]
            music_artist = self.search_music_dict_list[index]["歌手"]
        elif PLAY_SOURCE == 3:
            index = self.mv_playlist.currentIndex()
            music_title = self.mv_dict_list[index]["歌名"]
            music_artist = self.mv_dict_list[index]["歌手"]

        self.ui.music_title_label.setText(music_title)
        self.ui.music_artist_label.setText(music_artist)

        self.ui.progress_slider.setRange(0, total_duration)
        self.ui.progress_slider.setEnabled(True)
        # 显示歌曲时长
        self.ui.total_duration_label.setText(
            f"{int(total_duration/60000):02d}:{(int(total_duration/1000)%60):02d}"
        )
        if not PLAY_SOURCE == 3:
            cover_path = (
                f"{MUSIC_FILE_PATH[PLAY_SOURCE]}/{music_title}-{music_artist}.jpg"
            )
            self.lrc_widget_display()
        else:
            cover_path = "Images\周杰伦.png"

        self.ui.cover_label.setPixmap(QPixmap(MyImage.circleImage(cover_path)))
        self.ui.cover_label.setScaledContents(True)

    # 更新时间
    def get_position_func(self, current_duration):
        self.ui.progress_slider.setValue(current_duration)
        self.ui.current_duration_label.setText(
            f"{int(current_duration/60000):02d}:{(int(current_duration/1000)%60):02d}"
        )
        if PLAY_SOURCE == 3:
            return
        if len(self.lrc_dict_list) != 0:
            for dict in self.lrc_dict_list:
                if current_duration > dict["time"]:
                    self.ui.lrc_list_widget.item(5).setForeground(QColor(230, 230, 230))
                    self.ui.lrc_list_widget.item(6).setForeground(QColor(0, 122, 217))
                    self.ui.lrc_list_widget.takeItem(0)
                    self.lrc_dict_list.pop(0)

    # 控制槽函数
    def control_btn_func(self, btn):
        if PLAY_SOURCE == 2:
            old_index = self.local_playlist.currentIndex()
        elif PLAY_SOURCE == 1:
            old_index = self.recommend_playlist.currentIndex()
        elif PLAY_SOURCE == 3:
            old_index = self.mv_playlist.currentIndex()
        elif PLAY_SOURCE == 0:
            old_index = self.ui.search_music_list_widget.currentRow() - 1

        if btn == self.ui.volume_btn:
            if self.player.isMuted():
                self.player.setMuted(False)
                value = self.player.volume()
                if value in range(0, 30):
                    self.ui.volume_btn.setIcon(QIcon("images/音量_低.png"))
                elif value in range(30, 70):
                    self.ui.volume_btn.setIcon(QIcon("images/音量_中.png"))
                if value in range(70, 101):
                    self.ui.volume_btn.setIcon(QIcon("images/音量_高.png"))
                self.ui.volume_slider.setValue(value)
                self.ui.volume_label.setText(f"{value}%")
                print("静音: 关闭")
            else:
                self.player.setMuted(True)
                self.ui.volume_btn.setIcon(QIcon("Images/音量_关.png"))
                self.ui.volume_slider.setValue(0)
                self.ui.volume_label.setText("0%")
                print("静音: 开启")
        elif btn == self.ui.pre_play_btn:
            if PLAY_SOURCE == 0:
                print("点击 上一曲")
                return
            elif PLAY_SOURCE == 2:
                if old_index == 0:
                    self.local_playlist.setCurrentIndex(
                        self.local_playlist.mediaCount() - 1
                    )
                else:
                    self.local_playlist.previous()
                new_index = self.local_playlist.currentIndex()
                current_song = f'{self.local_music_dict_list[new_index]["歌名"]}-{self.local_music_dict_list[new_index]["歌手"]}'
            elif PLAY_SOURCE == 1:
                if old_index == 0:
                    self.recommend_playlist.setCurrentIndex(
                        self.recommend_playlist.mediaCount() - 1
                    )
                else:
                    self.recommend_playlist.previous()
                new_index = self.recommend_playlist.currentIndex()
                current_song = f'{self.recommend_music_dict_list[new_index]["歌名"]}-{self.recommend_music_dict_list[new_index]["歌手"]}'
            elif PLAY_SOURCE == 3:
                if old_index == 0:
                    self.mv_playlist.setCurrentIndex(self.mv_playlist.mediaCount() - 1)
                else:
                    self.mv_playlist.previous()
                new_index = self.mv_playlist.currentIndex()
                current_song = f'{self.mv_dict_list[new_index]["歌名"]}-{self.mv_dict_list[new_index]["歌手"]}'

            print(f"上一曲: {current_song}")
        elif btn == self.ui.play_pause_btn:
            if self.player.state() == 1:
                self.player.pause()
                self.ui.play_pause_btn.setIcon(QIcon("Images/暂停.png"))
                print("播放状态: 暂停")
            else:
                self.player.play()
                self.ui.play_pause_btn.setIcon(QIcon("Images/播放中.png"))
                if PLAY_SOURCE == 2:
                    current_song = f'{self.local_music_dict_list[old_index]["歌名"]}-{self.local_music_dict_list[old_index]["歌手"]}'
                elif PLAY_SOURCE == 1:
                    current_song = f'{self.recommend_music_dict_list[old_index]["歌名"]}-{self.recommend_music_dict_list[old_index]["歌手"]}'
                elif PLAY_SOURCE == 3:
                    current_song = f'{self.mv_dict_list[old_index]["歌名"]}-{self.mv_dict_list[old_index]["歌手"]}'
                else:
                    current_song = ""
                print(f"播放状态: 正在播放 - {current_song}")
        elif btn == self.ui.next_play_btn:
            if PLAY_SOURCE == 0:
                print("点击 下一曲")
                return
            elif PLAY_SOURCE == 2:
                if old_index == self.local_playlist.mediaCount() - 1:
                    self.local_playlist.setCurrentIndex(0)
                else:
                    self.local_playlist.next()
                new_index = self.local_playlist.currentIndex()
                current_song = f'{self.local_music_dict_list[new_index]["歌名"]}-{self.local_music_dict_list[new_index]["歌手"]}'
            elif PLAY_SOURCE == 1:
                if old_index == self.recommend_playlist.mediaCount() - 1:
                    self.recommend_playlist.setCurrentIndex(0)
                else:
                    self.recommend_playlist.next()
                new_index = self.recommend_playlist.currentIndex()
                current_song = f'{self.recommend_music_dict_list[new_index]["歌名"]}-{self.recommend_music_dict_list[new_index]["歌手"]}'
            elif PLAY_SOURCE == 3:
                if old_index == self.mv_playlist.mediaCount() - 1:
                    self.mv_playlist.setCurrentIndex(0)
                else:
                    self.mv_playlist.next()
                new_index = self.mv_playlist.currentIndex()
                current_song = f'{self.mv_dict_list[new_index]["歌名"]}-{self.mv_dict_list[new_index]["歌手"]}'
            print(f"下一曲: {current_song}")
        elif btn == self.ui.playmode_btn:
            if PLAY_SOURCE == 0:
                print("点击 播放模式")
                return
            elif PLAY_SOURCE == 2:
                if self.local_playlist.playbackMode() == QMediaPlaylist.Sequential:
                    self.local_playlist.setPlaybackMode(QMediaPlaylist.Loop)
                    self.ui.playmode_btn.setIcon(QIcon("Images/列表循环.png"))
                    print("播放模式: 列表循环")
                elif self.local_playlist.playbackMode() == QMediaPlaylist.Loop:
                    self.local_playlist.setPlaybackMode(QMediaPlaylist.Random)
                    self.ui.playmode_btn.setIcon(QIcon("Images/随机播放.png"))
                    print("播放模式: 随机播放")
                elif self.local_playlist.playbackMode() == QMediaPlaylist.Random:
                    self.local_playlist.setPlaybackMode(
                        QMediaPlaylist.CurrentItemInLoop
                    )
                    self.ui.playmode_btn.setIcon(QIcon("Images/单曲循环.png"))
                    print("播放模式: 单曲循环")
                elif (
                    self.local_playlist.playbackMode()
                    == QMediaPlaylist.CurrentItemInLoop
                ):
                    self.local_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
                    self.ui.playmode_btn.setIcon(QIcon("Images/顺序播放.png"))
                    print("播放模式: 顺序播放")
            elif PLAY_SOURCE == 1:
                if self.recommend_playlist.playbackMode() == QMediaPlaylist.Sequential:
                    self.recommend_playlist.setPlaybackMode(QMediaPlaylist.Loop)
                    self.ui.playmode_btn.setIcon(QIcon("Images/列表循环.png"))
                    print("播放模式: 列表循环")
                elif self.recommend_playlist.playbackMode() == QMediaPlaylist.Loop:
                    self.recommend_playlist.setPlaybackMode(QMediaPlaylist.Random)
                    self.ui.playmode_btn.setIcon(QIcon("Images/随机播放.png"))
                    print("播放模式: 随机播放")
                elif self.recommend_playlist.playbackMode() == QMediaPlaylist.Random:
                    self.recommend_playlist.setPlaybackMode(
                        QMediaPlaylist.CurrentItemInLoop
                    )
                    self.ui.playmode_btn.setIcon(QIcon("Images/单曲循环.png"))
                    print("播放模式: 单曲循环")
                elif (
                    self.recommend_playlist.playbackMode()
                    == QMediaPlaylist.CurrentItemInLoop
                ):
                    self.recommend_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
                    self.ui.playmode_btn.setIcon(QIcon("Images/顺序播放.png"))
                    print("播放模式: 顺序播放")
            elif PLAY_SOURCE == 3:
                if self.mv_playlist.playbackMode() == QMediaPlaylist.Sequential:
                    self.mv_playlist.setPlaybackMode(QMediaPlaylist.Loop)
                    self.ui.playmode_btn.setIcon(QIcon("Images/列表循环.png"))
                    print("播放模式: 列表循环")
                elif self.mv_playlist.playbackMode() == QMediaPlaylist.Loop:
                    self.mv_playlist.setPlaybackMode(QMediaPlaylist.Random)
                    self.ui.playmode_btn.setIcon(QIcon("Images/随机播放.png"))
                    print("播放模式: 随机播放")
                elif self.mv_playlist.playbackMode() == QMediaPlaylist.Random:
                    self.mv_playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
                    self.ui.playmode_btn.setIcon(QIcon("Images/单曲循环.png"))
                    print("播放模式: 单曲循环")
                elif (
                    self.mv_playlist.playbackMode() == QMediaPlaylist.CurrentItemInLoop
                ):
                    self.mv_playlist.setPlaybackMode(QMediaPlaylist.Sequential)
                    self.ui.playmode_btn.setIcon(QIcon("Images/顺序播放.png"))
                    print("播放模式: 顺序播放")
        elif btn == self.ui.lrc_btn:
            print("单击 歌词")
            if PLAY_SOURCE == 3:
                if self.ui.mv_widget.isHidden():
                    self.ui.main_widget.hide()
                    self.ui.mv_widget.show()
                    self.ui.setWindowOpacity(1)
                else:
                    self.ui.mv_widget.hide()
                    self.ui.main_widget.show()
                    self.ui.setWindowOpacity(0.85)
            else:
                if self.ui.lrc_widget.isHidden():
                    self.ui.main_widget.hide()
                    self.ui.lrc_widget.show()

                else:
                    self.ui.lrc_widget.hide()
                    self.ui.main_widget.show()

    # 双击播放
    def list_play_func(self):
        if PLAY_SOURCE == 2:
            # 界面存在标题行
            index = self.ui.mine_music_list_widget.currentRow() - 1
            if index < 0:
                return
            music_tilte = self.local_music_dict_list[index]["歌名"]
            music_artist = self.local_music_dict_list[index]["歌手"]
            self.local_playlist.setCurrentIndex(index)
            self.player.play()
            self.ui.play_pause_btn.setIcon(QIcon("images/播放中.png"))
            current_song = f"{music_tilte}-{music_artist}"
        elif PLAY_SOURCE == 1:
            # 界面存在标题行
            index = self.ui.recommend_music_list_widget.currentRow() - 1
            if index < 0:
                return
            music_tilte = self.recommend_music_dict_list[index]["歌名"]
            music_artist = self.recommend_music_dict_list[index]["歌手"]
            self.recommend_playlist.setCurrentIndex(index)
            self.player.play()
            self.ui.play_pause_btn.setIcon(QIcon("images/播放中.png"))
            current_song = f"{music_tilte}-{music_artist}"
        elif PLAY_SOURCE == 0:
            # 界面存在标题行
            index = self.ui.search_music_list_widget.currentRow() - 1
            if index < 0:
                return
            music_dict = self.search_music_dict_list[index]
            self.play_thread = PlayThread(music_dict, MUSIC_FILE_PATH[0])
            self.play_thread.play_ready_signal.connect(self.play_music)
            self.play_thread.start()
            current_song = ""
        elif PLAY_SOURCE == 3:
            # 界面存在标题行
            index = self.ui.mv_list_widget.currentRow() - 1
            if index < 0:
                return
            music_tilte = self.mv_dict_list[index]["歌名"]
            music_artist = self.mv_dict_list[index]["歌手"]
            self.mv_playlist.setCurrentIndex(index)
            self.player.play()
            self.ui.play_pause_btn.setIcon(QIcon("images/播放中.png"))
            current_song = f"{music_tilte}-{music_artist}"
        print(f"双击 正在播放: {current_song}")

    # 播放线程: 试听音乐
    def play_music(self, music_title, music_artist):
        music_path = f"{MUSIC_FILE_PATH[0]}/{music_title}-{music_artist}.mp3"
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(music_path)))
        self.player.play()
        self.ui.play_pause_btn.setIcon(QIcon("images/播放中.png"))

    # 选项卡切换槽函数
    def tab_btn_func(self, btn):
        global PLAY_SOURCE
        if btn == self.ui.mine_tabbtn:
            print("切换 我的页")
            PLAY_SOURCE = 2
            self.update_playlist()
            self.ui.play_pause_btn.setIcon(QIcon("images/暂停.png"))
            self.ui.playmode_btn.setIcon(QIcon("images/顺序播放.png"))
            self.player.setPlaylist(self.local_playlist)
            self.ui.stackedWidget.setCurrentIndex(1)
        elif btn == self.ui.recommend_tabbtn:
            print("切换 推荐页")
            PLAY_SOURCE = 1
            self.ui.play_pause_btn.setIcon(QIcon("images/暂停.png"))
            self.ui.playmode_btn.setIcon(QIcon("images/顺序播放.png"))
            self.player.setPlaylist(self.recommend_playlist)
            self.ui.stackedWidget.setCurrentIndex(0)
        elif btn == self.ui.about_tabbtn:
            print("切换 关于页")
            self.ui.stackedWidget.setCurrentIndex(3)
        elif btn == self.ui.mv_tabbtn:
            print("切换 视频页")
            PLAY_SOURCE = 3
            self.ui.play_pause_btn.setIcon(QIcon("images/暂停.png"))
            self.ui.playmode_btn.setIcon(QIcon("images/顺序播放.png"))
            self.player.setPlaylist(self.mv_playlist)
            self.player.setVideoOutput(self.ui.mv_play_widget)
            self.ui.stackedWidget.setCurrentIndex(4)

    # 标题栏按钮槽函数
    def header_btn_func(self, btn):
        if btn == self.ui.exit_btn:
            print("单击 退出按钮")
            for filename in os.listdir(MUSIC_FILE_PATH[0]):
                os.remove(f"{MUSIC_FILE_PATH[0]}\{filename}")
            self.ui.close()
        elif btn == self.ui.min_btn:
            print("单击 最小化按钮")
            self.ui.showMinimized()
        elif btn == self.ui.max_btn:
            print("单击 最大化按钮")
            if self.ui.isMaximized():
                self.ui.horizontalLayout_8.setContentsMargins(0, 1, 4, 0)
                self.ui.showNormal()
                self.ui.lrc_cover_label.setMinimumSize(500, 500)
                self.ui.lrc_cover_label.setMaximumSize(500, 500)
                radio = 1.6
                self.ui.mv_play_widget.setMinimumSize(
                    int(720 * radio), int(480 * radio)
                )
                self.ui.mv_play_widget.setMaximumSize(
                    int(720 * radio), int(480 * radio)
                )
                self.ui.max_btn.setIcon(QIcon("Images/最大化.png"))
            else:
                self.ui.horizontalLayout_8.setContentsMargins(3, 1, 4, 3)
                self.ui.showMaximized()
                radio = 3
                self.ui.mv_play_widget.setMinimumSize(
                    int(720 * radio), int(480 * radio)
                )
                self.ui.mv_play_widget.setMaximumSize(
                    int(720 * radio), int(480 * radio)
                )
                self.ui.lrc_cover_label.setMinimumSize(800, 800)
                self.ui.lrc_cover_label.setMaximumSize(800, 800)
                self.ui.max_btn.setIcon(QIcon("Images/最大化还原.png"))
        elif btn == self.ui.search_btn:
            self.ui.setWindowOpacity(0.85)
            if not self.ui.lrc_widget.isHidden():
                self.ui.lrc_widget.hide()
                self.ui.main_widget.show()
            if not self.ui.mv_widget.isHidden():
                self.ui.mv_widget.hide()
                self.ui.main_widget.show()
            print("单击 搜索按钮")
            self.search_playlist_init()
        elif btn == self.ui.set_btn:
            self.ui.setWindowOpacity(0.85)
            self.ui.stackedWidget.setCurrentIndex(3)
            if not self.ui.lrc_widget.isHidden():
                self.ui.lrc_widget.hide()
                self.ui.main_widget.show()
            if not self.ui.mv_widget.isHidden():
                self.ui.mv_widget.hide()
                self.ui.main_widget.show()
            print("单击 设置按钮")
        elif btn == self.ui.theme_btn:
            self.ui.setWindowOpacity(0.85)
            self.ui.stackedWidget.setCurrentIndex(3)
            if not self.ui.lrc_widget.isHidden():
                self.ui.lrc_widget.hide()
                self.ui.main_widget.show()
            if not self.ui.mv_widget.isHidden():
                self.ui.mv_widget.hide()
                self.ui.main_widget.show()
            print("单击 主题按钮")

    # 重写关闭事件
    def closeEvent(self, event):
        if hasattr(self, "search_thread") and self.search_thread.isRunning():
            self.search_thread.terminate()
        if hasattr(self, "download_thread") and self.download_thread.isRunning():
            self.download_thread.terminate()
        if hasattr(self, "play_thread") and self.play_thread.isRunning():
            self.play_thread.terminate()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication([])

    w = Main_Window()
    w.ui.show()

    app.exec_()
