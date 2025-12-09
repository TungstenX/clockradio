import datetime
import requests
from dateutil import parser
from spi_app.ui.UIUtil import ProgressBarDataCR
from spi_app.weather.WeatherCode import TimeOfDay


class WeatherClientCR:
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.config = main.config

        self.progress_bar_sun = ProgressBarDataCR()
        self.progress_bar_moon = ProgressBarDataCR()

        self.old_is_moon_up = None
        self.old_is_sun_up = None
        self.moon_minutes = None
        self.moon_minutes_total = None
        self.night_minutes = None
        self.night_minutes_total = None
        self.sun_minutes = None
        self.daylight_minutes_total = None
        self.current_moon = None
        self.tod = None
        self.current_cond = None

        self.last_update_astro = None
        self.last_update_day = None
        today_element = {
            "sun": {
                "rise": None,
                "set": None,
                "is_up": False
            },
            "moon": {
                "rise": None,
                "set": None,
                "is_up": False
            },
            "temp": {
                "min": None,
                "max": None
            },
            "rain": None
        }
        tomorrow_element = today_element.copy()
        self.forecast = {
            "today": today_element,
            "tomorrow": tomorrow_element
        }

        self.current_temp_max = None
        self.current_temp_min = None
        self.tomorrow_temp_min = None
        self.tomorrow_temp_max = None
        self.current_rain = None
        self.tomorrow_rain = None

    def fetch_weather(self):
        dt_now = datetime.datetime.now()
        # print("Checking weather")
        print('.', sep='', end='', flush=True)
        complete_url = "https://api.weatherapi.com/v1/forecast.json?key=" + self.config.get("Weather", "api_key") + "&q=-26.063018646041453,27.961667533360554&aqi=no&days=3"

        response = requests.get(complete_url)
        data = response.json()
        if response.status_code == 200:
            #print(data)
            # Set min and max temps
            self.current_temp_max = data["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
            self.current_temp_min = data["forecast"]["forecastday"][0]["day"]["mintemp_c"]
            self.tomorrow_temp_max = data["forecast"]["forecastday"][1]["day"]["maxtemp_c"]
            self.tomorrow_temp_min = data["forecast"]["forecastday"][1]["day"]["mintemp_c"]

            current_wind = data["current"]["wind_kph"]
            current_gust = data["current"]["gust_kph"]

            self.current_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]
            self.tomorrow_rain = data["forecast"]["forecastday"][1]["day"]["daily_chance_of_rain"]

            # Sun and moon rise and set
            self.forecast["today"]["sun"]["rise"] = parser.parse(data["forecast"]["forecastday"][0]["astro"]["sunrise"])
            self.forecast["today"]["sun"]["set"] = parser.parse(data["forecast"]["forecastday"][0]["astro"]["sunset"])
            moonrise = data["forecast"]["forecastday"][0]["astro"]["moonrise"]
            if moonrise != "No moonrise":
                self.forecast["today"]["moon"]["rise"] = parser.parse(moonrise)
            else:
                moonrise = data["forecast"]["forecastday"][1]["astro"]["moonrise"]
                if moonrise != "No moonrise":
                    self.forecast["today"]["moon"]["rise"] = parser.parse(moonrise) + datetime.timedelta(days=1)


            moonset = data["forecast"]["forecastday"][0]["astro"]["moonset"]
            if moonset != "No moonset":
                self.forecast["today"]["moon"]["set"] = parser.parse(moonset)
            else:
                moonset = data["forecast"]["forecastday"][1]["astro"]["moonset"]
                if moonset != "No moonset":
                    self.forecast["today"]["moon"]["set"] = parser.parse(moonset) + datetime.timedelta(days=1)

            # print("Sun rise date : " + self.forecast["today"]["sun"]["rise"].strftime('%Y-%m-%d, %H:%M'))
            # print("Sun set date  : " + self.forecast["today"]["sun"]["set"].strftime('%Y-%m-%d, %H:%M'))
            # print("Moon rise date: " + self.forecast["today"]["moon"]["rise"].strftime('%Y-%m-%d, %H:%M'))
            # print("Moon set date : " + self.forecast["today"]["moon"]["set"].strftime('%Y-%m-%d, %H:%M'))
            if self.forecast["today"]["moon"]["rise"] > self.forecast["today"]["moon"]["set"]:
                 self.forecast["today"]["moon"]["set"] += datetime.timedelta(days=1)

            # print("Moon rise date: " + self.forecast["today"]["moon"]["rise"].strftime('%Y-%m-%d, %H:%M'))
            # print("Moon set date : " + self.forecast["today"]["moon"]["set"].strftime('%Y-%m-%d, %H:%M'))
            self.old_is_sun_up = self.forecast["today"]["sun"]["is_up"]
            self.old_is_moon_up = self.forecast["today"]["moon"]["is_up"]

            # data["forecast"]["forecastday"][0]["astro"]["is_sun_up"] == 1
            self.forecast["today"]["sun"]["is_up"] = self.forecast["today"]["sun"]["rise"] <= dt_now <= self.forecast["today"]["sun"]["set"]
            self.forecast["today"]["moon"]["is_up"] = self.forecast["today"]["moon"]["rise"] <= dt_now <= self.forecast["today"]["moon"]["set"]

            if self.forecast["today"]["sun"]["is_up"]:
                self.daylight_minutes_total = (self.forecast["today"]["sun"]["set"] - self.forecast["today"]["sun"]["rise"]).seconds / 60
                self.sun_minutes = (self.forecast["today"]["sun"]["set"] - dt_now).seconds / 60
                self.night_minutes_total = 0
                self.night_minutes = 0
            elif not self.forecast["today"]["sun"]["is_up"]:
                self.daylight_minutes_total = 0
                self.sun_minutes = 0
                if dt_now < self.forecast["today"]["sun"]["rise"]:
                    self.night_minutes = (self.forecast["today"]["sun"]["rise"] - dt_now).seconds / 60
                    # Not yet today
                elif dt_now > self.forecast["today"]["sun"]["set"]:
                    # load tomorrows sun data
                    self.forecast["today"]["sun"]["rise"] = parser.parse(
                        data["forecast"]["forecastday"][1]["astro"]["sunrise"]) + datetime.timedelta(days=1)
                    self.night_minutes_total = (self.forecast["today"]["sun"]["rise"] - self.forecast["today"]["sun"]["set"]).seconds / 60
                    self.forecast["today"]["sun"]["set"] = parser.parse(
                        data["forecast"]["forecastday"][1]["astro"]["sunset"]) + datetime.timedelta(days=1)
                    self.night_minutes = (self.forecast["today"]["sun"]["rise"] - dt_now).seconds / 60

            if self.forecast["today"]["moon"]["is_up"]:
                self.moon_minutes_total = (self.forecast["today"]["moon"]["set"] - self.forecast["today"]["moon"]["rise"]).seconds / 60
                self.moon_minutes = (self.forecast["today"]["moon"]["set"] - dt_now).seconds / 60
                self.progress_bar_moon.set_range(int(self.moon_minutes_total))
            elif not self.forecast["today"]["moon"]["is_up"]:
                self.moon_minutes_total = 1
                self.moon_minutes = 0
                self.progress_bar_moon.set_range(int(self.moon_minutes_total))

            # print("Is sun up: " + str(self.forecast["today"]["sun"]["is_up"]))
            # print("Is moon up: " + str(self.forecast["today"]["moon"]["is_up"]))
            if self.forecast["today"]["sun"]["is_up"]:
                if self.old_is_sun_up != self.forecast["today"]["sun"]["is_up"]:
                    self.old_is_sun_up = self.forecast["today"]["sun"]["is_up"]
                    # make yellow/orange
                    self.progress_bar_sun.set_range(int(self.daylight_minutes_total))
                #     self.progress_bar_sun.setStyleSheet("""
                #     QProgressBar {
                #         background-color: rgba(237, 162, 7, 128);
                #     }
                #     QProgressBar::chunk {
                #         background-color: rgba(237, 162, 7, 255);
                #     }
                #     """)
                #
                self.progress_bar_sun.set_value(int(self.sun_minutes))
                # self.progress_bar_sun.repaint()
            else:  # night
                if self.old_is_sun_up != self.forecast["today"]["sun"]["is_up"]:
                    self.old_is_sun_up = self.forecast["today"]["sun"]["is_up"]
                    # make yellow/orange
                    if not self.night_minutes_total is None:
                        self.progress_bar_sun.set_range(int(self.night_minutes_total))
                #     self.progress_bar_sun.setStyleSheet("""
                #                         QProgressBar {
                #                             background-color: rgba(2, 18, 178, 128);
                #                         }
                #                         QProgressBar::chunk {
                #                             background-color: rgba(2, 18, 178, 255);
                #                         }
                #                         """)
                #
                if not self.night_minutes is None:
                    self.progress_bar_sun.set_value(int(self.night_minutes))
                # self.progress_bar_sun.repaint()

            if self.old_is_moon_up != self.forecast["today"]["moon"]["is_up"]:
                self.old_is_moon_up = self.forecast["today"]["moon"]["is_up"]
                self.progress_bar_moon.set_range(int(self.moon_minutes_total))
                # self.progress_bar_moon.setStyleSheet("""
                #                                         QProgressBar {
                #                                             background-color: rgba(0, 0, 0, 128);
                #                                         }
                #                                         QProgressBar::chunk {
                #                                             background-color: rgba(255, 255, 255, 255);
                #                                         }
                #                                         """)

            if self.forecast["today"]["moon"]["is_up"]:
                self.progress_bar_moon.set_value(int(self.moon_minutes))
            #     self.progress_bar_moon.repaint()

            # Current conditions
            self.current_cond = data["current"]["condition"]["code"]
            if (self.forecast["today"]["sun"]["rise"] + datetime.timedelta(hours=1)).time() >= dt_now.time() >= (
                    self.forecast["today"]["sun"]["rise"] - datetime.timedelta(
                hours=1)).time():  # sunrise is from an hour before and after sunrise
                self.tod = TimeOfDay.SUNRISE
            elif (self.forecast["today"]["sun"]["rise"] + datetime.timedelta(hours=1)).time() < dt_now.time() < (
                    self.forecast["today"]["sun"]["set"] - datetime.timedelta(hours=1)).time():
                self.tod = TimeOfDay.DAY
            elif (self.forecast["today"]["sun"]["rise"] + datetime.timedelta(hours=1)).time() >= dt_now.time() >= (
                    self.forecast["today"]["sun"]["rise"] - datetime.timedelta(hours=1)).time():
                self.tod = TimeOfDay.SUNSET
            else:
                self.tod = TimeOfDay.NIGHT
            #
            # bg_image_file_name = decode_weather_for_tod(current_cond, tod)
            # self.setStyleSheet("TimeWindow { background-image: url(\"res/" + bg_image_file_name + "\") }")

            self.current_moon = data["forecast"]["forecastday"][0]["astro"]["moon_phase"]
        else:
            print(" City Not Found ")