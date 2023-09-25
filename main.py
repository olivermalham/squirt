import motion
from libs import ssd1306
from machine import I2C, Pin
import utime as time
from servo import Servo, servo2040, ANGULAR

from motion import MotionState

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

display = ssd1306.SSD1306_I2C(128, 32, i2c)
# ----------------------------------------------------------------------------------------------------------------------


# Sleep required to give a chance to program before serial coms start on the same UART
# time.sleep(5)


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


test_data = [
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
]
test_loop = 0

display.poweron()
display.invert(1)
display.text('Squirt Starting...', 3, 3, 1)
display.show()


# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
while True:

    # Check if there is a new motion packet ready
    # If so, set it as the new command
    # If we get a Ctrl-A, then exit the program to allow raw REPL mode
    # if uselect.select([sys.stdin], [], [], 0)[0]:
    #     c = sys.stdin.read(1)
    #
    #     # Ctrl-A code exits immediately to allow reprogramming etc
    #     if c == 1:
    #         print("Bailing out")
    #         exit()
    #
    #     if c != '\n':
    #         command_input = command_input + c
    #     else:
    #         print("Command: {}".format(command_input))
    #
    #         # Process command here
    #         # TODO: This is a mess. No need for such general purpose code here
    #         try:
    #             command = json.loads(command_input)
    #             # print("json.loads {}".format(command))
    #             action = command["action"]
    #             parameters = command["parameters"]
    #             # action_motion(**parameters)
    #             target = eval(action)
    #             if callable(target):
    #                 # Pass the HAL instance down to the component
    #                 current_motion = target(**parameters)
    #         except:
    #             # TODO:Need to do better than this!
    #             print("Exception!")
    #         # Clear the buffer
    #         command_input = ""
    #
    #         # result = {}
    #         # actions = []
    #         # for entry in dir():
    #         #     if entry.startswith("action_"):
    #         #         actions.append(f"{entry}")
    #         # result["actions"] = actions
    #         # return json.dumps(result)

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

        # Map the translation and torque vector into individual motor powers
        motor_values = current_motion.map_to_motors()
        # print(json.dumps(current_motion.__dict__))
        # print(motor_values)

        # Smooth the motor power values
        # TODO

        # Output the motor powers to the ESCs
        for i in range(len(output)):
            output[i].to_percent(motor_values[i])

        # Update the digital outputs
        # TODO

        last_update = time.ticks_ms()
        count += 1

        # Once a second loop
        if count % 50 == 0:
            current_motion = motion.action_motion(*test_data[test_loop])
            display.fill(0)
            display.text("test_loop: {}".format(test_loop), 3, 3, 1)
            display.show()
            print("Test loop: {} - {} : {}".format(test_loop, test_data[test_loop], motor_values))
            if count % 500 == 0:
                # current_motion = motion.action_motion(*[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                test_loop = test_loop + 1 if (test_loop < len(test_data) - 1) else 0


#
# from machine import Pin, I2C
# import ssd1306
#
# # using default address 0x3C
# i2c = I2C(sda=Pin(4), scl=Pin(5))
# display = ssd1306.SSD1306_I2C(128, 64, i2c)
#
# display.text('Hello, World!', 0, 0, 1)
# display.show()
#
# # Basic functions:
#
# display.poweroff()     # power off the display, pixels persist in memory
# display.poweron()      # power on the display, pixels redrawn
# display.contrast(0)    # dim
# display.contrast(255)  # bright
# display.invert(1)      # display inverted
# display.invert(0)      # display normal
# display.rotate(True)   # rotate 180 degrees
# display.rotate(False)  # rotate 0 degrees
# display.show()         # write the contents of the FrameBuffer to display memory
#
# # Subclassing FrameBuffer provides support for graphics primitives:
# display.fill(0)                         # fill entire screen with colour=0
# display.pixel(0, 10)                    # get pixel at x=0, y=10
# display.pixel(0, 10, 1)                 # set pixel at x=0, y=10 to colour=1
# display.hline(0, 8, 4, 1)               # draw horizontal line x=0, y=8, width=4, colour=1
# display.vline(0, 8, 4, 1)               # draw vertical line x=0, y=8, height=4, colour=1
# display.line(0, 0, 127, 63, 1)          # draw a line from 0,0 to 127,63
# display.rect(10, 10, 107, 43, 1)        # draw a rectangle outline 10,10 to 117,53, colour=1
# display.fill_rect(10, 10, 107, 43, 1)   # draw a solid rectangle 10,10 to 117,53, colour=1
# display.text('Hello World', 0, 0, 1)    # draw some text at x=0, y=0, colour=1
# display.scroll(20, 0)                   # scroll 20 pixels to the right
#
# # draw another FrameBuffer on top of the current one at the given coordinates
# import framebuf
# fbuf = framebuf.FrameBuffer(bytearray(8 * 8 * 1), 8, 8, framebuf.MONO_VLSB)
# fbuf.line(0, 0, 7, 7, 1)
# display.blit(fbuf, 10, 10, 0)           # draw on top at x=10, y=10, key=0
# display.show()