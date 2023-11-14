import sys
import json
import uselect
from machine import I2C, Pin, mem32
import utime as time
from display import StatusDisplay
from servo import Servo, servo2040, ANGULAR
from libs.mpu9250 import MPU9250
from libs.fusion import Fusion
import motion
import status

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
i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400000)
# imu = MPU9250(i2c)
# fuse = Fusion()
display = StatusDisplay(i2c)
SIE_STATUS = const(0x50110000 + 0x50)
CONNECTED = const(1 << 16)
SUSPENDED = const(1 << 4)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Create servos
# ----------------------------------------------------------------------------------------------------------------------
output = [
    Servo(servo2040.SERVO_1, calibration=ANGULAR, freq=50),
    Servo(servo2040.SERVO_2, calibration=ANGULAR, freq=50),
    Servo(servo2040.SERVO_3, calibration=ANGULAR, freq=50),
    Servo(servo2040.SERVO_4, calibration=ANGULAR, freq=50),

    Servo(servo2040.SERVO_5, calibration=ANGULAR, freq=50),
    Servo(servo2040.SERVO_6, calibration=ANGULAR, freq=50),
    Servo(servo2040.SERVO_7, calibration=ANGULAR, freq=50),
    Servo(servo2040.SERVO_8, calibration=ANGULAR, freq=50),
]

[servo.enable() for servo in output]
[servo.to_percent(0.5) for servo in output]
# ----------------------------------------------------------------------------------------------------------------------


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

    # Refresh outputs at 50Hz to match standard servo PWM frequency
    if time.ticks_diff(time.ticks_ms(), last_update) > update_period:
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
            print(current_state_string)
            current_status.farpi_link = True
        else:
            current_status.farpi_link = False

        print(current_state_string)
        # print(current_status_string)

        # Update the digital outputs
        # TODO

        last_update = time.ticks_ms()
        count += 1

        display.refresh(current_status)

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

