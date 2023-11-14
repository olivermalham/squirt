from libs import ssd1306
from status import Status


class StatusDisplay:
    # OLED, 128 x 32
    _device = None

    def __init__(self, i2c):
        self._device = ssd1306.SSD1306_I2C(128, 32, i2c)
        self.status = None

    def refresh(self, status):
        self.status = status
        self._device.fill(0)
        self.draw_battery()
        self.draw_cpu()
        self.draw_net()
        self.draw_esc()
        self.draw_farpi()

        self.draw_centered(status.status)
        self._device.show()

    def draw_battery(self):

        bar_length = int(((self.status.battery_volts - 9.0) / 2.0) * 26)

        self._device.rect(3, 0, 30, 9, 1)  # Battery outline
        self._device.fill_rect(33, 2, 3, 5, 1)  # Battery end tab
        self._device.fill_rect(5, 2, bar_length, 5, 1)  # Bar

        self.draw_right_justified("{}v".format(round(self.status.battery_volts, 1)), 40)

    def draw_cpu(self):
        if not self.status.odroid_power:
            return
        # self._device.rect(42, 0, 20, 20, 1)  # Icon boundary

        # CPU center
        if self.status.odroid_alive:
            self._device.fill_rect(46, 4, 12, 12, 1)
        else:
            self._device.rect(46, 4, 12, 12, 1)

        #  CPU pins
        self._device.line(47, 1, 47, 4, 1)
        self._device.line(50, 1, 50, 4, 1)
        self._device.line(53, 1, 53, 4, 1)
        self._device.line(56, 1, 56, 4, 1)

        self._device.line(47, 16, 47, 19, 1)
        self._device.line(50, 16, 50, 19, 1)
        self._device.line(53, 16, 53, 19, 1)
        self._device.line(56, 16, 56, 19, 1)

        self._device.line(43, 5, 46, 5, 1)
        self._device.line(43, 8, 46, 8, 1)
        self._device.line(43, 11, 46, 11, 1)
        self._device.line(43, 14, 46, 14, 1)

        self._device.line(58, 5, 61, 5, 1)
        self._device.line(58, 8, 61, 8, 1)
        self._device.line(58, 11, 61, 11, 1)
        self._device.line(58, 14, 61, 14, 1)

    def draw_net(self):
        # self._device.rect(64, 0, 20, 20, 1)  # Icon boundary

        if self.status.tether_link is False:
            return

        if self.status.tether_ethernet is False:
            self._device.rect(70, 0, 8, 8, 1)
            self._device.rect(64, 12, 8, 8, 1)
            self._device.rect(76, 12, 8, 8, 1)
        else:
            self._device.fill_rect(70, 0, 8, 8, 1)
            self._device.fill_rect(64, 12, 8, 8, 1)
            self._device.fill_rect(76, 12, 8, 8, 1)

        self._device.line(68, 10, 80, 10, 1)
        self._device.line(74, 8, 74, 10, 1)
        self._device.line(68, 10, 68, 12, 1)
        self._device.line(80, 10, 80, 12, 1)

    def draw_esc(self):
        # self._device.rect(86, 0, 20, 20, 1)  # Icon boundary

        self._device.rect(90, 0, 10, 9, 1)
        self._device.line(100, 4, 103, 4, 1)

        if self.status.esc_1_active:
            self._device.fill_rect(87, 10, 4, 4, 1)
        if self.status.esc_2_active:
            self._device.fill_rect(92, 10, 4, 4, 1)
        if self.status.esc_3_active:
            self._device.fill_rect(97, 10, 4, 4, 1)
        if self.status.esc_4_active:
            self._device.fill_rect(102, 10, 4, 4, 1)

        if self.status.esc_5_active:
            self._device.fill_rect(87, 16, 4, 4, 1)
        if self.status.esc_6_active:
            self._device.fill_rect(92, 16, 4, 4, 1)
        if self.status.esc_7_active:
            self._device.fill_rect(97, 16, 4, 4, 1)
        if self.status.esc_8_active:
            self._device.fill_rect(102, 16, 4, 4, 1)

    def draw_farpi(self):
        # self._device.rect(108, 0, 20, 20, 1)  # Icon boundary

        self._device.line(118, 12, 118, 19, 1)  # Stalk
        self._device.line(113, 20, 124, 20, 1)  # Base

        # Rays
        if self.status.farpi_link:
            self._device.fill_rect(116, 8, 5, 5, 1)  # Central aerial pip

            self._device.line(118, 1, 118, 5, 1)
            self._device.line(123, 10, 127, 10, 1)
            self._device.line(109, 10, 113, 10, 1)
            self._device.line(110, 2, 113, 5, 1)
            self._device.line(123, 5, 126, 2, 1)
        else:
            self._device.rect(116, 8, 5, 5, 1)  # Central aerial pip

        # Take the corners off the pip to look more rounded
        self._device.pixel(116, 8, 0)
        self._device.pixel(116, 12, 0)
        self._device.pixel(120, 8, 0)
        self._device.pixel(120, 12, 0)

    def draw_right_justified(self, text, origin):
        length = len(text) * 8
        start = origin - length
        self._device.text(text, start, 12, 1)

    def draw_centered(self, text):
        length = len(text) * 4
        start = 64 - length
        self._device.text(text, start, 24, 1)
