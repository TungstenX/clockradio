import os
import random
from PIL import Image
from playsound import playsound

class ProgressBarDataCR:
    def __init__(self):
        super().__init__()
        self.current = None
        self.max = None
        self.valid = False

    def set_range(self, new_max: int):
        self.max = new_max
        self.valid = new_max > 0

    def set_value(self, value: int):
        self.current = value
        self.valid = value > 0

    def get_range(self):
        return self.max

    def get_value(self):
        return self.current

    def get_factor(self):
        if self.max is None or self.max == 0:
            return None
        return self.current / self.max

    def is_valid(self):
        return self.valid


def get_random(max_num: int) -> int:
    if max_num == 1:
        return 0
    else:
        return random.randint(0, max_num - 1)


class UIUtil:
    def __init__(self, home_dir):
        super().__init__()

        self.home_dir = home_dir

        self.pix_num_0 = Image.open(os.path.join(home_dir, "res/0.png"))
        self.pix_num_1 = Image.open(os.path.join(home_dir, "res/1.png"))
        self.pix_num_2 = Image.open(os.path.join(home_dir, "res/2.png"))
        self.pix_num_3 = Image.open(os.path.join(home_dir, "res/3.png"))
        self.pix_num_4 = Image.open(os.path.join(home_dir, "res/4.png"))
        self.pix_num_5 = Image.open(os.path.join(home_dir, "res/5.png"))
        self.pix_num_6 = Image.open(os.path.join(home_dir, "res/6.png"))
        self.pix_num_7 = Image.open(os.path.join(home_dir, "res/7.png"))
        self.pix_num_8 = Image.open(os.path.join(home_dir, "res/8.png"))
        self.pix_num_9 = Image.open(os.path.join(home_dir, "res/9.png"))
        self.pix_colon = Image.open(os.path.join(home_dir, "res/colon.png"))
        self.pix_dash = Image.open(os.path.join(home_dir, "res/dash.png"))
        self.pix_dot = Image.open(os.path.join(home_dir, "res/dot.png"))
        self.pix_blank = Image.open(os.path.join(home_dir, "res/blank.png"))
        self.pix_let_A = Image.open(os.path.join(home_dir, "res/A.png"))
        self.pix_let_D = Image.open(os.path.join(home_dir, "res/D.png"))
        self.pix_let_E = Image.open(os.path.join(home_dir, "res/E.png"))
        self.pix_let_F = Image.open(os.path.join(home_dir, "res/F.png"))
        self.pix_let_H = Image.open(os.path.join(home_dir, "res/H.png"))
        self.pix_let_I = Image.open(os.path.join(home_dir, "res/I.png"))
        self.pix_let_M = Image.open(os.path.join(home_dir, "res/M.png"))
        self.pix_let_N = Image.open(os.path.join(home_dir, "res/N.png"))
        self.pix_let_O = Image.open(os.path.join(home_dir, "res/O.png"))
        self.pix_let_R = Image.open(os.path.join(home_dir, "res/R.png"))
        self.pix_let_S = Image.open(os.path.join(home_dir, "res/S.png"))
        self.pix_let_T = Image.open(os.path.join(home_dir, "res/T.png"))
        self.pix_let_U = Image.open(os.path.join(home_dir, "res/U.png"))
        self.pix_let_V = Image.open(os.path.join(home_dir, "res/V.png"))
        self.pix_let_W = Image.open(os.path.join(home_dir, "res/W.png"))
        self.pix_nums = [self.pix_num_0, self.pix_num_1, self.pix_num_2, self.pix_num_3, self.pix_num_4, self.pix_num_5,
                         self.pix_num_6, self.pix_num_7, self.pix_num_8, self.pix_num_9]
        self.pix_letter = {"A": self.pix_let_A, "D": self.pix_let_D, "E": self.pix_let_E, "F": self.pix_let_F,
                           "H": self.pix_let_H, "I": self.pix_let_I, "M": self.pix_let_M, "N": self.pix_let_N,
                           "O": self.pix_let_O, "R": self.pix_let_R, "S": self.pix_let_S, "T": self.pix_let_T,
                           "U": self.pix_let_U, "V": self.pix_let_V, "W": self.pix_let_W}

        self.pix_percentage = Image.open(os.path.join(home_dir, "res/percentage.png"))

        self.bg = {"day_clear": [os.path.join(home_dir, "res/bg_day_clear1.png"),
                                 os.path.join(home_dir, "res/bg_day_clear2.png"),
                                 os.path.join(home_dir, "res/bg_day_clear3.png"),
                                 os.path.join(home_dir, "res/bg_day_clear4.png")],
                   "day_cloudy": [os.path.join(home_dir, "res/bg_day_cloudy1.png")],
                   "day_lrain": [os.path.join(home_dir, "res/bg_day_lrain1.png"),
                                 os.path.join(home_dir, "res/bg_day_lrain2.png"),
                                 os.path.join(home_dir, "res/bg_day_lrain3.png"),
                                 os.path.join(home_dir, "res/bg_day_lrain4.png")],
                   "day_rain": [os.path.join(home_dir, "res/bg_day_rain1.png"),
                                os.path.join(home_dir, "res/bg_day_rain2.png"),
                                os.path.join(home_dir, "res/bg_day_rain3.png"),
                                os.path.join(home_dir, "res/bg_day_rain4.png")],
                   "day_thunder": [os.path.join(home_dir, "res/bg_day_thunder1.png")],
                   "night_clear": [os.path.join(home_dir, "res/bg_night_clear1.png"),
                                   os.path.join(home_dir, "res/bg_night_clear2.png"),
                                   os.path.join(home_dir, "res/bg_night_clear3.png"),
                                   os.path.join(home_dir, "res/bg_night_clear4.png"),
                                   os.path.join(home_dir, "res/bg_night_clear5.png")],
                   "night_cloudy": [os.path.join(home_dir, "res/bg_night_cloudy1.png")],
                   "night_pcloudy": [os.path.join(home_dir, "res/bg_night_pcloudy1.png"),
                                     os.path.join(home_dir, "res/bg_night_pcloudy2.png"),
                                     os.path.join(home_dir, "res/bg_night_pcloudy3.png"),
                                     os.path.join(home_dir, "res/bg_night_pcloudy4.png"),
                                     os.path.join(home_dir, "res/bg_night_pcloudy5.png")],
                   "night_rain": [os.path.join(home_dir, "res/bg_night_rain1.png"),
                                  os.path.join(home_dir, "res/bg_night_rain2.png"),
                                  os.path.join(home_dir, "res/bg_night_rain3.png"),
                                  os.path.join(home_dir, "res/bg_night_rain4.png")],
                   "night_thunder": [os.path.join(home_dir, "res/bg_night_thunder1.png"),
                                     os.path.join(home_dir, "res/bg_night_thunder2.png")],
                   "sunrise": [os.path.join(home_dir, "res/bg_sunrise1.png"),
                               os.path.join(home_dir, "res/bg_sunrise2.png"),
                               os.path.join(home_dir, "res/bg_sunrise3.png"),
                               os.path.join(home_dir, "res/bg_sunrise4.png")],
                   "sunset": [os.path.join(home_dir, "res/bg_sunset1.png"),
                              os.path.join(home_dir, "res/bg_sunset2.png"),
                              os.path.join(home_dir, "res/bg_sunset3.png"),
                              os.path.join(home_dir, "res/bg_sunset4.png")],

                   "day_clear_nd": [os.path.join(home_dir, "res/bg_day_clear_nd1.png"),
                                    os.path.join(home_dir, "res/bg_day_clear_nd2.png"),
                                    os.path.join(home_dir, "res/bg_day_clear_nd3.png"),
                                    os.path.join(home_dir, "res/bg_day_clear_nd4.png")],
                   "day_cloudy_nd": [os.path.join(home_dir, "res/bg_day_cloudy_nd1.png")],
                   "day_lrain_nd": [os.path.join(home_dir, "res/bg_day_lrain_nd1.png"),
                                    os.path.join(home_dir, "res/bg_day_lrain_nd2.png"),
                                    os.path.join(home_dir, "res/bg_day_lrain_nd3.png"),
                                    os.path.join(home_dir, "res/bg_day_lrain_nd4.png")],
                   "day_rain_nd": [ os.path.join(home_dir, "res/bg_day_rain_nd1.png"),
                                    os.path.join(home_dir, "res/bg_day_rain_nd2.png"),
                                    os.path.join(home_dir, "res/bg_day_rain_nd3.png"),
                                    os.path.join(home_dir, "res/bg_day_rain_nd4.png")],
                   "day_thunder_nd": [os.path.join(home_dir, "res/bg_day_thunder_nd1.png")],
                   "night_clear_nd": [  os.path.join(home_dir, "res/bg_night_clear_nd1.png"),
                                        os.path.join(home_dir, "res/bg_night_clear_nd2.png"),
                                        os.path.join(home_dir, "res/bg_night_clear_nd3.png"),
                                        os.path.join(home_dir, "res/bg_night_clear_nd4.png"),
                                        os.path.join(home_dir, "res/bg_night_clear_nd5.png")],
                   "night_cloudy_nd": [os.path.join(home_dir, "res/bg_night_cloudy_nd1.png")],
                   "night_pcloudy_nd": [os.path.join(home_dir, "res/bg_night_pcloudy_nd1.png"),
                                        os.path.join(home_dir, "res/bg_night_pcloudy_nd2.png"),
                                        os.path.join(home_dir, "res/bg_night_pcloudy_nd3.png"),
                                        os.path.join(home_dir, "res/bg_night_pcloudy_nd4.png"),
                                        os.path.join(home_dir, "res/bg_night_pcloudy_nd5.png")],
                   "night_rain_nd": [   os.path.join(home_dir, "res/bg_night_rain_nd1.png"),
                                        os.path.join(home_dir, "res/bg_night_rain_nd2.png"),
                                        os.path.join(home_dir, "res/bg_night_rain_nd3.png"),
                                        os.path.join(home_dir, "res/bg_night_rain_nd4.png")],
                   "night_thunder_nd": [os.path.join(home_dir, "res/bg_night_thunder_nd1.png"),
                                        os.path.join(home_dir, "res/bg_night_thunder_nd2.png")],
                   "sunrise_nd": [  os.path.join(home_dir, "res/bg_sunrise_nd1.png"),
                                    os.path.join(home_dir, "res/bg_sunrise_nd2.png"),
                                    os.path.join(home_dir, "res/bg_sunrise_nd3.png"),
                                    os.path.join(home_dir, "res/bg_sunrise_nd4.png")],
                   "sunset_nd": [   os.path.join(home_dir, "res/bg_sunset_nd1.png"),
                                    os.path.join(home_dir, "res/bg_sunset_nd2.png"),
                                    os.path.join(home_dir, "res/bg_sunset_nd3.png"),
                                    os.path.join(home_dir, "res/bg_sunset_nd4.png")],
                   "blank": Image.open(os.path.join(home_dir, "res/bg_blank.png")),
                   "radio": os.path.join(home_dir, "res/bg_radio.png"),
                   "no_details": Image.open(os.path.join(home_dir, "res/bg_no_details.png"))}

        self.fg_frame = Image.open(os.path.join(home_dir, "res/fg_frame.png"))

        self.buttons = {
            "alarm": Image.open(os.path.join(home_dir, "res/bt_alarm.png")),
            "clock": Image.open(os.path.join(home_dir, "res/bt_clock.png")),
            "details": Image.open(os.path.join(home_dir, "res/bt_details.png")),
            "exit": Image.open(os.path.join(home_dir, "res/bt_exit.png")),
            "radio": Image.open(os.path.join(home_dir, "res/bt_radio.png")),
            "play": Image.open(os.path.join(home_dir, "res/bt_radio_play_off.png")),
            "station 1": Image.open(os.path.join(home_dir, "res/bt_radio_station_left_off.png")),
            "station 2": Image.open(os.path.join(home_dir, "res/bt_radio_station_right_off.png"))
        }
        self.buttons_selector = Image.open(os.path.join(home_dir, "res/bt_selected.png"))

        self.moon_phases = {
            "First Quarter": os.path.join(home_dir, "res/moon_first_quarter.png"),
            "Full Moon": os.path.join(home_dir, "res/moon_full.png"),
            "New Moon": os.path.join(home_dir, "res/moon_new_moon.png"),
            "Last Quarter": os.path.join(home_dir, "res/moon_third_quarter.png"),
            "Waning Gibbous": os.path.join(home_dir, "res/moon_waning_gibbous.png"),
            "Waning Crescent": os.path.join(home_dir, "res/moon_waning_crescent.png"),
            "Waxing Crescent": os.path.join(home_dir, "res/moon_waxing_crescent.png"),
            "Waxing Gibbous": os.path.join(home_dir, "res/moon_waxing_gibbous.png")
        }

        self.sun = Image.open(os.path.join(home_dir, "res/sun.png"))
        self.sun_black = Image.open(os.path.join(home_dir, "res/sun_black.png"))

        self.bar = {
            "sun_bar": Image.open(os.path.join(home_dir, "res/sun_bar.png")),
            "moon_bar": Image.open(os.path.join(home_dir, "res/moon_bar.png"))
        }
        self.pix_press_dot = Image.open(os.path.join(home_dir, "res/press_dot.png"))

        #Audio
        self.sound_button = os.path.join(home_dir, "res/button-press.mp3")


    def get_bg_path(self, name: str):
        if name in self.bg:
            try:
                bg_array = self.bg[name]
                index = get_random(len(bg_array))
                return bg_array[index]
            except:
                print("Could not get random background for " + name)
        return self.bg["day_clear"][0]

    def press_button(self):
        playsound(self.sound_button)
