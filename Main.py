import configparser
import getopt
import json
import logging
from pathlib import Path

import event_emitter as events
import vlc
from PyQt6.QtWidgets import QApplication

from RadioWindow import RadioWindow
from TimeWindow import TimeWindow
from spi_app.SPIWindow import SPIWindow

# Create and configure logger
logging.basicConfig(filename="clockradio.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')

W_HEIGHT = 320
W_WIDTH = 480
VERSION = "0.0.0"

stylesheet = """
    RadioWindow {
        background-image: url("res/bg_radio.png"); 
        background-repeat: no-repeat; 
        background-position: center;
    }
    TimeWindow {
        background-image: url("res/bg_day_clear1.png"); 
        background-repeat: no-repeat; 
        background-position: center;
    }
    QProgressBar {
        background-color: rgba(0, 0, 0, 128);
    }
    QProgressBar::chunk {
        background-color: rgba(255, 255, 255, 255);
    }
    QPushButton {
        background-color: rgba(0, 0, 0, 128);
        color: #FFFFFF;
    }
"""


# TODO:
# Do wind
# Alarm Window
class Main:
    def __init__(self):
        super().__init__()
        self.time_window = None
        self.radio_window = None
        self.channels = None
        self.log_level = None
        self.debug_mode = None
        self.config = configparser.ConfigParser()
        self.em = events.EventEmitter()

        # Add sections and key-value pairs
        self.config['General'] = {
            'debug': True,
            'log_level': 'info',
            'start_up': "RADIO"
        }
        self.config['Clock'] = {
            'show_details': "True"
        }
        self.config['Radio'] = {
            "channels": '[{"id": 0,"name": "Hot 102.7","url": "https://edge.iono.fm/xhls/57_high.m3u8"},{"id": 1,"name": "Hot 102.7 Rock","url": "https://edge.iono.fm/xhls/303_high.m3u8"}]',
            "current_channel": 0
        }

        config_file = Path("config.ini")
        if not config_file.exists():
            self.write_config()
        self.read_config()

        self.player = vlc.MediaPlayer()

        self.init_radio()

    def __del__(self):
        if self.player.is_playing():
            self.player.stop()

    def init_radio(self):
        self.channels = json.loads(self.config.get("Radio", "channels").replace("'", "\""))
        current_channel_index = int(self.config.get("Radio", "current_channel"))
        current_channel = None
        for channel in self.channels:
            if channel["id"] == current_channel_index:
                current_channel = channel
        if not current_channel is None:
            self.set_station(current_channel["url"])

    def set_station(self, url):
        self.player.set_mrl(url)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.stop()
            return False
        else:
            self.player.play()
            return True

    def write_config(self):
        # Write the configuration to a file
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def read_config(self):
        # Create a ConfigParser object
        self.config = configparser.ConfigParser()

        # Read the configuration file
        self.config.read('config.ini')

        # Access values from the configuration file
        self.debug_mode = self.config.getboolean('General', 'debug')
        self.log_level = self.config.get('General', 'log_level')

    def set_radio_window(self, new_radio_window):
        self.radio_window = new_radio_window

    def set_time_window(self, new_time_window):
        self.time_window = new_time_window

    def show_clock_wind(self):
        self.time_window.show()
        self.radio_window.hide()

    def show_radio_wind(self):
        self.radio_window.show()
        self.time_window.hide()

    def touch(self, x, y):
        pass


if __name__ == "__main__":
    import sys
    import os

    logger = logging.getLogger()
    home_dir = os.path.dirname(__file__)

    main = Main()
    logger.setLevel(logging._nameToLevel[main.config.get("General", "log_level").upper()])

    args = sys.argv[1:]
    options = "hltv"
    long_options = ["help", "headless", "test", "version"]

    start_headless = False
    start_test_mode = False
    try:
        arguments, values = getopt.getopt(args, options, long_options)
        for currentArg, currentVal in arguments:
            if currentArg in ("-h", "--Help"):
                print("Welcome to Clock Radio app!")
                print(f"Version {VERSION}")
                print("Website: TBD\n")
                print("Usage: python Main.py [global options] [command options]\n")
                print("Commands options:")
                print("    --headLess -l  Running as headless mode, input and out put through SPI")
                print("    --test -t      Output image as file (test1.BMP)\n")
                print("Global options:")
                print("    --help, -h     Show help")
                print("    --version, -v  Print the version\n")
                print("Create file call 'stop' to stop nohup/background process\n")
                sys.exit(0)
            elif currentArg in ("-v", "--version"):
                print("Welcome to Clock Radio app!")
                print(f"Version {VERSION}")
                print("Website: TBD\n")
                sys.exit(0)
            else:
                if currentArg in ("-l", "--headLess", "--Headless"):
                    logger.info("Running as headless")
                    start_headless = True
                if currentArg in ("-t", "--test", "--Test"):
                    logger.info("Running in Test mode")
                    start_test_mode = True
    except getopt.error as err:
        print(str(err))

    # If headless
    if start_headless:
        spiMain = SPIWindow(main, home_dir, start_test_mode)
    else:
        app = QApplication(sys.argv)
        app.setStyleSheet(stylesheet)

        time_window = TimeWindow(main)
        time_window.resize(W_WIDTH, W_HEIGHT)
        time_window.setGeometry(0, 0, W_WIDTH, W_HEIGHT)
        main.set_time_window(time_window)
        time_window.show()

        radio_window = RadioWindow(main)
        radio_window.resize(W_WIDTH, W_HEIGHT)
        radio_window.setGeometry(0, 0, W_WIDTH, W_HEIGHT)
        main.set_radio_window(radio_window)

        sys.exit(app.exec())
