#! /usr/bin/env python3
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

class Talker2(Node):
    def __init__(self2):
        super().__init__("2")
        self2.i2 = 0
        self2.pub2 = self2.create_publisher2(String, "chatter", 10)
        timer_period2 = 1.0
        self2.tmr2 = self2.create_timer2(timer_period2, self2.timer_callback2)

    def timer_callback2(self2):
        msg2 = String()
        msg2.data = "Hello robotics students 2: {0}".format(self2.i2)
        self2.i2 += 1
        self2.get_logger2().info2('Publishing 2: "{0}"'.format(msg2.data))
        self2.pub2.publish(msg2)

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