import datetime
import logging
from typing import Any
from spi_app.ui.UIUtil import UIUtil
from spi_app.weather.WeatherClient import WeatherClientCR

class TimeUtilsCR:
    def __init__(self, main, home_dir):
        super().__init__()
        self.main = main
        self.config = main.config
        self.ui_util = UIUtil(home_dir)
        self.weather_client = WeatherClientCR(main)
        self.logger = logging.getLogger()

    def get_time_parts(self, dt) -> list[Any]:
        hour = dt.hour
        minute = dt.minute
        self.logger.debug("Hour's minute:" + str(minute))
        hour_ones = hour % 10
        hour_tens = (hour % 100) // 10
        minute_ones = minute % 10
        minute_tens = (minute % 100) // 10

        day = dt.day
        day_ones = day % 10
        day_tens = (day % 100) // 10
        return [self.ui_util.pix_nums[int(hour_tens)], self.ui_util.pix_nums[int(hour_ones)], self.ui_util.pix_nums[int(minute_tens)],
                self.ui_util.pix_nums[int(minute_ones)], self.ui_util.pix_nums[int(day_tens)], self.ui_util.pix_nums[int(day_ones)]]

    def can_update_astro(self):
        dt_now = datetime.datetime.now()
        if self.weather_client.last_update_astro is None or (dt_now - self.weather_client.last_update_astro).total_seconds() > 3600:  # check every hour
            self.weather_client.last_update_astro = dt_now
            return True
        return False

    def can_update_daily(self):
        if self.weather_client.last_update_day is None or self.weather_client.last_update_day != datetime.date.today():
            self.weather_client.last_update_day = datetime.date.today()
            return True
        return False

    def update_sunrise(self)-> list[Any] | None:
        if not self.weather_client.forecast["today"]["sun"]["rise"] is None:
            return self.get_time_parts(self.weather_client.forecast["today"]["sun"]["rise"])
        return None

    def update_sunset(self)-> list[Any] | None:
        if not self.weather_client.forecast["today"]["sun"]["set"] is None:
            return self.get_time_parts(self.weather_client.forecast["today"]["sun"]["set"])
        return None

    def update_moonrise(self)-> list[Any] | None:
        if not self.weather_client.forecast["today"]["moon"]["rise"] is None:
            return self.get_time_parts(self.weather_client.forecast["today"]["moon"]["rise"])
        return None

    def update_moonset(self)-> list[Any] | None:
        if not self.weather_client.forecast["today"]["moon"]["set"] is None:
            return self.get_time_parts(self.weather_client.forecast["today"]["moon"]["set"])
        return None

    def make_dow(self) -> list[Any]:
        dt_now = datetime.datetime.now()
        week_day = dt_now.isoweekday()
        match week_day:
            case 1:
                # Monday
                return [self.ui_util.pix_letter["M"], self.ui_util.pix_letter["O"],self.ui_util.pix_letter["N"]]
            case 2:
                # Tuesday
                return [self.ui_util.pix_letter["T"], self.ui_util.pix_letter["U"], self.ui_util.pix_letter["E"]]

            case 3:
                # Wednesday
                return [self.ui_util.pix_letter["W"],self.ui_util.pix_letter["E"],self.ui_util.pix_letter["D"]]

            case 4:
                # Thursday
                return [self.ui_util.pix_letter["T"],self.ui_util.pix_letter["H"],self.ui_util.pix_letter["U"]]

            case 5:
                # Friday
                return [self.ui_util.pix_letter["F"],self.ui_util.pix_letter["R"],self.ui_util.pix_letter["I"]]

            case 6:
                # Saturday
                return [self.ui_util.pix_letter["S"],self.ui_util.pix_letter["A"],self.ui_util.pix_letter["T"]]

            case 7:
                # Sunday
                return [self.ui_util.pix_letter["S"],self.ui_util.pix_letter["U"],self.ui_util.pix_letter["N"]]
            case _:
                # Default
                print("make_dow default")
                return [self.ui_util.pix_letter["S"],self.ui_util.pix_letter["U"],self.ui_util.pix_letter["N"]]

