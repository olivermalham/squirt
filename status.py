class Status:

    battery_volts: float = 0.0
    odroid_alive: bool = False
    odroid_power: bool = False
    tether_ethernet: bool = False
    tether_link: bool = False

    farpi_link: bool = False

    esc_1_active: bool = True
    esc_2_active: bool = False
    esc_3_active: bool = False
    esc_4_active: bool = True

    esc_5_active: bool = True
    esc_6_active: bool = False
    esc_7_active: bool = True
    esc_8_active: bool = False

    status: str = ""

    def __init__(self):
        self.battery_volts = 11.0

        self.odroid_alive = False
        self.odroid_power = False
        self.tether_ethernet = False
        self.tether_link = False

        self.farpi_link = False

        self.esc_1_active = True
        self.esc_2_active = False
        self.esc_3_active = False
        self.esc_4_active = True

        self.esc_5_active = True
        self.esc_6_active = False
        self.esc_7_active = True
        self.esc_8_active = False

        self.status = ""
