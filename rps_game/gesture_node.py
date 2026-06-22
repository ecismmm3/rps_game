import rclpy
from rclpy.node import Node
from std_msgs.msg import String


CLASS_NAMES = ['paper', 'rock', 'scissors']


class GestureNode(Node):

    def __init__(self):
        super().__init__('gesture_node')
        self.publisher_ = self.create_publisher(String, '/player_gesture', 10)
        self.timer = self.create_timer(0.2, self.publish_gesture)
        self.gesture_file = '/mnt/c/Users/Ethan Chen/gesture.txt'
        self.get_logger().info('Gesture node ready.')

    def publish_gesture(self):
        try:
            with open(self.gesture_file, 'r') as f:
                gesture = f.read().strip()
            if gesture not in CLASS_NAMES:
                return
            msg = String()
            msg.data = gesture
            self.publisher_.publish(msg)
            self.get_logger().info(f'Gesture: {gesture}')
        except FileNotFoundError:
            self.get_logger().warn('Waiting for gesture file...')


def main(args=None):
    rclpy.init(args=args)
    node = GestureNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()