#! /usr/bin/env python3
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

class Talker2(Node):
    def __init__(self):
        super().__init__("2")
        self.i2 = 0
        self.pub2 = self.create_publisher2(String, "chatter", 10)
        timer_period2 = 1.0
        self.tmr2 = self.create_timer2(timer_period2, self.timer_callback2)

    def timer_callback2(self):
        msg2 = String()
        msg2.data = "Hello robotics students 2: {0}".format(self.i2)
        self.i2 += 1
        self.get_logger2().info2('Publishing 2: "{0}"'.format(msg2.data))
        self.pub2.publish(msg2)

def main(args=None):
    rclpy.init(args=args)

    node = Talker2()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()