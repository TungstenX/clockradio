# AI Generate code
import logging
import threading
import time

import event_emitter as events
import pigpio
import spidev
from PIL import Image

spi_lock = threading.Lock()

em = events.EventEmitter()
# ========== CONFIG ==========
GPIO_DC       = 25  # BCM GPIO for D/C (Data/Command)
GPIO_RESET    = 24  # BCM GPIO for RESET
GPIO_LCD_CS   = 8
GPIO_TOUCH_CS = 7
GPIO_TIRQ     = 17 # (PIN 11)
GPIO_TCS      = 27
# Rotary encoder (RE)
GPIO_RE_CLK = 4   # GPIO04 connected to the rotary encoder's CLK pin (PIN 7)
GPIO_RE_DT  = 23  # GPIO23 connected to the rotary encoder's DT pin (PIN 16)
GPIO_RE_SW  = 22  # GPIO22 connected to the rotary encoder's SW pin (PIN 15)

SPI_BUS    = 0
SPI_DEVICE = 0
SPI_MAX_HZ = 48000000  # try high, reduce if unstable

# Set your display size here (common: 320x480 or 480x320)
WIDTH  = 320
HEIGHT = 480


# ============================

# ------- pack RGB888 -> RGB666 bytes -------
def rgb888_to_rgb666_bytes(image: Image.Image):
    """
    Accepts a Pillow RGB image sized WIDTH x HEIGHT.
    Returns bytes arranged as [R6,G6,B6, R6,G6,B6, ...] where R6=R>>2
    """
    w, h = image.size
    assert (w, h) == (WIDTH, HEIGHT)
    raw = image.tobytes()  # RGBRGB...
    out = bytearray()
    # iterate raw in steps of 3
    for i in range(0, len(raw), 3):
        r = raw[i]
        g = raw[i + 1]
        b = raw[i + 2]
        out.append(r >> 2)
        out.append(g >> 2)
        out.append(b >> 2)
    return bytes(out)


class SPIClient:
    def __init__(self, event_m):
        super().__init__()

        self.logger = logging.getLogger()
        # ------- helpers for SPI/GPIO -------
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise SystemExit("pigpio daemon not running. Start with: sudo pigpiod")

        self.spi_touch = self.pi.spi_open(SPI_BUS, 2000000, 0)
        self.logger.info(f"SPI HANDLE: {str(self.spi_touch)} {str(type(self.spi_touch))}")
        self.spi_display = spidev.SpiDev()
        self.spi_display.open(SPI_BUS, SPI_DEVICE)
        self.spi_display.max_speed_hz = SPI_MAX_HZ
        self.spi_display.mode = 0b00
        self.pi.set_mode(GPIO_DC, pigpio.OUTPUT)
        self.pi.set_mode(GPIO_RESET, pigpio.OUTPUT)
        self.pi.set_mode(GPIO_LCD_CS, pigpio.OUTPUT)
        self.pi.set_mode(GPIO_TOUCH_CS, pigpio.OUTPUT)
        self.ili_init()

        self.pi.set_mode(GPIO_TIRQ, pigpio.INPUT)
        self.pi.set_pull_up_down(GPIO_TIRQ, pigpio.PUD_UP)

        self.pi.set_mode(GPIO_TCS, pigpio.OUTPUT)
        self.pi.write(GPIO_TCS, 1)

        self.pi.set_mode(GPIO_RE_CLK, pigpio.INPUT)
        self.pi.set_mode(GPIO_RE_DT, pigpio.INPUT)
        self.pi.set_mode(GPIO_RE_SW, pigpio.INPUT)
        self.pi.set_pull_up_down(GPIO_RE_CLK, pigpio.PUD_UP)
        self.pi.set_pull_up_down(GPIO_RE_DT, pigpio.PUD_UP)
        self.pi.set_pull_up_down(GPIO_RE_SW, pigpio.PUD_UP)

        # Register interrupt callback
        self.reading = False
        self.cb = self.pi.callback(GPIO_TIRQ, pigpio.FALLING_EDGE, self.irq_callback)
        self.encoder = self.pi.callback(GPIO_RE_CLK, pigpio.RISING_EDGE, self.encoder_callback)
        self.event_emitter = event_m

    def read_coord(self, cmd):
        with spi_lock:
            try:
                self.pi.write(GPIO_TCS, 0)
                _, data = self.pi.spi_xfer(self.spi_touch, bytes([cmd, 0, 0]))
                self.pi.write(GPIO_TCS, 1)
            except:
                self.logger.error("Error while read_coord")
        value = ((data[1] << 8) | data[2]) >> 3
        return value

    def read_touch_worker(self):
        self.reading = True
        try:
            # keep reading while pen touches screen
            while self.pi.read(GPIO_TIRQ) == 0:
                self.pi.write(GPIO_TOUCH_CS, 0)

                x = self.read_coord(0x90)  # X command
                y = self.read_coord(0xD0)  # Y command

                self.pi.write(GPIO_TOUCH_CS, 1)
                self.logger.info(f"Touch: ({x}, {y})")
                self.event_emitter.emit('touch')

                time.sleep(0.02)
        except:
            self.logger.error("Error while read_touch_worker")
        finally:
            self.reading = False

    # Encoder callback
    def encoder_callback(self, gpio, level, tick):
        print(f"encode_callback: {gpio} {level} {tick}")
        # if level == 0 and not self.reading:
        #     # launch worker thread
        #     threading.Thread(target=self.read_touch_worker, daemon=True).start()

    # IRQ callback
    def irq_callback(self, gpio, level, tick):
        if level == 0 and not self.reading:
            # launch worker thread
            threading.Thread(target=self.read_touch_worker, daemon=True).start()

    def gpio_write(self, pin, level):
        try:
            self.pi.write(pin, 1 if level else 0)
        except:
            self.logger.error("Error while gpio_write")

    def hw_reset(self):
        self.gpio_write(GPIO_RESET, 0)
        time.sleep(0.05)
        self.gpio_write(GPIO_RESET, 1)
        time.sleep(0.15)

    # DC: 0 = command, 1 = data (we'll call set_dc(0/1))
    def set_dc(self, is_data: bool):
        self.gpio_write(GPIO_DC, 1 if is_data else 0)

    def send_cmd(self, cmd):
        try:
            self.set_dc(False)
            # use xfer2 for full-duplex safe transfer
            self.spi_display.xfer2([cmd])
        except:
            self.logger.error("Error while send_cmd")

    def send_data_bytes(self, bts):
        self.set_dc(True)
        self.gpio_write(GPIO_LCD_CS, 0)
        try:
            # bts is bytes or list of ints; send in chunks to avoid huge allocations
            CHUNK = 4096
            if isinstance(bts, bytes):
                view = memoryview(bts)
                for i in range(0, len(view), CHUNK):
                    self.spi_display.xfer2(list(view[i:i + CHUNK]))
            else:
                for i in range(0, len(bts), CHUNK):
                    self.spi_display.xfer2(bts[i:i + CHUNK])
        except TimeoutError:
            self.logger.error("Time out error while send data bytes")
        except:
            self.logger.error("Error while send data bytes")
        self.gpio_write(GPIO_LCD_CS, 1)

    # ------- ILI9488 init (minimal, common sequence) -------
    def ili_init(self):
        self.hw_reset()
        # Some common init sequences — may need tweaks per module
        self.send_cmd(0xE0);
        self.send_data_bytes([0x00, 0x07, 0x0F, 0x0D, 0x1B, 0x0A, 0x3C, 0x78, 0x4A, 0x07, 0x0E, 0x09, 0x1B, 0x1E, 0x0F])
        self.send_cmd(0xE1);
        self.send_data_bytes([0x00, 0x22, 0x24, 0x06, 0x12, 0x07, 0x36, 0x47, 0x47, 0x06, 0x0A, 0x07, 0x30, 0x37, 0x0F])
        self.send_cmd(0xC0);
        self.send_data_bytes([0x17, 0x15])
        self.send_cmd(0xC1);
        self.send_data_bytes([0x41])
        self.send_cmd(0xC5);
        self.send_data_bytes([0x00, 0x12, 0x80])
        # Pixel Format: 0x66 -> 18-bit (RGB666)
        self.send_cmd(0x3A);
        self.send_data_bytes([0x66])
        # Memory Access Control: orientation (may need change)
        self.send_cmd(0x36);
        self.send_data_bytes([0x48])
        self.send_cmd(0x11);
        time.sleep(0.12)  # Sleep Out
        self.send_cmd(0x29);
        time.sleep(0.05)  # Display ON

    # ------- set column/row window -------
    def set_window(self, x0, y0, x1, y1):
        # column
        self.send_cmd(0x2A)
        self.send_data_bytes([(x0 >> 8) & 0xFF, x0 & 0xFF, (x1 >> 8) & 0xFF, x1 & 0xFF])
        # page
        self.send_cmd(0x2B)
        self.send_data_bytes([(y0 >> 8) & 0xFF, y0 & 0xFF, (y1 >> 8) & 0xFF, y1 & 0xFF])
        self.send_cmd(0x2C)

    # ------- flood fill (single color) -------
    def flood_color_rgb666(self, r6, g6, b6):
        # r6,g6,b6 are 6-bit values (0..63)
        # build one line and stream it
        pixel = [r6 & 0x3F, g6 & 0x3F, b6 & 0x3F]
        line = pixel * WIDTH
        self.set_window(0, 0, WIDTH - 1, HEIGHT - 1)
        # write each line
        for _ in range(HEIGHT):
            self.send_data_bytes(line)

    # ------- main flow -------
    def output_image(self, image: Image.Image):
        # export pins as outputs
        self.logger.debug("Converting image to RGB666 (this may take a few seconds)...")
        data = rgb888_to_rgb666_bytes(image)
        self.set_window(0, 0, WIDTH - 1, HEIGHT - 1)
        self.logger.debug("Writing image to display...")
        self.send_data_bytes(data)
        self.logger.debug("Done writing image to display.")

    def close(self):
        try:
            self.spi_display.close()
            if self.cb:
                self.cb.cancel()

            if self.encoder:
                self.encoder.cancel()

            self.pi.stop()
        except:
            self.logger.error("Error while close")
