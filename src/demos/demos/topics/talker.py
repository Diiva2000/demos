#! /usr/bin/env python3
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32
import random 


class Talker(Node):
    def __init__(self):
        super().__init__("talker")
        self.i = 0
        self.pub = self.create_publisher(Int32, "chatter", 10)
        timer_period = 1.0
        self.tmr = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self): 

        msg = Int32()
        self.i = random.randint(1, 100)
        msg.data = self.i
    
        
        self.get_logger().info(f'Publishing: {format(msg.data)}')
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = Talker()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
