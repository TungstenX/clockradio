import spidev
from PIL import Image

from spi_app.SPIClient import SPIClient
from spi_app.time_util.TimeUtilsCR import TimeUtilsCR
from spi_app.ui.UIUtil import UIUtil
from spi_app.weather.WeatherCode import WeatherCode, TimeOfDay

DIGIT_SIZE_MEDIUM = (40, 30)
DIGIT_SIZE_SMALL = (20, 15)
DIGIT_SIZE_X_SMALL = (10, 7)
COLON_SIZE_MEDIUM = (20, 6)
BUTTON_SIZE = (30, 30)


class SPIWindow:
    def __init__(self, main, home_dir, start_test_mode):
        super().__init__()

        self.main = main
        self.home_dir = home_dir
        self.which_window = 0  # 0 Clock, 1 = Alarm, 2 = Radio

        self.time_util = TimeUtilsCR(self.main, home_dir)
        self.ui_util = UIUtil(self.home_dir)
        self.spi_client = None
        if not start_test_mode:
            self.spi_client = SPIClient()

        self.xy_moon = None
        self.xy_sun = None
        self.ms_minute1 = None
        self.ms_minute0 = None
        self.ms_hour1 = None
        self.ms_hour0 = None
        self.mr_minute1 = None
        self.mr_minute0 = None
        self.mr_hour1 = None
        self.mr_hour0 = None
        self.ss_minute1 = None
        self.ss_minute0 = None
        self.ss_hour1 = None
        self.ss_hour0 = None
        self.sr_minute1 = None
        self.sr_minute0 = None
        self.sr_hour1 = None
        self.sr_hour0 = None
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
            "today": [None, None],
            "tomorrow": [None, None]
        }

        # Opening the primary image (used in background)
        self.weather_code = WeatherCode(home_dir)
        self.bg_file = self.weather_code.decode_weather_for_tod(0, TimeOfDay.DAY)  #
        self.bg_pix = Image.open(self.bg_file)
        self.last_update_astro = None
        self.last_update_day = None

        # Time:
        # [(102, 120), (168, 120), (252, 120), (318, 120), (295, 275), (330, 275)]
        self.xy_time_date = [(120, 102), (120, 168), (120, 252), (120, 318), (275, 295), (275, 330)]
        self.xy_time_colon = (120, 234)

        self.xy_rise_set = {
            "sun": {
                "rise": [(5, 10), (5, 28), (5, 55), (5, 73)],
                "set": [(5, 397), (5, 415), (5, 442), (5, 460)]
            },
            "moon": {
                "rise": [(28, 10), (28, 28), (28, 55), (28, 73)],
                "set": [(28, 397), (28, 415), (28, 442), (28, 460)]
            },
            "colon": [(5, 46), (5, 433), (28, 46), (28, 433)]
        }

        # Sun / Moon bar:
        self.xy_sun_bar = (5, 94)
        self.xy_moon_bar = (28, 94)

        # Date:
        self.xy_day = [(275, 370), (275, 405), (275, 440)]

        # Button:
        self.xy_button1 = (285, 10)
        self.xy_button2 = (285, 45)
        self.xy_button3 = (285, 80)
        self.xy_button4 = (285, 115)

        # Min max
        self.xy_min_max = {
            "today": {
                "min": [(166, 10), (166, 28), (166, 46), (166, 64), (166, 73)],
                "max": [(143, 10), (143, 28), (143, 46), (143, 64), (143, 73)]
            },
            "tomorrow": {
                "min": [(166, 397), (166, 415), (166, 433), (166, 451), (166, 460)],
                "max": [(143, 397), (143, 415), (143, 433), (143, 451), (143, 460)]
            }
        }
        # Rain
        self.xy_rain = {
            "today": [(120, 10), (120, 28)],
            "tomorrow": [(120, 442), (120, 460)]
        }

        self.button_alarm = self.ui_util.buttons["alarm"].resize(BUTTON_SIZE)
        self.button_clock = self.ui_util.buttons["clock"].resize(BUTTON_SIZE)
        self.button_details = self.ui_util.buttons["details"].resize(BUTTON_SIZE)
        self.button_exit = self.ui_util.buttons["exit"].resize(BUTTON_SIZE)
        self.button_radio = self.ui_util.buttons["radio"].resize(BUTTON_SIZE)

        self.sun_bar = self.ui_util.bar["sun_bar"]
        self.moon_bar = self.ui_util.bar["moon_bar"]

        self.sun = self.ui_util.sun

        self.moon = None

        self.update()
        self.render()
        self.bg_pix.save('test1.bmp')

    def close(self):
        if not self.spi_client is None:
            self.spi_client.close()

    def render(self):
        if self.which_window == 0:
            self.bg_pix = Image.open(self.bg_file)

        if self.which_window == 0:
            # Date and Time
            self.render_date_time()
            # Buttons
            self.render_buttons()
            if self.main.config.get('Clock', 'show_details'):
                # Sunrise/set Moonrise/set and progress
                self.render_sun_moon()
                # Min max temps + rain
                self.render_min_max()

        if not self.spi_client is None:
            self.spi_client.output_image(self.bg_pix)
        else:
            print("spi_client could not init or running in test mode")

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
        # print("Sun progress:  " + str(self.time_util.weather_client.forecast["today"]["sun"]["rise"]) + " - " + str(self.time_util.weather_client.forecast["today"]["sun"]["set"]) + " current: " + str(self.time_util.weather_client.progress_bar_sun.get_value()) + " max: " + str(self.time_util.weather_client.progress_bar_sun.get_range()))
        # print("Sun factor:    " + str(self.time_util.weather_client.progress_bar_sun.get_factor()))
        if self.time_util.weather_client.forecast["today"]["sun"][
            "is_up"] and self.time_util.weather_client.progress_bar_sun.is_valid():
            self.bg_pix.paste(self.sun_bar, self.xy_sun_bar, mask=self.sun_bar)
            width, height = self.sun_bar.size
            img_w, img_h = self.sun.size
            y = (height * (1 - self.time_util.weather_client.progress_bar_sun.get_factor())) - (img_h / 2)
            # print("Sun factor 1-: " + str(1 - self.time_util.weather_client.progress_bar_sun.get_factor()))
            # print("Sun height:     " + str(height))
            # print("Sun y:         " + str(y))
            if int(y) < 0:
                y = 0
            elif int(y + img_h) > height:
                y = height - img_h
            self.xy_sun = (5, int(94 + y))
            self.bg_pix.paste(self.sun, self.xy_sun, mask=self.sun)
        elif not self.time_util.weather_client.forecast["today"]["sun"]["is_up"]:
            self.bg_pix.paste(self.moon_bar, self.xy_sun_bar, mask=self.moon_bar)

        # Moon
        self.bg_pix.paste(self.moon_bar, self.xy_moon_bar, mask=self.moon_bar)
        if self.time_util.weather_client.forecast["today"]["moon"][
            "is_up"] and self.time_util.weather_client.progress_bar_moon.is_valid() and not self.moon is None:
            width, height = self.moon_bar.size
            img_w, img_h = self.moon.size
            y = (height * (1 - self.time_util.weather_client.progress_bar_moon.get_factor())) - (img_h / 2)
            if int(y) < 0:
                y = 0
            elif int(y + img_h) > height:
                y = height - img_h
            self.xy_moon = (5, int(94 + y))
            self.bg_pix.paste(self.moon, self.xy_moon, mask=self.moon)

    def render_buttons(self):
        self.bg_pix.paste(self.button_exit, self.xy_button1, mask=self.button_exit)
        self.bg_pix.paste(self.button_radio, self.xy_button2, mask=self.button_radio)
        self.bg_pix.paste(self.button_alarm, self.xy_button3, mask=self.button_alarm)
        self.bg_pix.paste(self.button_details, self.xy_button4, mask=self.button_details)

    def render_date_time(self):
        index = 0
        for pix in self.time_date:
            self.bg_pix.paste(pix, self.xy_time_date[index], mask=pix)
            index += 1

        self.bg_pix.paste(self.colon, self.xy_time_colon, mask=self.colon)
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
        self.update_time_date()
        self.update_astro()
        self.render()

    def update_time_date(self):
        self.time_date = self.time_util.get_time_parts()

        self.time_date[4] = self.time_date[4].resize(DIGIT_SIZE_MEDIUM)
        self.time_date[5] = self.time_date[5].resize(DIGIT_SIZE_MEDIUM)

        if self.time_util.can_update_daily():
            days = self.time_util.make_dow()
            index = 0
            for d in days:
                self.day[index] = d.resize(DIGIT_SIZE_MEDIUM)
                index += 1

    def update_astro(self):
        if self.time_util.can_update_astro():
            self.time_util.weather_client.fetch_weather()  # TDOD Move to time_util
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
