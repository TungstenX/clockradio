"""
    url = "https://edge.iono.fm/xhls/57_high.m3u8" #"https://edge.iono.fm/xice/57_medium.aac?ver=768196"
    url_rock = "https://edge.iono.fm/xhls/303_high.m3u8"
    r = requests.get(url, stream=True)

    player = vlc.MediaPlayer()
    player.set_mrl(url)
    player.play()

    # keep your program alive while it's playing
    import time_util

    while True:
        time_util.sleep(1)
"""
import json
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QMainWindow, QComboBox, QVBoxLayout, QWidget, QPushButton, QGestureEvent,
                             QHBoxLayout, QDockWidget)

class RadioWindow(QMainWindow):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.config = main.config

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        window_layout = QVBoxLayout()
        window_widget = QWidget()
        window_widget.setLayout(window_layout)

        channels_dropdown = QComboBox(self)
        print(self.config.get('Radio', 'channels').replace("'","\""))
        self.channels = json.loads(self.config.get("Radio", "channels").replace("'","\""))
        current_channel_index = int(self.config.get("Radio", "current_channel"))
        for channel in self.channels:
            channels_dropdown.addItem(channel["name"], channel)
            if channel["id"] == current_channel_index:
                self.current_channel = channel

        channels_dropdown.setCurrentIndex(current_channel_index)
        channels_dropdown.currentIndexChanged.connect(self.index_changed)
        window_layout.addWidget(channels_dropdown)

        self.play_button = QPushButton("\u23F5", self)
        self.play_button.clicked.connect(self.play_pause)
        window_layout.addWidget(self.play_button)

        ### Bottom Dock
        self.dock_bottom = QDockWidget()
        self.dock_bottom.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_bottom)

        other_widget = QWidget(self)
        bottom_layout = QHBoxLayout(other_widget)
        bottom_layout.setContentsMargins(9, 0, 9, 3)
        other_widget.setLayout(bottom_layout)

        clock_button = QPushButton(self)
        clock_button.setIcon(QIcon("res/bt_clock.png"))
        clock_button.clicked.connect(self.show_clock)
        bottom_layout.addWidget(clock_button,1, Qt.AlignmentFlag.AlignLeft)
        self.dock_bottom.setWidget(other_widget)

        self.setCentralWidget(window_widget)
        # self.radio = threading.Thread(target=self.radio_thread, args=(1,), daemon=True)

    def show_clock(self):
        self.main.show_clock_wind()

    def index_changed(self, i):
        found_channel = False
        for channel in self.channels:
            if channel["id"] == i:
                self.current_channel = channel
                found_channel = True
                break

        if found_channel:
            self.config.set("Radio", "current_channel", str(i))
            self.main.write_config()
            self.main.set_station(self.current_channel["url"])

    def reload_station(self):
        pass

    def play_pause(self):
        if self.main.toggle_play():
            self.play_button.setText("\u23F9")
        else:
            self.play_button.setText("\u23F5")

    def event(self, event):
        if event.type() == QGestureEvent:
            print("Gesture even")
        return super().event(event)

"""
    def radio_thread(self):
        url = "https://edge.iono.fm/xhls/57_high.m3u8"  # "https://edge.iono.fm/xice/57_medium.aac?ver=768196"
        url_rock = "https://edge.iono.fm/xhls/303_high.m3u8"
        #r = requests.get(url, stream=True)
"""


