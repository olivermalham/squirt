from machine import Pin
from rp2 import StateMachine, asm_pio


@asm_pio(autopull=True, pull_thresh=16, set_init=rp2.PIO.OUT_LOW)
def dshot_prog():
    # DShot600 frame length is 1.67us, 0.625us for zero, 1.25us for one, 0.42us dead band
    # Auto-pull set to 16 bits means this should only loop 16 times
    wrap_target()
    out(x, 1)  # Shift one bit out of the OSR into the X register - this is the next bit to send

    # Output minimum pulse length (for 0 bit) - 0.625us
    set(pins, 1)[31]
    set(pins, 1)[31]
    set(pins, 1)[12]
    jmp(not_x, "bitlow")  # If the bit is 0, jump over the high pulse

    # If bit is a 1 wait another 0.625us
    set(pins, 1)[31]
    set(pins, 1)[31]
    set(pins, 1)[13]
    jmp("deadspace")

    # Otherwise 0 for 0.625us
    label("bitlow")
    set(pins, 0)[31]
    set(pins, 0)[31]
    set(pins, 0)[13]

    # set output low for dead band for 0.42us
    label("deadspace")
    set(pins, 0)[31]
    set(pins, 0)[18]
    wrap()


class Dshot600:
    # Implements the DSHOT600 protocol
    def __init__(self, sm_id, pin):
        self._sm = StateMachine(sm_id, dshot_prog, set_base=Pin(pin))
        self._sm.active(1)

    def set(self, value, telemetry):
        # TODO - Need to build data frame
        self._sm.put(value << 16)

    def crc(self, value):
        pass
