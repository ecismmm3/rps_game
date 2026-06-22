import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import random
import time


RULES = {
    ('rock', 'scissors'): 'player',
    ('paper', 'rock'): 'player',
    ('scissors', 'paper'): 'player',
    ('scissors', 'rock'): 'robot',
    ('rock', 'paper'): 'robot',
    ('paper', 'scissors'): 'robot',
}

CLASS_NAMES = ['paper', 'rock', 'scissors']


class GameLogicNode(Node):

    def __init__(self):
        super().__init__('game_logic_node')

        self.subscription = self.create_subscription(
            String, '/player_gesture', self.gesture_callback, 10)

        self.robot_pub = self.create_publisher(String, '/robot_choice', 10)
        self.result_pub = self.create_publisher(String, '/game_result', 10)
        self.countdown_pub = self.create_publisher(String, '/countdown', 10)

        self.player_score = 0
        self.robot_score = 0
        self.latest_gesture = 'rock'

        # game state
        self.state = 'waiting'      # waiting, countdown, result_pause
        self.countdown_step = 0
        self.countdown_start = 0.0
        self.pause_start = 0.0

        # 10hz tick drives the state machine
        self.timer = self.create_timer(0.1, self.tick)

        self.get_logger().info('Game logic node ready.')

    def gesture_callback(self, msg):
        # always track latest gesture
        self.latest_gesture = msg.data

    def tick(self):
        now = time.time()

        if self.state == 'waiting':
            # start a new countdown
            self.state = 'countdown'
            self.countdown_step = 0
            self.countdown_start = now
            self.get_logger().info('Starting countdown...')

        elif self.state == 'countdown':
            elapsed = now - self.countdown_start
            step = int(elapsed)  # 0=rock, 1=paper, 2=scissors, 3=shoot

            if step != self.countdown_step:
                self.countdown_step = step

                if step == 0:
                    self._pub_countdown('rock')
                elif step == 1:
                    self._pub_countdown('paper')
                elif step == 2:
                    self._pub_countdown('scissors')
                elif step == 3:
                    self._pub_countdown('shoot')
                    # lock in gestures at shoot
                    self._resolve_round()
                    self.state = 'result_pause'
                    self.pause_start = now

        elif self.state == 'result_pause':
            if now - self.pause_start >= 5.0:
                self.state = 'waiting'

    def _pub_countdown(self, word):
        msg = String()
        msg.data = word
        self.countdown_pub.publish(msg)
        self.get_logger().info(f'Countdown: {word.upper()}')

    def _resolve_round(self):
        player_gesture = self.latest_gesture
        robot_gesture = random.choice(CLASS_NAMES)

        if player_gesture == robot_gesture:
            result = 'Tie'
        else:
            winner = RULES.get((player_gesture, robot_gesture), 'robot')
            if winner == 'player':
                self.player_score += 1
                result = 'Player wins'
            else:
                self.robot_score += 1
                result = 'Robot wins'

        self.get_logger().info(
            f'Player: {player_gesture} | Robot: {robot_gesture} | {result} '
            f'(Score: You {self.player_score} - {self.robot_score} Robot)'
        )

        robot_msg = String()
        robot_msg.data = robot_gesture
        self.robot_pub.publish(robot_msg)

        result_msg = String()
        result_msg.data = result
        self.result_pub.publish(result_msg)


def main(args=None):
    rclpy.init(args=args)
    node = GameLogicNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()