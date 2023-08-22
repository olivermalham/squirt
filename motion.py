

# Motion information expected from the FarPI host
class MotionPacket:
    # Force vector
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Torque vector
    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0

    # Hold flags
    pitch_hold: bool = True
    roll_hold: bool = True
    yaw_hold: bool = False

    # Switches
    sw1: bool = 0
    sw2: bool = 0
    sw3: bool = 0
    sw4: bool = 0
    sw5: bool = 0
    sw6: bool = 0

    def map_to_motors(self):
        # Motors mapped clockwise from top right

        # Horizontal thrusters - assumes all point forwards
        # Motor 1 - horizontal top right
        motor1 = ((1.0 * self.x) + (-1.0 * self.y) + (0.0 * self.z)
                  + (0.0 * self.pitch) + (0.0 * self.roll) + (1.0 * self.yaw))

        # Motor 4 - horizontal bottom right
        motor4 = ((1.0 * self.x) + (-1.0 * self.y) + (0.0 * self.z)
                  + (0.0 * self.pitch) + (0.0 * self.roll) + (-1.0 * self.yaw))

        # Motor 5 - horizontal bottom left
        motor5 = ((1.0 * self.x) + (1.0 * self.y) + (0.0 * self.z)
                  + (0.0 * self.pitch) + (0.0 * self.roll) + (-1.0 * self.yaw))

        # Motor 8 - horizontal top left
        motor8 = ((1.0 * self.x) + (1.0 * self.y) + (0.0 * self.z)
                  + (0.0 * self.pitch) + (0.0 * self.roll) + (1.0 * self.yaw))

        # Vertical thrusters - assumes all point upwards
        # Motor 2 - vertical top right
        motor2 = ((0.0 * self.x) + (0.0 * self.y) + (1.0 * self.z)
                  + (1.0 * self.pitch) + (1.0 * self.roll) + (0.0 * self.yaw))

        # Motor 3 - vertical bottom right
        motor3 = ((0.0 * self.x) + (0.0 * self.y) + (1.0 * self.z)
                  + (-1.0 * self.pitch) + (1.0 * self.roll) + (0.0 * self.yaw))

        # Motor 6 - vertical bottom left
        motor6 = ((0.0 * self.x) + (0.0 * self.y) + (1.0 * self.z)
                  + (-1.0 * self.pitch) + (-1.0 * self.roll) + (0.0 * self.yaw))

        # Motor 7 - vertical top left
        motor7 = ((0.0 * self.x) + (0.0 * self.y) + (1.0 * self.z)
                  + (1.0 * self.pitch) + (-1.0 * self.roll) + (0.0 * self.yaw))

        return [motor1, motor2, motor3, motor4, motor5, motor6, motor7, motor8]


# Create a new motion packet from parameters. Called when a FarPi action is received
def action_motion(x, y, z, roll, pitch, yaw):
    print("action_motion x:{} y:{} z:{} roll:{} pitch:{} yaw:{}".format(x, y, z, roll, pitch, yaw))
    new_motion = MotionPacket()
    new_motion.x = x
    new_motion.y = y
    new_motion.z = z

    new_motion.roll = roll
    new_motion.pitch = pitch
    new_motion.yaw = yaw
    return new_motion
