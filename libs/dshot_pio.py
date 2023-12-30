import utime as time


class Dshot600:
    # Implements the DSHOT600 protocol
    # Output value is clamped to 0-2000
    # If telemetry is set to true, a UART will need to be configured to receive to get the data, this
    # class does not handle it (should it?)
    # TODO: Add the special commands, including suitable repeats
    def __init__(self, statemachine):
        self._sm = statemachine
        # self._sm = StateMachine(statemachine, dshot_prog, set_base=Pin(pin))
        self._sm.active(1)

    def send(self, value, telemetry=False, repeat=1):
        # Construct the frame and send it via PIO statemachine
        value = 2000 if abs(value) > 2000 else abs(value)
        frame = value << 1 | telemetry
        crc = (frame ^ (frame >> 4) ^ (frame >> 8)) & 0x0F  # CRC
        frame = (frame << 4) | crc

        for i in range(repeat):
            self._sm.put(frame << 16)  # Shift to ditch the top 16 bits

    def arm(self):
        start_time = time.ticks_ms()
        # Send a stream of motor stop commands for 400ms to arm the controller
        while time.ticks_diff(time.ticks_ms(), start_time) < 1100:
            self.send(0)
        # time.sleep_ms(500)
        # print("Armed")

    def motor_stop(self):
        # 0
        pass

    def beep1(self):
        # 1
        pass

    def beep2(self):
        # 2
        pass

    def beep3(self):
        # 3
        pass

    def beep4(self):
        # 4
        pass

    def beep5(self):
        # 5
        pass

    def info(self):
        # 6, 12ms min wait
        pass

    def direction_1(self):
        # 7
        # x6
        pass

    def direction_2(self):
        # 8
        # x6
        pass

    def three_d_mode(self, active=False):
        # 9 / 10
        # x6
        pass

    def save_settings(self):
        # 12
        # x6, 35ms min pause
        pass

    def enable_telemetry(self, value):
        # 32 disable, 33 enable x6
        pass

    # TODO!
    """
    Telemetry commands:
    42 temp 1C/bit
    43 volts 10mV/bit
    44 current 100mA/bit
    45 consumption 10mAh/bit
    46 eRPM 100erpm/bit
    47 telemetry period 16us/bit
    """
