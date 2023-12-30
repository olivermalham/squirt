import sys
import json
import uselect
from machine import mem32, Pin
import utime as time
from micropython import const
from rp2 import StateMachine, asm_pio
import motion
import status
from libs.dshot_pio import Dshot600

# ----------------------------------------------------------------------------------------------------------------------
# NOTES
#
# Need to be able to lock orientation in 2-3 axis (depending on if heading can be reliably determined)
# Translation will not need any processing other than mapping values and some smoothing (is PID required?)
# Translation values are effectively force values, represented as a fraction of the maximum force available
# TODO: Figure out how rotation hold is going to work
#
# Packet from controller will be 6 axis force values - translation and rotation.
# Additional fields for hold flags, and a few digital switches for lighting etc
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Configure peripherals, sensor fusion
# ----------------------------------------------------------------------------------------------------------------------
# i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400000)
# imu = MPU9250(i2c)
# fuse = Fusion()
# display = StatusDisplay(i2c)
SIE_STATUS = const(0x50110000 + 0x50)
CONNECTED = const(1 << 16)
SUSPENDED = const(1 << 4)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# PIO code for DShot protocol. For some reason MicroPython doesn't like importing libraries in sub-files, so have
# to make it messy like this. Not happy :(
# ----------------------------------------------------------------------------------------------------------------------
@asm_pio(autopull=True, pull_thresh=16, set_init=rp2.PIO.OUT_LOW)
def dshot_prog():
    # DShot600 frame length is 1.67us, 0.625us for zero, 1.25us for one, 0.42us dead band
    # Loop values here have been tuned via oscilloscope
    # Code is crude but does the job!
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


# ----------------------------------------------------------------------------------------------------------------------
# Create motor controllers
# ----------------------------------------------------------------------------------------------------------------------
output = [
    Dshot600(statemachine=StateMachine(0, dshot_prog, set_base=Pin(2), freq=125_000_000)),
    Dshot600(statemachine=StateMachine(1, dshot_prog, set_base=Pin(3), freq=125_000_000)),
    Dshot600(statemachine=StateMachine(2, dshot_prog, set_base=Pin(4), freq=125_000_000)),
    Dshot600(statemachine=StateMachine(3, dshot_prog, set_base=Pin(5), freq=125_000_000)),

    Dshot600(statemachine=StateMachine(4, dshot_prog, set_base=Pin(6), freq=125_000_000)),
    Dshot600(statemachine=StateMachine(5, dshot_prog, set_base=Pin(7), freq=125_000_000)),
    Dshot600(statemachine=StateMachine(6, dshot_prog, set_base=Pin(8), freq=125_000_000)),
    Dshot600(statemachine=StateMachine(7, dshot_prog, set_base=Pin(9), freq=125_000_000))
]

# ----------------------------------------------------------------------------------------------------------------------
motor_value = 48
motor_delta = 1

# ----------------------------------------------------------------------------------------------------------------------
# Get timing stuff sorted out
# ----------------------------------------------------------------------------------------------------------------------
last_update = time.ticks_ms()
update_period = 1000/50  # Milliseconds between updates
count = 0
command_input = ""
current_motion = motion.MotionState()
target_motion = current_motion

test_data = [
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
]
test_loop = 0

# TODO NEXT
# 1. Test vertical thrust output / mixing DONE
# 2. Write / test basic stabilisation DONE
# 3. Get the connection to FarPi finished
# 4. Get D-Shot PIO working
# 5. Get sensor reading working DONE (for IMU)
# 6. Get status display designed and implemented DONE


def correction(orientation):
    delta = orientation / 90.0
    delta = 0.0 if (0.0 < delta < 0.1) else delta
    delta = 0.0 if (0.0 > delta > -0.1) else delta
    delta = 1.0 if delta > 1.0 else delta
    delta = -1.0 if delta < -1.0 else delta
    return round(delta, 2)


current_status = status.Status()


# Arm the motors
# [motor.arm() for motor in output]
for i in range(500):
    [motor.send(48) for motor in output]
for i in range(500):
    [motor.send(2000) for motor in output]
for i in range(500):
    [motor.send(48) for motor in output]


# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
while True:

    # Check if there is a new motion packet ready
    # If so, set it as the new command
    # If we get a Ctrl-A, then exit the program to allow raw REPL mode
    if uselect.select([sys.stdin], [], [], 0)[0]:
        c = sys.stdin.read(1)

        # Ctrl-A code exits immediately to allow reprogramming etc
        if c == 1:
            print("Bailing out")
            exit()

        if c != '\n':
            command_input = command_input + c
        else:
            # Process command here - single action, just sets the target state to the passed parameters
            try:
                command = json.loads(command_input)
                action = command["action"]
                parameters = command["parameters"]
                target_motion = motion.action_motion(**parameters)
            except:
                pass
            # Clear the buffer
            command_input = ""
        # current_status.status = command_input

    # if time.ticks_diff(time.ticks_ms(), last_update) > 1:
    [motor.send(motor_value) for motor in output]

    # Refresh outputs at 50Hz to match standard servo PWM frequency
    if time.ticks_diff(time.ticks_ms(), last_update) > update_period:
        motor_value += motor_delta

        if motor_value >= 2000:
            motor_delta = -1
        if motor_value <= 48:
            motor_delta = 1

        # print(motor_value)
        # Update the target orientation vector using the new motion vector
        # TODO

        # Get the current orientation vector
        # fuse.update_nomag(imu.accel.xyz, imu.gyro.xyz)

        # Calculate the difference between the two orientation vectors
        # TODO

        # Update the command torque vector for each axis where hold = True
        # TODO
        # FIXME! Need to capture IMU measured values as well as the target vectors
        # current_motion = motion.action_motion(0, 0, 0,
        #                                       correction(fuse.pitch),
        #                                       correction(fuse.roll),
        #                                       correction(fuse.heading))

        # Map the translation and torque vector into individual motor powers
        motor_values = current_motion.map_to_motors()

        current_state_string = json.dumps(current_motion.__dict__)
        current_status_string = json.dumps(current_status.__dict__)

        current_state_string = current_state_string[:-1] + "," + current_status_string[1:]

        if (mem32[SIE_STATUS] & (CONNECTED | SUSPENDED)) == CONNECTED:
            # print(current_state_string)
            current_status.farpi_link = True
        else:
            current_status.farpi_link = False

        # print(current_status_string)

        # Update the digital outputs
        # TODO

        last_update = time.ticks_ms()
        count += 1

        # display.refresh(current_status)

        # Motor test
        # [motor.send(1999) for motor in output]

        # Once a second loop
        if count % 50 == 0:

            # current_status.status = "Count {}".format(count)

            current_status.battery_volts = current_status.battery_volts - 0.1 if current_status.battery_volts > 9.0 else 11.0

            # off -> power -> alive -> off
            if current_status.odroid_power is False:
                current_status.odroid_power = True
                current_status.tether_link = True
                # current_status.farpi_link = True
            elif current_status.odroid_power and current_status.odroid_alive is False:
                current_status.odroid_alive = True
                current_status.tether_ethernet = True
            else:
                current_status.odroid_alive = False
                current_status.odroid_power = False
                current_status.tether_link = False
                current_status.tether_ethernet = False
                # current_status.farpi_link = False

            # print("Test loop: {} - {} : {}".format(test_loop, test_data[test_loop], motor_values))
            # print("IMU: Pitch: {}\tRoll: {}\tYaw: {}".format(current_motion.roll,
            #                                                  current_motion.pitch,
            #                                                  current_motion.yaw))
            # if count % 500 == 0:
            #     # current_motion = motion.action_motion(*[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            #     test_loop = test_loop + 1 if (test_loop < len(test_data) - 1) else 0

