from mpu9250 import MPU9250
from machine import I2C, Pin
from fusion import Fusion
import utime as time
from servo import Servo, servo2040, ANGULAR
from PID import PID
from uresponsivevalue import ResponsiveValue
import json
import uselect
import sys

from motion import action_motion, MotionState

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
# Configure the I2C IMU, sensor fusion
# ----------------------------------------------------------------------------------------------------------------------
i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400000)
imu = MPU9250(i2c)
fuse = Fusion()
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
current_motion = MotionState()


time.sleep(5)

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
            print("Command: {}".format(command_input))

            # Process command here
            try:
                command = json.loads(command_input)
                print("json.loads {}".format(command))
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
        fuse.update_nomag(imu.accel.xyz, imu.gyro.xyz)

        # Calculate the difference between the two orientation vectors
        # TODO

        # Update the command torque vector for each axis where hold = True
        # TODO

        # Map the translation and torque vector into individual motor powers
        motor_values = current_motion.map_to_motors()
        print(json.dumps(current_motion.__dict__))
        print(motor_values)

        # Smooth the motor power values
        # TODO

        # Output the motor powers to the ESCs
        # for i in range(len(output)):
        #     output[i].to_percent(motor_values[i])

        # Update the digital outputs
        # TODO

        last_update = time.ticks_ms()
        count += 1

        # Once a second loop
        if count % 50 == 0:
            pass
