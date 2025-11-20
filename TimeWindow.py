import sys

import requests
import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QHBoxLayout, QPushButton, QDockWidget, QVBoxLayout, \
    QProgressBar
from dateutil import parser
from weather.WeatherCode import TimeOfDay, decode_weather_for_tod

# TODO:


WEATHER_API_KEY = "0bea637c931042fbbe0211531251311"


def get_time_parts(dt_now) -> tuple[int, int, int, int]:
    hour = dt_now.hour
    minute = dt_now.minute
    hour_ones = hour % 10
    hour_tens = (hour % 100) // 10
    minute_ones = minute % 10
    minute_tens = (minute % 100) // 10
    return int(hour_ones), int(hour_tens), int(minute_ones), int(minute_tens)


class TimeWindow(QMainWindow):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.config = main.config

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.init_vars()
        self.init_pix()

        # Time
        self.time_widget = QWidget(self)
        self.setCentralWidget(self.time_widget)
        self.hour_1 = QLabel()
        self.hour_2 = QLabel()
        self.time_seperator = QLabel()
        self.minute_1 = QLabel()
        self.minute_2 = QLabel()

        self.hour_1.setPixmap(self.pix_num_0)
        self.hour_2.setPixmap(self.pix_num_0)
        self.time_seperator.setPixmap(self.pix_colon)
        self.minute_1.setPixmap(self.pix_num_0)
        self.minute_2.setPixmap(self.pix_num_0)

        main_layout = QHBoxLayout(self.time_widget)
        main_layout.addWidget(self.hour_1, 2, Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.hour_2)
        main_layout.addWidget(self.time_seperator, 0, Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(self.minute_1)
        main_layout.addWidget(self.minute_2, 2)

        # Other button
        radio_button = QPushButton(self)
        radio_button.setIcon(QIcon("res/bt_radio.png"))
        radio_button.clicked.connect(self.show_radio)

        details_button = QPushButton(self)
        details_button.setIcon(QIcon("res/bt_details.png"))
        details_button.clicked.connect(self.toggle_detail_display)

        alarm_button = QPushButton(self)
        alarm_button.setIcon(QIcon("res/bt_alarm.png"))
        alarm_button.clicked.connect(self.show_alarm)

        exit_button = QPushButton(self)
        exit_button.setIcon(QIcon("res/bt_exit.png"))
        exit_button.clicked.connect(self.do_exit)

        # Date
        self.dock_bottom = QDockWidget()
        self.dock_bottom.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_bottom)

        date_widget = QWidget(self)
        bottom_layout = QHBoxLayout(date_widget)
        bottom_layout.setContentsMargins(9, 0, 9, 3)
        date_widget.setLayout(bottom_layout)

        bottom_layout.addWidget(details_button, 1, Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addWidget(radio_button, 1, Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addWidget(alarm_button, 1, Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addWidget(exit_button, 1, Qt.AlignmentFlag.AlignLeft)

        self.dow_1 = QLabel()
        self.dow_2 = QLabel()
        self.dow_3 = QLabel()

        self.day_1 = QLabel()
        self.day_2 = QLabel()

        self.dow_1.setPixmap(self.pix_letter["A"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation))
        self.dow_2.setPixmap(self.pix_letter["A"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation))
        self.dow_3.setPixmap(self.pix_letter["A"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation))

        self.set_pixmap_num(self.day_1, 0, 30, 40)
        self.set_pixmap_num(self.day_2, 0, 30, 40)

        bottom_layout.addWidget(self.day_1, 2, Qt.AlignmentFlag.AlignRight)
        bottom_layout.addWidget(self.day_2)
        bottom_layout.addWidget(self.dow_1)
        bottom_layout.addWidget(self.dow_2)
        bottom_layout.addWidget(self.dow_3)

        self.dock_bottom.setWidget(date_widget)

        # Astro
        self.dock_top = QDockWidget()
        self.dock_top.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dock_top)

        # self.dock_top.setVisible(False)

        astro_widget = QWidget(self)
        top_layout = QVBoxLayout(astro_widget)
        astro_widget.setLayout(top_layout)

        # Sun bar
        sun_progress_widget = QWidget(astro_widget)
        sun_layout = QHBoxLayout(sun_progress_widget)
        sun_layout.setContentsMargins(0, 0, 0, 0)
        self.sun_rise_1 = QLabel()
        self.sun_rise_2 = QLabel()
        self.sun_rise_3 = QLabel()
        self.sun_rise_4 = QLabel()
        self.make_time_ui(self.sun_rise_1, self.sun_rise_2, self.sun_rise_3, self.sun_rise_4, sun_layout)

        self.progress_bar_sun = QProgressBar(self)
        self.progress_bar_sun.setTextVisible(False)
        self.progress_bar_sun.setInvertedAppearance(True)
        sun_layout.addWidget(self.progress_bar_sun)

        self.sun_set_1 = QLabel()
        self.sun_set_2 = QLabel()
        self.sun_set_3 = QLabel()
        self.sun_set_4 = QLabel()
        self.make_time_ui(self.sun_set_1, self.sun_set_2, self.sun_set_3, self.sun_set_4, sun_layout)

        top_layout.addWidget(sun_progress_widget)

        # Moon bar
        moon_progress_widget = QWidget(astro_widget)
        moon_layout = QHBoxLayout(moon_progress_widget)  #
        moon_layout.setContentsMargins(0, 0, 0, 0)
        self.moon_rise_1 = QLabel()
        self.moon_rise_2 = QLabel()
        self.moon_rise_3 = QLabel()
        self.moon_rise_4 = QLabel()
        self.make_time_ui(self.moon_rise_1, self.moon_rise_2, self.moon_rise_3, self.moon_rise_4, moon_layout)

        self.progress_bar_moon = QProgressBar(self)
        self.progress_bar_moon.setTextVisible(False)
        self.progress_bar_moon.setInvertedAppearance(True)
        moon_layout.addWidget(self.progress_bar_moon)

        self.moon_set_1 = QLabel()
        self.moon_set_2 = QLabel()
        self.moon_set_3 = QLabel()
        self.moon_set_4 = QLabel()
        self.make_time_ui(self.moon_set_1, self.moon_set_2, self.moon_set_3, self.moon_set_4, moon_layout)

        top_layout.addWidget(moon_progress_widget)

        self.dock_top.setWidget(astro_widget)

        # weather
        self.dock_left = QDockWidget()
        self.dock_left.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_left)

        self.weather_widget = QWidget(self)
        left_layout = QVBoxLayout(self.weather_widget)
        self.weather_widget.setLayout(left_layout)

        # Temp
        current_temp_min_widget = QWidget(self)
        ctw_layout = QHBoxLayout(current_temp_min_widget)
        current_temp_min_widget.setLayout(ctw_layout)

        self.current_temp_min_1 = QLabel()
        self.current_temp_min_2 = QLabel()
        self.current_temp_min_3 = QLabel()
        dot_seperator = QLabel()
        self.current_temp_min_4 = QLabel()

        self.current_temp_min_1.setPixmap(self.pix_dash.scaled(7, 10, Qt.AspectRatioMode.KeepAspectRatio,
                                                               Qt.TransformationMode.SmoothTransformation))
        self.set_pixmap_num(self.current_temp_min_2, 0, 11, 15)
        self.set_pixmap_num(self.current_temp_min_3, 0, 11, 15)
        dot_seperator.setPixmap(self.pix_dot.scaled(3, 10, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
        self.set_pixmap_num(self.current_temp_min_4, 0, 7, 10)

        ctw_layout.addWidget(self.current_temp_min_1, Qt.AlignmentFlag.AlignLeft)
        ctw_layout.addWidget(self.current_temp_min_2)
        ctw_layout.addWidget(self.current_temp_min_3)
        ctw_layout.addWidget(dot_seperator)
        ctw_layout.addWidget(self.current_temp_min_4)
        left_layout.addWidget(current_temp_min_widget, Qt.AlignmentFlag.AlignLeft)

        current_temp_max_widget = QWidget(self)
        ctw_max_layout = QHBoxLayout(current_temp_max_widget)
        current_temp_max_widget.setLayout(ctw_max_layout)

        self.current_temp_max_1 = QLabel()
        self.current_temp_max_2 = QLabel()
        self.current_temp_max_3 = QLabel()
        dot_seperator_max = QLabel()
        self.current_temp_max_4 = QLabel()

        self.current_temp_max_1.setPixmap(self.pix_dash.scaled(7, 10, Qt.AspectRatioMode.KeepAspectRatio,
                                                               Qt.TransformationMode.SmoothTransformation))
        self.set_pixmap_num(self.current_temp_max_2, 0, 11, 15)
        self.set_pixmap_num(self.current_temp_max_3, 0, 11, 15)
        dot_seperator_max.setPixmap(self.pix_dot.scaled(3, 10, Qt.AspectRatioMode.KeepAspectRatio,
                                                        Qt.TransformationMode.SmoothTransformation))
        self.set_pixmap_num(self.current_temp_max_4, 0, 7, 10)

        ctw_max_layout.addWidget(self.current_temp_max_1, Qt.AlignmentFlag.AlignLeft)
        ctw_max_layout.addWidget(self.current_temp_max_2)
        ctw_max_layout.addWidget(self.current_temp_max_3)
        ctw_max_layout.addWidget(dot_seperator_max)
        ctw_max_layout.addWidget(self.current_temp_max_4)
        left_layout.addWidget(current_temp_max_widget, Qt.AlignmentFlag.AlignLeft)

        # Rain
        current_rain_widget = QWidget(self)
        crw_layout = QHBoxLayout(current_rain_widget)
        current_rain_widget.setLayout(crw_layout)

        self.current_rain_1 = QLabel()
        self.current_rain_2 = QLabel()

        self.set_pixmap_num(self.current_rain_1, 0, 15, 20)
        self.set_pixmap_num(self.current_rain_2, 0, 15, 20)

        crw_layout.addWidget(self.current_rain_1, Qt.AlignmentFlag.AlignLeft)
        crw_layout.addWidget(self.current_rain_2, 4, Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(current_rain_widget, Qt.AlignmentFlag.AlignLeft)

        self.dock_left.setWidget(self.weather_widget)
        if not self.config.get('Clock', 'show_details'):
            # self.dock_bottom.setVisible(False)
            self.dock_top.setVisible(False)
            self.dock_left.setVisible(False)

        self.update()

        # Interval Timer (Every 20 seconds)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20 * 1000)

    def show_radio(self):
        self.main.show_radio_wind()

    def show_alarm(self):
        pass

    def toggle_detail_display(self):
        # self.dock_bottom.setVisible(not self.dock_bottom.isVisible())
        self.dock_top.setVisible(not self.dock_top.isVisible())
        self.dock_left.setVisible(not self.dock_left.isVisible())
        self.config.set('Clock', 'show_details', str(self.dock_top.isVisible()))
        self.main.write_config()

    def do_exit(self):
        sys.exit()

    def make_time_ui(self, label_1: QLabel, label_2: QLabel, label_3: QLabel, label_4: QLabel, sun_layout: QHBoxLayout):

        sun_rise_seperator = QLabel()

        self.set_pixmap_num(label_1, 0, 15, 20)
        self.set_pixmap_num(label_2, 0, 15, 20)
        sun_rise_seperator.setPixmap(self.pix_colon.scaled(6, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation))
        self.set_pixmap_num(label_3, 0, 15, 20)
        self.set_pixmap_num(label_4, 0, 15, 20)

        sun_layout.addWidget(label_1)
        sun_layout.addWidget(label_2)
        sun_layout.addWidget(sun_rise_seperator)
        sun_layout.addWidget(label_3)
        sun_layout.addWidget(label_4)

    def init_vars(self):
        self.last_update_astro = None
        self.last_update_day = None
        self.moon_minutes = None
        self.moon_minutes_total = None
        self.night_minutes = None
        self.current_sunset = None
        self.night_minutes_total = None
        self.current_sunrise = None
        self.sun_minutes = 0
        self.daylight_minutes_total = 0
        self.current_is_moon_up = None
        self.current_moonset = None
        self.current_moonrise = None
        self.pix_letter = None
        self.pix_nums = None
        self.current_is_sun_up = None
        self.last_update_day = None
        self.pix_num_0 = None
        self.pix_num_1 = None
        self.pix_num_2 = None
        self.pix_num_3 = None
        self.pix_num_4 = None
        self.pix_num_5 = None
        self.pix_num_6 = None
        self.pix_num_7 = None
        self.pix_num_8 = None
        self.pix_num_9 = None
        self.pix_colon = None
        self.pix_dash = None
        self.pix_dot = None
        self.pix_blank = None
        self.pix_let_A = None
        self.pix_let_D = None
        self.pix_let_E = None
        self.pix_let_F = None
        self.pix_let_H = None
        self.pix_let_I = None
        self.pix_let_M = None
        self.pix_let_N = None
        self.pix_let_O = None
        self.pix_let_R = None
        self.pix_let_S = None
        self.pix_let_T = None
        self.pix_let_U = None
        self.pix_let_V = None
        self.pix_let_W = None

    def init_pix(self):
        self.pix_num_0 = QPixmap("res/0.png")
        self.pix_num_1 = QPixmap("res/1.png")
        self.pix_num_2 = QPixmap("res/2.png")
        self.pix_num_3 = QPixmap("res/3.png")
        self.pix_num_4 = QPixmap("res/4.png")
        self.pix_num_5 = QPixmap("res/5.png")
        self.pix_num_6 = QPixmap("res/6.png")
        self.pix_num_7 = QPixmap("res/7.png")
        self.pix_num_8 = QPixmap("res/8.png")
        self.pix_num_9 = QPixmap("res/9.png")
        self.pix_colon = QPixmap("res/colon.png")
        self.pix_dash = QPixmap("res/dash.png")
        self.pix_dot = QPixmap("res/dot.png")
        self.pix_blank = QPixmap("res/blank.png")
        self.pix_let_A = QPixmap("res/A.png")
        self.pix_let_D = QPixmap("res/D.png")
        self.pix_let_E = QPixmap("res/E.png")
        self.pix_let_F = QPixmap("res/F.png")
        self.pix_let_H = QPixmap("res/H.png")
        self.pix_let_I = QPixmap("res/I.png")
        self.pix_let_M = QPixmap("res/M.png")
        self.pix_let_N = QPixmap("res/N.png")
        self.pix_let_O = QPixmap("res/O.png")
        self.pix_let_R = QPixmap("res/R.png")
        self.pix_let_S = QPixmap("res/S.png")
        self.pix_let_T = QPixmap("res/T.png")
        self.pix_let_U = QPixmap("res/U.png")
        self.pix_let_V = QPixmap("res/V.png")
        self.pix_let_W = QPixmap("res/W.png")
        self.pix_nums = [self.pix_num_0, self.pix_num_1, self.pix_num_2, self.pix_num_3, self.pix_num_4, self.pix_num_5,
                         self.pix_num_6, self.pix_num_7, self.pix_num_8, self.pix_num_9]
        self.pix_letter = {"A": self.pix_let_A, "D": self.pix_let_D, "E": self.pix_let_E, "F": self.pix_let_F,
                           "H": self.pix_let_H, "I": self.pix_let_I, "M": self.pix_let_M, "N": self.pix_let_N,
                           "O": self.pix_let_O, "R": self.pix_let_R, "S": self.pix_let_S, "T": self.pix_let_T,
                           "U": self.pix_let_U, "V": self.pix_let_V, "W": self.pix_let_W}

    def update(self):
        dt_now = datetime.datetime.now()
        week_day = dt_now.isoweekday()

        self.update_date_time(dt_now)

        if self.last_update_astro is None or (
                dt_now - self.last_update_astro).total_seconds() > 3600:  # check every hour
            self.last_update_astro = dt_now
            self.weather(dt_now)

        if self.last_update_day is None or self.last_update_day != datetime.date.today():
            self.last_update_day = datetime.date.today()
            self.make_dow(week_day)

        # self.toggle_detail_display()

    def update_date_time(self, dt_now):
        # Time
        hour_ones, hour_tens, minute_ones, minute_tens = get_time_parts(dt_now)
        self.set_pixmap_num(self.hour_1, hour_tens)
        self.set_pixmap_num(self.hour_2, hour_ones)
        self.set_pixmap_num(self.minute_1, minute_tens)
        self.set_pixmap_num(self.minute_2, minute_ones)

        # Date
        day = dt_now.day
        day_ones = day % 10
        day_tens = (day % 100) // 10

        self.set_pixmap_num(self.day_1, day_tens, 30, 40)
        self.set_pixmap_num(self.day_2, day_ones, 30, 40)

        self.time_widget.repaint()
        self.dock_bottom.repaint()

    def make_dow(self, week_day: int):
        # 05:05 AM
        # Update sunrise
        if not self.current_sunrise is None:
            hour_ones, hour_tens, minute_ones, minute_tens = get_time_parts(self.current_sunrise)
            self.set_pixmap_num(self.sun_rise_1, hour_tens, 15, 20)
            self.set_pixmap_num(self.sun_rise_2, hour_ones, 15, 20)
            self.set_pixmap_num(self.sun_rise_3, minute_tens, 15, 20)
            self.set_pixmap_num(self.sun_rise_4, minute_ones, 15, 20)

        # Update sunset
        if not self.current_sunset is None:
            hour_ones, hour_tens, minute_ones, minute_tens = get_time_parts(self.current_sunset)
            self.set_pixmap_num(self.sun_set_1, hour_tens, 15, 20)
            self.set_pixmap_num(self.sun_set_2, hour_ones, 15, 20)
            self.set_pixmap_num(self.sun_set_3, minute_tens, 15, 20)
            self.set_pixmap_num(self.sun_set_4, minute_ones, 15, 20)

        # Update moonrise
        if not self.current_moonrise is None:
            hour_ones, hour_tens, minute_ones, minute_tens = get_time_parts(self.current_moonrise)
            self.set_pixmap_num(self.moon_rise_1, hour_tens, 15, 20)
            self.set_pixmap_num(self.moon_rise_2, hour_ones, 15, 20)
            self.set_pixmap_num(self.moon_rise_3, minute_tens, 15, 20)
            self.set_pixmap_num(self.moon_rise_4, minute_ones, 15, 20)

        # Update sunrise
        if not self.current_moonset is None:
            hour_ones, hour_tens, minute_ones, minute_tens = get_time_parts(self.current_moonset)
            self.set_pixmap_num(self.moon_set_1, hour_tens, 15, 20)
            self.set_pixmap_num(self.moon_set_2, hour_ones, 15, 20)
            self.set_pixmap_num(self.moon_set_3, minute_tens, 15, 20)
            self.set_pixmap_num(self.moon_set_4, minute_ones, 15, 20)

        match week_day:
            case 1:
                # Monday
                self.dow_1.setPixmap(self.pix_letter["M"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["O"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["N"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
            case 2:
                # Tuesday
                self.dow_1.setPixmap(self.pix_letter["T"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["U"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["E"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))

            case 3:
                # Wednesday
                self.dow_1.setPixmap(self.pix_letter["W"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["E"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["D"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))

            case 4:
                # Thursday
                self.dow_1.setPixmap(self.pix_letter["T"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["H"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["U"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))

            case 5:
                # Friday
                self.dow_1.setPixmap(self.pix_letter["F"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["R"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["I"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))

            case 6:
                # Saturday
                self.dow_1.setPixmap(self.pix_letter["S"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["A"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["T"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))

            case 7:
                # Sunday
                self.dow_1.setPixmap(self.pix_letter["S"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_2.setPixmap(self.pix_letter["U"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
                self.dow_3.setPixmap(self.pix_letter["N"].scaled(30, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation))
        self.dock_bottom.repaint()

    def weather(self, dt_now):
        print("Checking weather")
        complete_url = "https://api.weatherapi.com/v1/forecast.json?key=" + WEATHER_API_KEY + "&q=-26.063018646041453,27.961667533360554&aqi=no&days=3"

        response = requests.get(complete_url)
        data = response.json()
        if response.status_code == 200:

            # Set min and max temps
            current_temp_max = data["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
            current_temp_min = data["forecast"]["forecastday"][0]["day"]["mintemp_c"]

            current_wind = data["current"]["wind_kph"]
            current_gust = data["current"]["gust_kph"]
            self.update_temp(current_temp_min, self.current_temp_min_1, self.current_temp_min_2,
                             self.current_temp_min_3, self.current_temp_min_4)
            self.update_temp(current_temp_max, self.current_temp_max_1, self.current_temp_max_2,
                             self.current_temp_max_3, self.current_temp_max_4)

            current_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]
            current_rain_str = str(current_rain)
            if len(current_rain_str) == 0:  # null?
                self.current_rain_1.setPixmap(self.pix_nums[0].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                      Qt.TransformationMode.SmoothTransformation))
                self.current_rain_2.setPixmap(self.pix_nums[0].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                      Qt.TransformationMode.SmoothTransformation))
            if len(current_rain_str) == 1:  # 0-9%
                self.current_rain_1.setPixmap(self.pix_nums[0].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                      Qt.TransformationMode.SmoothTransformation))
                self.current_rain_2.setPixmap(
                    self.pix_nums[int(current_rain_str[0])].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                   Qt.TransformationMode.SmoothTransformation))
            elif len(current_rain_str) == 3:  # 100% ?
                self.current_rain_1.setPixmap(self.pix_nums[9].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                      Qt.TransformationMode.SmoothTransformation))
                self.current_rain_2.setPixmap(self.pix_nums[9].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                      Qt.TransformationMode.SmoothTransformation))
            else:
                self.current_rain_1.setPixmap(
                    self.pix_nums[int(current_rain_str[0])].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                   Qt.TransformationMode.SmoothTransformation))
                self.current_rain_2.setPixmap(
                    self.pix_nums[int(current_rain_str[1])].scaled(15, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                                   Qt.TransformationMode.SmoothTransformation))

            self.weather_widget.repaint()

            # Sun and moon rise and set
            self.current_sunrise = parser.parse(data["forecast"]["forecastday"][0]["astro"]["sunrise"])
            self.current_sunset = parser.parse(data["forecast"]["forecastday"][0]["astro"]["sunset"])
            self.current_moonrise = parser.parse(data["forecast"]["forecastday"][0]["astro"]["moonrise"])
            self.current_moonset = parser.parse(data["forecast"]["forecastday"][0]["astro"]["moonset"])
            if self.current_moonrise > self.current_moonset:
                self.current_moonset = parser.parse(
                    data["forecast"]["forecastday"][1]["astro"]["moonset"]) + datetime.timedelta(days=1)

            self.old_is_sun_up = self.current_is_sun_up
            self.old_is_moon_up = self.current_is_moon_up

            self.current_is_sun_up = self.current_sunrise <= dt_now <= self.current_sunset
            self.current_is_moon_up = self.current_moonrise <= dt_now <= self.current_moonset

            if self.current_is_sun_up:
                self.daylight_minutes_total = (self.current_sunset - self.current_sunrise).seconds / 60
                self.sun_minutes = (self.current_sunset - dt_now).seconds / 60
                self.night_minutes_total = 0
                self.night_minutes = 0
            elif not self.current_is_sun_up:
                self.daylight_minutes_total = 0
                self.sun_minutes = 0
                if dt_now < self.current_sunrise:
                    self.night_minutes = (self.current_sunrise - dt_now).seconds / 60
                    # Not yet today
                elif dt_now > self.current_sunset:
                    # load tomorrows sun data
                    self.current_sunrise = parser.parse(
                        data["forecast"]["forecastday"][1]["astro"]["sunrise"]) + datetime.timedelta(days=1)
                    self.night_minutes_total = (self.current_sunrise - self.current_sunset).seconds / 60
                    self.current_sunset = parser.parse(
                        data["forecast"]["forecastday"][1]["astro"]["sunset"]) + datetime.timedelta(days=1)
                    self.night_minutes = (self.current_sunrise - dt_now).seconds / 60

            if self.current_is_moon_up:
                self.moon_minutes_total = (self.current_moonset - self.current_moonrise).seconds / 60
                self.moon_minutes = (self.current_moonset - dt_now).seconds / 60
                self.progress_bar_moon.setRange(0, int(self.moon_minutes_total))
            elif not self.current_is_moon_up:
                self.moon_minutes_total = 1
                self.moon_minutes = 0
                self.progress_bar_moon.setRange(0, int(self.moon_minutes_total))

            if self.current_is_sun_up:
                if self.old_is_sun_up != self.current_is_sun_up:
                    self.old_is_sun_up = self.current_is_sun_up
                    # make yellow/orange
                    self.progress_bar_sun.setRange(0, int(self.daylight_minutes_total))
                    self.progress_bar_sun.setStyleSheet("""
                    QProgressBar {
                        background-color: rgba(237, 162, 7, 128);
                    }
                    QProgressBar::chunk {
                        background-color: rgba(237, 162, 7, 255);
                    }
                    """)

                self.progress_bar_sun.setValue(int(self.sun_minutes))
                self.progress_bar_sun.repaint()
            else:  # night
                if self.old_is_sun_up != self.current_is_sun_up:
                    self.old_is_sun_up = self.current_is_sun_up
                    # make yellow/orange
                    self.progress_bar_sun.setRange(0, int(self.night_minutes_total))
                    self.progress_bar_sun.setStyleSheet("""
                                        QProgressBar {
                                            background-color: rgba(2, 18, 178, 128);
                                        }
                                        QProgressBar::chunk {
                                            background-color: rgba(2, 18, 178, 255);
                                        }
                                        """)

                self.progress_bar_sun.setValue(int(self.night_minutes))
                self.progress_bar_sun.repaint()

            if self.old_is_moon_up != self.current_is_moon_up:
                self.old_is_moon_up = self.current_is_moon_up
                self.progress_bar_moon.setRange(0, int(self.moon_minutes_total))
                self.progress_bar_moon.setStyleSheet("""
                                                        QProgressBar {
                                                            background-color: rgba(0, 0, 0, 128);
                                                        }
                                                        QProgressBar::chunk {
                                                            background-color: rgba(255, 255, 255, 255);
                                                        }
                                                        """)

            if self.current_is_moon_up:
                self.progress_bar_moon.setValue(int(self.sun_minutes))
                self.progress_bar_moon.repaint()

            # Current conditions
            current_cond = data["current"]["condition"]["code"]
            if (self.current_sunrise + datetime.timedelta(hours=1)).time() >= dt_now.time() >= (
                    self.current_sunrise - datetime.timedelta(
                hours=1)).time():  # sunrise is from an hour before and after sunrise
                tod = TimeOfDay.SUNRISE
            elif (self.current_sunrise + datetime.timedelta(hours=1)).time() < dt_now.time() < (
                    self.current_sunset - datetime.timedelta(hours=1)).time():
                tod = TimeOfDay.DAY
            elif (self.current_sunrise + datetime.timedelta(hours=1)).time() >= dt_now.time() >= (
                    self.current_sunrise - datetime.timedelta(hours=1)).time():
                tod = TimeOfDay.SUNSET
            else:
                tod = TimeOfDay.NIGHT

            bg_image_file_name = decode_weather_for_tod(current_cond, tod)
            self.setStyleSheet("TimeWindow { background-image: url(\"res/" + bg_image_file_name + "\") }")

            current_moon = data["forecast"]["forecastday"][0]["astro"]["moon_phase"]
            current_moonrise = data["forecast"]["forecastday"][0]["astro"]["moonrise"]
            current_moonset = data["forecast"]["forecastday"][0]["astro"]["moonset"]
            tomorrow_temp_max = data["forecast"]["forecastday"][1]["day"]["maxtemp_c"]
            tomorrow_temp_min = data["forecast"]["forecastday"][1]["day"]["mintemp_c"]
            tomorrow_temp_ave = data["forecast"]["forecastday"][1]["day"]["avgtemp_c"]
            tomorrow_wind = data["forecast"]["forecastday"][1]["day"]["maxwind_kph"]
            tomorrow_rain = data["forecast"]["forecastday"][1]["day"]["daily_chance_of_rain"]
            tomorrow_cond = data["forecast"]["forecastday"][1]["day"]["condition"]["text"]
            tomorrow_sunrise = data["forecast"]["forecastday"][1]["astro"]["sunrise"]
            tomorrow_sunset = data["forecast"]["forecastday"][1]["astro"]["sunset"]
            tomorrow_moon = data["forecast"]["forecastday"][1]["astro"]["moon_phase"]
            tomorrow_moonrise = data["forecast"]["forecastday"][1]["astro"]["moonrise"]
            tomorrow_moonset = data["forecast"]["forecastday"][1]["astro"]["moonset"]
        else:
            print(" City Not Found ")

    def update_temp(self, temp, current_temp_1, current_temp_2, current_temp_3, current_temp_4):
        temp_str = str(temp)
        ten_is_zero = False
        index = 0
        if temp < 0.0:
            # -1.1
            current_temp_1.setPixmap(self.pix_dash.scaled(7, 10, Qt.AspectRatioMode.KeepAspectRatio,
                                                          Qt.TransformationMode.SmoothTransformation))
            ten_is_zero = len(temp_str) == 4
            index += 1
        else:
            # 1.1
            current_temp_1.setPixmap(self.pix_blank.scaled(11, 15, Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation))
            ten_is_zero = len(temp_str) == 3

        if ten_is_zero:
            self.set_pixmap_num(current_temp_2, 0, 11, 15)
        else:
            self.set_pixmap_num(current_temp_2, int(temp_str[index]), 11, 15)
            index += 1

        self.set_pixmap_num(current_temp_3, int(temp_str[index]), 11, 15)
        index += 2
        self.set_pixmap_num(current_temp_4, int(temp_str[index]), 7, 10)

    def set_pixmap_num(self, element, number, width_scale=0, height_scale=0):
        if width_scale > 0 and height_scale > 0:
            element.setPixmap(
                self.pix_nums[number].scaled(width_scale, height_scale, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
        else:
            element.setPixmap(self.pix_nums[number])
