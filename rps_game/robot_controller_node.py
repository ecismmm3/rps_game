import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import JointState
import math
import time

FINGER_JOINTS = []
for f in range(1, 6):
    for j in range(1, 4):
        FINGER_JOINTS.append(f'finger_{f}_joint_{j}')

def make_finger_positions(config):
    positions = []
    for f in range(1, 6):
        j1, j2, j3 = config[f]
        positions.extend([j1, j2, j3])
    return positions

CURL = -math.pi / 2

ROCK_CONFIG     = {f: (0.0, CURL, CURL) for f in range(1, 6)}
PAPER_CONFIG    = {f: (0.0, 0.0,  0.0)  for f in range(1, 6)}
SCISSORS_CONFIG = {
    1: (0.0, CURL, CURL),
    2: (0.0, 0.0,  0.0),
    3: (0.0, 0.0,  0.0),
    4: (0.0, CURL, CURL),
    5: (0.0, CURL, CURL),
}

ROCK_FINGERS     = make_finger_positions(ROCK_CONFIG)
PAPER_FINGERS    = make_finger_positions(PAPER_CONFIG)
SCISSORS_FINGERS = make_finger_positions(SCISSORS_CONFIG)

ALL_JOINTS = ['base_to_forearm', 'forearm_to_hand'] + FINGER_JOINTS


class RobotControllerNode(Node):

    def __init__(self):
        super().__init__('robot_controller_node')

        self.countdown_sub = self.create_subscription(
            String, '/countdown', self.countdown_callback, 10)
        self.choice_sub = self.create_subscription(
            String, '/robot_choice', self.choice_callback, 10)

        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.timer = self.create_timer(0.05, self.publish_current_pose) 

        self.forearm_angle = 0.0
        self.wrist_angle = 0.0
        self.finger_positions = PAPER_FINGERS  # default open hand
        
        self.mode = 'idle' # idle, countdown, result
        self.countdown_start = 0.0
        self.result_choice = 'paper'

        self.result_fingers = PAPER_FINGERS
        self.result_wrist = 0.0

        self.get_logger().info('Robot controller node ready.')

    def countdown_callback(self, msg):
        word = msg.data

        if word in ('rock', 'paper', 'scissors'):
            self.mode = 'countdown'
            self.countdown_start = time.time()
            self.finger_positions = ROCK_FINGERS
            self.wrist_angle = 0.0

        elif word == 'shoot':
            self.mode = 'shoot'
            self.countdown_start = time.time()

    def choice_callback(self, msg):
        self.result_choice = msg.data
        if msg.data == 'rock':
            self.result_fingers = ROCK_FINGERS
            self.result_wrist = 0.0
        elif msg.data == 'paper':
            self.result_fingers = PAPER_FINGERS
            self.result_wrist = 0.0
        elif msg.data == 'scissors':
            self.result_fingers = SCISSORS_FINGERS
            self.result_wrist = -0.6

    def publish_current_pose(self):
        now = time.time()

        if self.mode == 'countdown':
            elapsed = (now - self.countdown_start) % 1.0
            if elapsed < 0.5:
                self.forearm_angle = 0.4 + (elapsed / 0.5) * 0.8
            else:
                self.forearm_angle = 1.2 - ((elapsed - 0.5) / 0.5) * 0.8
            self.finger_positions = ROCK_FINGERS
            self.wrist_angle = 0.0

        elif self.mode == 'shoot':
            elapsed = now - self.countdown_start
            if elapsed < 0.5:
                self.forearm_angle = 0.4 + (elapsed / 0.5) * 0.8
                self.finger_positions = ROCK_FINGERS
                self.wrist_angle = 0.0
            else:
                self.mode = 'result'
                self.forearm_angle = 0.8
                self.finger_positions = self.result_fingers
                self.wrist_angle = self.result_wrist

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ALL_JOINTS
        msg.position = [self.forearm_angle, self.wrist_angle] + self.finger_positions
        self.joint_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RobotControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
