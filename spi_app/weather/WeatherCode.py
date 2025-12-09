from enum import Enum
import random

from spi_app.ui.UIUtil import UIUtil


class TimeOfDay(Enum):
    SUNRISE = 1
    DAY = 2
    SUNSET = 3
    NIGHT = 4


MAX_DAY_CLEAR = 4
MAX_DAY_CLOUDY = 1
MAX_DAY_LRAIN = 4
MAX_DAY_RAIN = 4
MAX_DAY_THUNDER = 1
MAX_NIGHT_CLEAR = 5
MAX_NIGHT_CLOUDY = 1
MAX_NIGHT_PCLOUDY = 5
MAX_NIGHT_RAIN = 4
MAX_NIGHT_THUNDER = 2
MAX_SUNRISE = 4
MAX_SUNSET = 4


def get_random(max_num: int) -> int:
    if max_num == 1:
        return 1
    else:
        return random.randint(1, max_num)


def get_by_time_of_day(prefix_sunrise, prefix_day, prefix_sunset, prefix_night, max_sunrise: int, max_day: int,
                       max_sunset: int, max_night: int, tod: TimeOfDay):
    match tod:
        case TimeOfDay.SUNRISE:
            return prefix_sunrise + str(get_random(max_sunrise)) + ".png"
        case TimeOfDay.DAY:
            return prefix_day + str(get_random(max_day)) + ".png"
        case TimeOfDay.SUNSET:
            return prefix_sunset + str(get_random(max_sunset)) + ".png"
        case TimeOfDay.NIGHT:
            return prefix_night + str(get_random(max_night)) + ".png"

class WeatherCode:
    def __init__(self, home_dir):
        super().__init__()
        self.ui_util = UIUtil(home_dir)

    def get_by_time_of_day(self, sunrise, day, sunset, night, tod: TimeOfDay):
            match tod:
                case TimeOfDay.SUNRISE:
                    return self.ui_util.get_bg_path(sunrise)
                case TimeOfDay.DAY:
                    return self.ui_util.get_bg_path(day)
                case TimeOfDay.SUNSET:
                    return self.ui_util.get_bg_path(sunset)
                case TimeOfDay.NIGHT:
                    return self.ui_util.get_bg_path(night)

    def decode_weather_for_tod(self, code: int, tod: TimeOfDay):
        match code:
            case 1000:
                # "day" : "Sunny",
                # "night" : "Clear",
                return self.get_by_time_of_day("sunrise", "day_clear", "sunset", "night_clear", tod)
            case 1003:
                # "day" : "Partly cloudy",
                # "night" : "Partly cloudy",
                return self.get_by_time_of_day("sunrise", "day_cloudy", "sunset", "night_pcloudy", tod)

            case 1006 | 1009 | 1030 | 1063 | 1066 | 1069 | 1072 | 1135 | 1147 | 1150 | 1153 | 1168 | 1171 | 1180 | 1198 | 1204 | 1183 | 1213 | 1210 | 1240:
                # Overcast, Mist, Cloudy, Patchy rain possible
                return self.get_by_time_of_day("day_lrain", "day_lrain", "night_cloudy", "night_cloudy", tod)

            case 1087 | 1273 | 1276 | 1279 | 1282 | 1117:
                # Thunder
                return self.get_by_time_of_day("day_thunder", "day_thunder", "night_thunder", "night_thunder", tod)

            case 1186 | 1189 | 1192 | 1195 | 1201 | 1207 | 1216 | 1243 | 1246:
                # Rain
                return self.get_by_time_of_day("day_rain", "day_rain", "night_rain", "night_rain", tod)

            case _:
                return self.get_by_time_of_day("sunrise", "day_clear", "sunset", "night_clear", tod)

# https://www.weatherapi.com/docs/weather_conditions.json
def decode_weather_for_tod(code: int, tod: TimeOfDay):
    match code:
        case 1000:
            # "day" : "Sunny",
            # "night" : "Clear",
            return get_by_time_of_day("bg_sunrise", "bg_day_clear", "bg_sunset", "bg_night_clear", MAX_SUNRISE,
                                      MAX_DAY_CLEAR, MAX_SUNSET, MAX_NIGHT_CLEAR, tod)
        case 1003:
            # "day" : "Partly cloudy",
            # "night" : "Partly cloudy",
            return get_by_time_of_day("bg_sunrise", "bg_day_cloudy", "bg_sunset", "bg_night_pcloudy", MAX_SUNRISE,
                              MAX_DAY_CLOUDY, MAX_SUNSET, MAX_NIGHT_PCLOUDY, tod)
        case 1006 | 1009 | 1030 | 1063 | 1066 | 1069 | 1072 | 1135 | 1147 | 1150 | 1153 | 1168 | 1171 | 1180 | 1198 | 1204 | 1183 | 1213 | 1210 | 1240:
            # Overcast, Mist, Cloudy, Patchy rain possible
            return get_by_time_of_day("bg_day_lrain", "bg_day_lrain", "bg_night_cloudy", "bg_night_cloudy", MAX_DAY_LRAIN,
                              MAX_DAY_LRAIN, MAX_NIGHT_CLOUDY, MAX_NIGHT_CLOUDY, tod)
        case 1087 | 1273 | 1276 | 1279 | 1282 | 1117:
            # Thunder
            return get_by_time_of_day("bg_day_thunder", "bg_day_thunder", "bg_night_thunder", "bg_night_thunder", MAX_DAY_THUNDER,
                              MAX_DAY_THUNDER, MAX_NIGHT_THUNDER, MAX_NIGHT_THUNDER, tod)
        case 1186 | 1189 | 1192 | 1195 | 1201 | 1207 | 1216 | 1243 | 1246:
            # Rain
            return get_by_time_of_day("bg_day_rain", "bg_day_rain", "bg_night_rain", "bg_night_rain", MAX_DAY_RAIN,
                              MAX_DAY_RAIN, MAX_NIGHT_RAIN, MAX_NIGHT_RAIN, tod)
        case _:
            return get_by_time_of_day("bg_sunrise", "bg_day_clear", "bg_sunset", "bg_night_clear", MAX_SUNRISE,
                              MAX_DAY_CLEAR, MAX_SUNSET, MAX_NIGHT_CLEAR, tod)
"""            

	{
		"code" : 1114,
		"day" : "Blowing snow",
		"night" : "Blowing snow",
		"icon" : 227
	},
	{
		"code" : 1219,
		"day" : "Moderate snow",
		"night" : "Moderate snow",
		"icon" : 332
	},
	{
		"code" : 1222,
		"day" : "Patchy heavy snow",
		"night" : "Patchy heavy snow",
		"icon" : 335
	},
	{
		"code" : 1225,
		"day" : "Heavy snow",
		"night" : "Heavy snow",
		"icon" : 338
	},
	{
		"code" : 1237,
		"day" : "Ice pellets",
		"night" : "Ice pellets",
		"icon" : 350
	},
	{
		"code" : ,
		"day" : "Moderate or heavy rain shower",
		"night" : "Moderate or heavy rain shower",
		"icon" : 356
	},
	{
		"code" : ,
		"day" : "Torrential rain shower",
		"night" : "Torrential rain shower",
		"icon" : 359
	},
	{
		"code" : 1249,
		"day" : "Light sleet showers",
		"night" : "Light sleet showers",
		"icon" : 362
	},
	{
		"code" : 1252,
		"day" : "Moderate or heavy sleet showers",
		"night" : "Moderate or heavy sleet showers",
		"icon" : 365
	},
	{
		"code" : 1255,
		"day" : "Light snow showers",
		"night" : "Light snow showers",
		"icon" : 368
	},
	{
		"code" : 1258,
		"day" : "Moderate or heavy snow showers",
		"night" : "Moderate or heavy snow showers",
		"icon" : 371
	},
	{
		"code" : 1261,
		"day" : "Light showers of ice pellets",
		"night" : "Light showers of ice pellets",
		"icon" : 374
	},
	{
		"code" : 1264,
		"day" : "Moderate or heavy showers of ice pellets",
		"night" : "Moderate or heavy showers of ice pellets",
		"icon" : 377
	},
]
"""
