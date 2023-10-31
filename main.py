import sys
import json
import uselect
from machine import I2C, Pin
import utime as time
from display import StatusDisplay
from servo import Servo, servo2040, ANGULAR
from libs.mpu9250 import MPU9250
from libs.fusion import Fusion
import motion

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
#
# Example packets:
# {"action":"action_motion", "parameters":{"x":1.0, "y":0.0, "z":0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}}
# {"action":"action_motion", "parameters":{"x":0.0, "y":1.0, "z":0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}}
# {"action":"action_motion", "parameters":{"x":0.0, "y":0.0, "z":1.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}}
#
# {"action":"action_motion", "parameters":{"x":0.0, "y":0.0, "z":0.0, "roll": 1.0, "pitch": 0.0, "yaw": 0.0}}
# {"action":"action_motion", "parameters":{"x":0.0, "y":0.0, "z":0.0, "roll": 0.0, "pitch": 1.0, "yaw": 0.0}}
# {"action":"action_motion", "parameters":{"x":0.0, "y":0.0, "z":0.0, "roll": 0.0, "pitch": 0.0, "yaw": 1.0}}
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Configure peripherals, sensor fusion
# ----------------------------------------------------------------------------------------------------------------------
i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400000)
# imu = MPU9250(i2c)
# fuse = Fusion()
display = StatusDisplay(i2c)
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
            # print("Command: {}".format(command_input))

            # Process command here
            # TODO: This is a mess. No need for such general purpose code here
            try:
                command = json.loads(command_input)
                # print("json.loads {}".format(command))
                action = command["action"]
                parameters = command["parameters"]
                # action_motion(**parameters)
                target = eval(action)
                if callable(target):
                    # Pass the HAL instance down to the component
                    current_motion = target(**parameters)
            except:
                # TODO:Need to do better than this!
                print("Exception!")
            # Clear the buffer
            command_input = ""

            # result = {}
            # actions = []
            # for entry in dir():
            #     if entry.startswith("action_"):
            #         actions.append(f"{entry}")
            # result["actions"] = actions
            # return json.dumps(result)

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

        current_state = current_motion.__dict__
        print(json.dumps(current_state))

        # Smooth the motor power values?
        # TODO

        # Output the motor powers to the ESCs
        # for i in range(len(output)):
        #     output[i].to_percent(motor_values[i])

        # Update the digital outputs
        # TODO

        last_update = time.ticks_ms()
        count += 1

        display.refresh()

        # Once a second loop
        if count % 50 == 0:

            display.status = "Count {}".format(count)

            display.battery_volts = display.battery_volts - 0.1 if display.battery_volts > 9.0 else 11.0

            # off -> power -> alive -> off
            if display.odroid_power is False:
                display.odroid_power = True
                display.tether_link = True
                display.farpi_link = True
            elif display.odroid_power and display.odroid_alive is False:
                display.odroid_alive = True
                display.tether_ethernet = True
            else:
                display.odroid_alive = False
                display.odroid_power = False
                display.tether_link = False
                display.tether_ethernet = False
                display.farpi_link = False

            # print("Test loop: {} - {} : {}".format(test_loop, test_data[test_loop], motor_values))
            # print("IMU: Pitch: {}\tRoll: {}\tYaw: {}".format(current_motion.roll,
            #                                                  current_motion.pitch,
            #                                                  current_motion.yaw))
            # if count % 500 == 0:
            #     # current_motion = motion.action_motion(*[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            #     test_loop = test_loop + 1 if (test_loop < len(test_data) - 1) else 0

