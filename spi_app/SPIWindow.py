import copy
import datetime
import event_emitter as events
import logging
import os
import threading
import time

from enum import Enum
from interval_timer import IntervalTimer
from pathlib import Path
from PIL import Image

from spi_app.SPIClient import SPIClient
from spi_app.radio.RadioClient import RadioClient
from spi_app.time_util.TimeUtilsCR import TimeUtilsCR
from spi_app.ui.MSP3520 import MSP3520
from spi_app.ui.UIUtil import UIUtil
from spi_app.weather.WeatherCode import WeatherCode, TimeOfDay

DIGIT_SIZE_X_LARGE = (126, 95)
DIGIT_SPACE_X_LARGE = 9
DIGIT_SIZE_MEDIUM = (40, 30)
DIGIT_SIZE_SMALL = (20, 15)
DIGIT_SIZE_X_SMALL = (10, 7)

COLON_SIZE_X_LARGE = (126, 19)
COLON_SIZE_MEDIUM = (20, 6)
BUTTON_SIZE = (30, 30)
BUTTON_SELECTOR_SIZE = (40, 40)

em = events.EventEmitter()
press_lock = threading.Lock()


class ActiveWindow(Enum):
    CLOCK = 0
    ALARM = 1
    RADIO = 2

    @staticmethod
    def from_str(label):
        match label:
            case "CLOCK":
                return ActiveWindow.CLOCK
            case "ALARM":
                return ActiveWindow.ALARM
            case "RADIO":
                return ActiveWindow.RADIO
            case _:
                return ActiveWindow.CLOCK


def adjust_opacity(image, opacity):
    """Adjust the opacity of an RGBA image"""
    img_rgba = image.convert('RGBA')
    data = img_rgba.getdata()

    new_data = []
    for item in data:
        # Modify alpha value while keeping RGB same
        new_data.append((item[0], item[1], item[2],
                         int(item[3] * opacity)))

    img_rgba.putdata(new_data)
    return img_rgba


class SPIWindow:
    def __init__(self, main, home_dir, start_test_mode):
        super().__init__()

        self.main = main
        self.home_dir = home_dir
        self.event_emitter = main.em

        self.xy_moon = None
        self.xy_sun = None
        self.last_update_astro = None
        self.last_update_day = None
        self.moon = None
        self.rain_pix = None
        self.min_max_pix = None
        self.day = None
        self.time_date = None
        self.rise_set_pix = None
        self.colon_medium = None
        self.colon = None
        self.bg_pix = None
        self.bg_file = None
        self.weather_code = None
        self.sun = None
        self.moon_bar = None
        self.sun_bar = None
        self.button = None
        self.xy_button = None
        self.xy_rain = None
        self.xy_min_max = None
        self.xy_day = None
        self.xy_moon_bar = None
        self.xy_sun_bar = None
        self.xy_rise_set = None
        self.xy_time_colon = None
        self.xy_time_date = None
        self.x_offset_sun_moon = None
        self.y_offset_sun_moon = None
        self.xy_radio_button = None
        self.ui_util = None
        self.time_util = None
        self.which_window = None
        self.spi_client = None
        self.radio_client = None
        self.msp = None
        self.screen_pressed = False
        self.timer_rerender_dot = None
        self.screen_press_x = None
        self.screen_press_y = None
        self.last_press_time = None
        self.button_selector = None
        self.button_selected = None
        self.show_details = None
        self.last_temp_log = None
        self.logger = logging.getLogger()

        self.init(home_dir, start_test_mode)
        tempo = int(self.main.config.get("General", "interval"))
        for interval in IntervalTimer(tempo):
            self.logger.info(interval)
            self.update()
            # File path
            stop = os.path.join(home_dir, "stop")
            stop_file = Path(stop)
            # Check if the file exists
            if stop_file.exists():
                self.logger.info("Found stop file")
                break

        self.close()

    def close(self):
        if not self.spi_client is None:
            self.render_blank()
            time.sleep(2)
            self.spi_client.close()

    def init(self, home_dir, start_test_mode):
        self.time_util = TimeUtilsCR(self.main, home_dir)
        self.ui_util = UIUtil(self.home_dir)
        if not start_test_mode:
            self.spi_client = SPIClient(self.event_emitter)  # self
            self.render_blank()

        y_offset_mid = 18
        y_offset_buttons = 33
        x_offset_buttons = 23
        y_offset_dow = 33
        x_offset_dow = 23
        self.y_offset_sun_moon = 33
        self.x_offset_sun_moon = 23

        self.which_window = ActiveWindow.from_str(self.main.config.get("General", "start_up"))

        self.show_details = self.main.config.getboolean('Clock', 'show_details')

        # Time:
        self.xy_time_date = [(120, 102), (120, 168), (120, 252), (120, 318),
                             (275 - x_offset_dow, 295 - y_offset_dow), (275 - x_offset_dow, 330 - y_offset_dow)]
        self.xy_time_colon = (120, 234)

        self.xy_rise_set = {
            "sun": {
                "rise": [(5 + self.x_offset_sun_moon, 10 + self.y_offset_sun_moon),
                         (5 + self.x_offset_sun_moon, 28 + self.y_offset_sun_moon),
                         (5 + self.x_offset_sun_moon, 55 + self.y_offset_sun_moon),
                         (5 + self.x_offset_sun_moon, 73 + self.y_offset_sun_moon)],
                "set": [(5 + self.x_offset_sun_moon, 392 - self.y_offset_sun_moon),
                        (5 + self.x_offset_sun_moon, 410 - self.y_offset_sun_moon),
                        (5 + self.x_offset_sun_moon, 437 - self.y_offset_sun_moon),
                        (5 + self.x_offset_sun_moon, 455 - self.y_offset_sun_moon)]
            },
            "moon": {
                "rise": [(28 + self.x_offset_sun_moon, 10 + self.y_offset_sun_moon),
                         (28 + self.x_offset_sun_moon, 28 + self.y_offset_sun_moon),
                         (28 + self.x_offset_sun_moon, 55 + self.y_offset_sun_moon),
                         (28 + self.x_offset_sun_moon, 73 + self.y_offset_sun_moon)],
                "set": [(28 + self.x_offset_sun_moon, 392 - self.y_offset_sun_moon),
                        (28 + self.x_offset_sun_moon, 410 - self.y_offset_sun_moon),
                        (28 + self.x_offset_sun_moon, 437 - self.y_offset_sun_moon),
                        (28 + self.x_offset_sun_moon, 455 - self.y_offset_sun_moon)]
            },
            "colon": [(5 + self.x_offset_sun_moon, 46 + self.y_offset_sun_moon),
                      (5 + self.x_offset_sun_moon, 427 - self.y_offset_sun_moon),
                      (28 + self.x_offset_sun_moon, 46 + self.y_offset_sun_moon),
                      (28 + self.x_offset_sun_moon, 427 - self.y_offset_sun_moon)]
        }

        # Sun / Moon bar:
        self.xy_sun_bar = (5 + self.x_offset_sun_moon, 94 + self.y_offset_sun_moon)
        self.xy_moon_bar = (28 + self.x_offset_sun_moon, 94 + self.y_offset_sun_moon)

        # Date:
        self.xy_day = [(275 - x_offset_dow, 370 - y_offset_dow), (275 - x_offset_dow, 405 - y_offset_dow),
                       (275 - x_offset_dow, 440 - y_offset_dow)]

        # Min max
        self.xy_min_max = {
            "today": {
                "min": [(166, y_offset_mid + 10), (166, y_offset_mid + 28), (166, y_offset_mid + 46),
                        (166, y_offset_mid + 64), (166, y_offset_mid + 73)],
                "max": [(143, y_offset_mid + 10), (143, y_offset_mid + 28), (143, y_offset_mid + 46),
                        (143, y_offset_mid + 64), (143, y_offset_mid + 73)]
            },
            "tomorrow": {
                "min": [(166, 397 - y_offset_mid), (166, 415 - y_offset_mid), (166, 433 - y_offset_mid),
                        (166, 451 - y_offset_mid), (166, 460 - y_offset_mid)],
                "max": [(143, 397 - y_offset_mid), (143, 415 - y_offset_mid), (143, 433 - y_offset_mid),
                        (143, 451 - y_offset_mid), (143, 460 - y_offset_mid)]
            }
        }
        # Rain
        self.xy_rain = {
            "today": [(120, y_offset_mid + 28), (120, y_offset_mid + 46), (120, y_offset_mid + 64)],
            "tomorrow": [(120, 415 - y_offset_mid), (120, 433 - y_offset_mid), (120, 451 - y_offset_mid)]
        }

        # Button:
        self.xy_button = {
            "alarm": (285 - x_offset_buttons, y_offset_buttons + 10),
            "clock": (146, 50),
            "details": (285 - x_offset_buttons, y_offset_buttons + 80),
            "exit": (285 - x_offset_buttons, y_offset_buttons + 115),
            "radio": (285 - x_offset_buttons, y_offset_buttons + 45)
        }
        self.xy_radio_button = {
            "play": (127, 205),
            "station 1": (246, 88),
            "station 2": (248, 355)
        }
        self.button = {
            "alarm": self.ui_util.buttons["alarm"].resize(BUTTON_SIZE),
            "clock": self.ui_util.buttons["clock"].resize(BUTTON_SIZE),
            "details": self.ui_util.buttons["details"].resize(BUTTON_SIZE),
            "exit": self.ui_util.buttons["exit"].resize(BUTTON_SIZE),
            "radio": self.ui_util.buttons["radio"].resize(BUTTON_SIZE)
        }
        self.button_selector = self.ui_util.buttons_selector.resize(BUTTON_SELECTOR_SIZE)
        self.button_selected = "details"

        self.sun_bar = self.ui_util.bar["sun_bar"]
        self.moon_bar = self.ui_util.bar["moon_bar"]

        self.sun = self.ui_util.sun

        # Opening the primary image (used in background)
        self.weather_code = WeatherCode(home_dir)
        match self.which_window:
            case ActiveWindow.CLOCK:
                self.bg_file = self.weather_code.decode_weather_for_tod(0, TimeOfDay.DAY)
            case ActiveWindow.RADIO:
                self.bg_file = self.ui_util.bg["radio"]
        self.bg_pix = Image.open(self.bg_file)

        self.colon = self.ui_util.pix_colon
        self.colon_medium = self.colon.resize(COLON_SIZE_MEDIUM)
        self.rise_set_pix = {
            "sun": {
                "rise": [None, None, None, None],
                "set": [None, None, None, None]
            },
            "moon": {
                "rise": [None, None, None, None],
                "set": [None, None, None, None]
            },
            "colon": [self.colon_medium, self.colon_medium, self.colon_medium, self.colon_medium]
        }
        self.time_date = [None, None, None, None, None, None]
        self.day = [None, None, None]

        self.min_max_pix = {
            "today": {
                "min": [None, None, None, self.ui_util.pix_dot.resize(COLON_SIZE_MEDIUM), None],
                "max": [None, None, None, self.ui_util.pix_dot.resize(COLON_SIZE_MEDIUM), None]
            },
            "tomorrow": {
                "min": [None, None, None, self.ui_util.pix_dot.resize(COLON_SIZE_MEDIUM), None],
                "max": [None, None, None, self.ui_util.pix_dot.resize(COLON_SIZE_MEDIUM), None]
            }
        }
        self.rain_pix = {
            "today": [None, None, None],
            "tomorrow": [None, None, None]
        }

        self.screen_pressed = False
        self.screen_press_x = 310
        self.screen_press_y = 10
        self.msp = MSP3520()
        self.event_emitter.on('touch', self.touch)
        self.radio_client = RadioClient()

    def render_blank(self):
        if not self.spi_client is None:
            self.spi_client.output_image(self.ui_util.bg["blank"])

    def render(self):
        if self.show_details:
            self.bg_pix = Image.open(self.bg_file)
        else:
            self.bg_pix = Image.open(self.ui_util.bg["no_details"])

        # Buttons
        self.render_buttons()

        if self.which_window == ActiveWindow.CLOCK:
            # Date and Time
            self.render_date_time()
            if self.show_details:
                # Sunrise/set Moonrise/set and progress
                self.render_sun_moon()
                # Min max temps + rain
                self.render_min_max()
            self.bg_pix.paste(self.ui_util.fg_frame, (0, 0), mask=self.ui_util.fg_frame)
        elif self.which_window == ActiveWindow.RADIO:
            if not self.radio_client.play:
                self.bg_pix.paste(self.ui_util.buttons["play"], self.xy_radio_button["play"],
                                  mask=self.ui_util.buttons["play"])
            if self.radio_client.station == 1:
                self.bg_pix.paste(self.ui_util.buttons["station 2"], self.xy_radio_button["station 2"],
                                  mask=self.ui_util.buttons["station 2"])
            else:
                self.bg_pix.paste(self.ui_util.buttons["station 1"], self.xy_radio_button["station 1"],
                                  mask=self.ui_util.buttons["station 1"])

        if not self.spi_client is None:
            self.spi_client.output_image(self.bg_pix)
        else:
            self.bg_pix.save('test1.bmp')
            self.logger.info("spi_client could not init or running in test mode")

    def render_sun_moon(self):
        for sm in ["sun", "moon"]:
            for rs in ["rise", "set"]:
                for x in range(4):
                    self.bg_pix.paste(self.rise_set_pix[sm][rs][x], self.xy_rise_set[sm][rs][x],
                                      mask=self.rise_set_pix[sm][rs][x])

        for x in range(4):  # 4
            self.bg_pix.paste(self.rise_set_pix["colon"][x], self.xy_rise_set["colon"][x],
                              mask=self.rise_set_pix["colon"][x])

        # Sun / Moon Bar
        # Sun
        self.logger.debug(
            "Sun progress:  " + str(self.time_util.weather_client.forecast["today"]["sun"]["rise"]) + " - " + str(
                self.time_util.weather_client.forecast["today"]["sun"]["set"]) + " current: " + str(
                self.time_util.weather_client.progress_bar_sun.get_value()) + " max: " + str(
                self.time_util.weather_client.progress_bar_sun.get_range()))
        self.logger.debug("Sun factor:    " + str(self.time_util.weather_client.progress_bar_sun.get_factor()))
        if self.time_util.weather_client.forecast["today"]["sun"][
            "is_up"] and self.time_util.weather_client.progress_bar_sun.is_valid():
            self.bg_pix.paste(self.sun_bar, self.xy_sun_bar, mask=self.sun_bar)
            width, height = self.sun_bar.size
            img_w, img_h = self.sun.size
            y = (height * (1 - self.time_util.weather_client.progress_bar_sun.get_factor())) - (img_h / 2)
            self.logger.debug("Sun factor 1-: " + str(1 - self.time_util.weather_client.progress_bar_sun.get_factor()))
            self.logger.debug("Sun height:     " + str(height))
            self.logger.debug("Sun y:         " + str(y))
            if int(y) < 0:
                y = 0
            elif int(y + img_h) > height:
                y = height - img_h
            self.xy_sun = (5 + self.x_offset_sun_moon, int(94 + y) + self.y_offset_sun_moon)
            self.bg_pix.paste(self.sun, self.xy_sun, mask=self.sun)
        elif not self.time_util.weather_client.forecast["today"]["sun"]["is_up"]:
            self.bg_pix.paste(self.moon_bar, self.xy_sun_bar, mask=self.moon_bar)

        # Moon
        self.bg_pix.paste(self.moon_bar, self.xy_moon_bar, mask=self.moon_bar)
        if (self.time_util.weather_client.forecast["today"]["moon"]["is_up"] and
                self.time_util.weather_client.progress_bar_moon.is_valid() and
                not self.moon is None):
            width, height = self.moon_bar.size
            img_w, img_h = self.moon.size
            y = (height * (1 - self.time_util.weather_client.progress_bar_moon.get_factor())) - (img_h / 2)
            if int(y) < 0:
                y = 0
            elif int(y + img_h) > height:
                y = height - img_h
            self.xy_moon = (28 + self.x_offset_sun_moon, int(94 + y) + self.y_offset_sun_moon)
            self.bg_pix.paste(self.moon, self.xy_moon, mask=self.moon)

    def render_buttons(self):
        if self.which_window == ActiveWindow.CLOCK:
            s_xy = self.xy_button[self.button_selected]
            self.bg_pix.paste(self.button_selector, (s_xy[0] - 5, s_xy[1] - 5), mask=self.button_selector)
            self.bg_pix.paste(self.button["exit"], self.xy_button["exit"], mask=self.button["exit"])
            self.bg_pix.paste(self.button["radio"], self.xy_button["radio"], mask=self.button["radio"])
            self.bg_pix.paste(self.button["alarm"], self.xy_button["alarm"], mask=self.button["alarm"])
            self.bg_pix.paste(self.button["details"], self.xy_button["details"], mask=self.button["details"])
        else:
            self.bg_pix.paste(self.button["clock"], self.xy_button["clock"], mask=self.button["clock"])

    def render_date_time(self):
        xy = copy.deepcopy(self.xy_time_date)
        xy_colon = copy.deepcopy(self.xy_time_colon)

        if not self.show_details:
            y = 24
            xy_colon = (97, y + (DIGIT_SIZE_X_LARGE[1] * 2) + (DIGIT_SPACE_X_LARGE * 2))

            for i in range(0, 4):
                xy[i] = (97, y)
                if i == 1:
                    y += COLON_SIZE_X_LARGE[1] + DIGIT_SPACE_X_LARGE
                y += DIGIT_SIZE_X_LARGE[1] + DIGIT_SPACE_X_LARGE

        index = 0
        for pix in self.time_date:
            tmp_pix = pix
            if not self.show_details and index < 4:
                tmp_pix = pix.resize(DIGIT_SIZE_X_LARGE)
            self.bg_pix.paste(tmp_pix, xy[index], mask=tmp_pix)
            index += 1

        # Colon
        tmp_pix = self.colon
        if not self.show_details:
            tmp_pix = self.colon.resize(COLON_SIZE_X_LARGE)
        self.bg_pix.paste(tmp_pix, xy_colon, mask=tmp_pix)

        # Day
        index = 0
        for pix in self.day:
            if not pix is None:
                self.bg_pix.paste(pix, self.xy_day[index], mask=pix)
            index += 1

    def render_min_max(self):
        for day in ["today", "tomorrow"]:
            if not self.rain_pix[day][0] is None:
                index = 0
                for pix in self.rain_pix[day]:
                    self.bg_pix.paste(pix, self.xy_rain[day][index], mask=pix)
                    index += 1

            for mm in ["min", "max"]:
                if not self.min_max_pix[day][mm][0] is None:
                    index = 0
                    for pix in self.min_max_pix[day][mm]:
                        self.bg_pix.paste(pix, self.xy_min_max[day][mm][index], mask=pix)
                        index += 1

    def update(self):
        self.read_cpu_temp()
        if self.which_window == ActiveWindow.CLOCK:
            self.update_time_date()
            self.update_astro()
        elif self.which_window == ActiveWindow.RADIO:
            self.bg_file = self.ui_util.bg["radio"]
        self.render()

    def update_time_date(self):
        dt = datetime.datetime.now()
        self.time_date = self.time_util.get_time_parts(dt)

        self.time_date[4] = self.time_date[4].resize(DIGIT_SIZE_MEDIUM)
        self.time_date[5] = self.time_date[5].resize(DIGIT_SIZE_MEDIUM)

        if self.time_util.can_update_daily():
            days = self.time_util.make_dow()
            index = 0
            for d in days:
                self.day[index] = d.resize(DIGIT_SIZE_MEDIUM)
                index += 1

        # if self.time_util.weather_client.forecast["today"]["sun"]["is_up"] and not self.show_details:
        #     self.show_details = True
        #     self.logger.debug("Showing details: " + str(self.show_details))
        #     self.main.config.set("Clock", "show_details", str(self.show_details))
        # elif not self.time_util.weather_client.forecast["today"]["sun"]["is_up"] and self.show_details:
        #     self.show_details = False
        #     self.logger.debug("Showing details: " + str(self.show_details))
        #     self.main.config.set("Clock", "show_details", str(self.show_details))

    def update_astro(self):
        if self.time_util.can_update_astro():
            self.time_util.weather_client.fetch_weather()
            self.bg_file = self.weather_code.decode_weather_for_tod(self.time_util.weather_client.current_cond,
                                                                    self.time_util.weather_client.tod)
            # Get moon phase
            self.moon = Image.open(self.time_util.ui_util.moon_phases[self.time_util.weather_client.current_moon])
            digit_list = {
                "sr": self.time_util.update_sunrise(),
                "ss": self.time_util.update_sunset(),
                "mr": self.time_util.update_moonrise(),
                "ms": self.time_util.update_moonset()
            }
            for x in range(4):
                pix = {
                    "sr": digit_list["sr"][x],
                    "ss": digit_list["ss"][x],
                    "mr": digit_list["mr"][x],
                    "ms": digit_list["ms"][x]
                }

                if not pix["sr"] is None:
                    self.rise_set_pix["sun"]["rise"][x] = pix["sr"].resize(DIGIT_SIZE_SMALL)
                if not pix["ss"] is None:
                    self.rise_set_pix["sun"]["set"][x] = pix["ss"].resize(DIGIT_SIZE_SMALL)
                if not pix["mr"] is None:
                    self.rise_set_pix["moon"]["rise"][x] = pix["mr"].resize(DIGIT_SIZE_SMALL)
                if not pix["ms"] is None:
                    self.rise_set_pix["moon"]["set"][x] = pix["ms"].resize(DIGIT_SIZE_SMALL)

            d_w_mm = {
                "today": {
                    "min": self.time_util.weather_client.current_temp_min,
                    "max": self.time_util.weather_client.current_temp_max
                },
                "tomorrow": {
                    "min": self.time_util.weather_client.tomorrow_temp_min,
                    "max": self.time_util.weather_client.tomorrow_temp_max
                }
            }
            d_w_r = {
                "today": self.time_util.weather_client.current_rain,
                "tomorrow": self.time_util.weather_client.tomorrow_rain
            }

            for day in ["today", "tomorrow"]:
                if not d_w_r[day] is None:
                    self.process_rain(d_w_r[day], self.rain_pix[day])

                for mm in ["min", "max"]:
                    if not d_w_mm[day][mm] is None:
                        self.process_min_max(d_w_mm[day][mm], self.min_max_pix[day][mm])

    def process_min_max(self, temp, pix_a):
        str_min = f"{temp:.1f}"
        is_neg = False
        if temp < 0.0:
            # negative, remove the -
            str_min = str_min[1:]
            is_neg = True

        if len(str_min) == 3:  # E.g. 1.0
            # add 0 in front
            str_min = "0" + str_min

        if is_neg:
            pix_a[0] = self.ui_util.pix_dash.resize(DIGIT_SIZE_SMALL)
        else:
            pix_a[0] = self.ui_util.pix_blank.resize(DIGIT_SIZE_SMALL)

        pix_a[1] = self.ui_util.pix_nums[int(str_min[0])].resize(DIGIT_SIZE_SMALL)
        pix_a[2] = self.ui_util.pix_nums[int(str_min[1])].resize(DIGIT_SIZE_SMALL)
        pix_a[4] = self.ui_util.pix_nums[int(str_min[3])].resize(DIGIT_SIZE_X_SMALL)

    def process_rain(self, rain: int, pix_a):
        str_min = str(rain)

        if len(str_min) == 0:  # E.g. => 00
            # Set to 00
            str_min = "00"
        elif len(str_min) == 1:  # E.g. 1 => 01
            # add 0 in front
            str_min = "0" + str_min
        elif len(str_min) >= 3:  # E.g. 100 => 99
            # Set to 99
            str_min = "99"

        pix_a[0] = self.ui_util.pix_nums[int(str_min[0])].resize(DIGIT_SIZE_SMALL)
        pix_a[1] = self.ui_util.pix_nums[int(str_min[1])].resize(DIGIT_SIZE_SMALL)
        pix_a[2] = self.ui_util.pix_percentage.resize(DIGIT_SIZE_SMALL)

    def touch(self):
        with press_lock:
            tt = time.time()  # seconds
            if self.last_press_time is None or self.last_press_time + 1 <= tt:  # + 1s
                self.logger.info("Touch: Last press is None or ready")
                self.last_press_time = tt + 1
            else:
                self.logger.info("Touch: Busy")
                return

        if self.which_window == ActiveWindow.CLOCK:
            self.show_details = not self.show_details
            self.logger.debug("Showing details: " + str(self.show_details))
            self.main.config.set("Clock", "show_details", str(self.show_details))
        elif self.which_window == ActiveWindow.RADIO:
            # toggle play on and off
            self.radio_client.play = self.main.toggle_play()
            self.logger.debug("Is radio playing: " + str(self.radio_client.play))
        self.render()

    def read_cpu_temp(self):
        tempo = int(self.main.config.get("General", "interval_temp_read"))
        tt = time.time()  # seconds
        if self.last_temp_log is None or self.last_temp_log + tempo <= tt:  # + 10s
            self.last_temp_log = tt + tempo
            temp_file = Path("/sys/class/thermal/thermal_zone0/temp")
            if not temp_file.exists():
                self.logger.error("Could not find temp file: " + temp_file.name)
                return
            with temp_file.open() as f:
                temp = f.read()

            self.logger.debug("Reading temp: " + temp)
            f_temp = float(temp) / 1000.0

            if f_temp > 80.0:
                self.logger.error(f"CPU Temperatures: {f_temp:.1f}°C")
            else:
                self.logger.info(f"CPU Temperatures: {f_temp:.1f}°C")