#!/usr/bin/env python3
import threading
import time
import ast
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from math import sqrt, atan2, pi
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import ParameterDescriptor

class TurtleBot(Node):
    def __init__(self):
        super().__init__("turtlesim_goal")

        self.velocity_publisher = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)

        self.pose_subscriber = self.create_subscription(
            Pose, "/turtle1/pose", self.update_pose, 10
        )

        # Movement parameters
        self.max_linear_speed = 1.5
        self.min_linear_speed = 0.3
        self.angular_speed_factor = 2.0

        # Setup control timer (10Hz)
        self.timer = self.create_timer(0.1, self.controller_callback)

        # Setup turtle state
        self.pose = Pose()
        self.goal_pose = Pose()
        self.moving_to_goal = False
        self.distance_tolerance = 0.1

        # For position logging
        self.last_log_time = 0.0

           # Waypoints parameter
        self.declare_parameter(
            "waypoints",
            [],
            ParameterDescriptor(dynamic_typing=True)
        )
        waypoint_value = self.get_parameter("waypoints").value
        self.get_logger().info(f"Raw waypoints parameter: {waypoint_value}")

        self.waypoints = []

        try:
            if isinstance(waypoint_value, str):
                waypoint_value = ast.literal_eval(waypoint_value)

            if isinstance(waypoint_value, list):
                # Fall 1: platt lista, t.ex. [1.0, 2.0, 3.0, 4.0]
                if all(isinstance(v, (int, float)) for v in waypoint_value):
                    if len(waypoint_value) % 2 != 0:
                        self.get_logger().error("Waypoints must contain an even number of values")
                    else:
                        for i in range(0, len(waypoint_value), 2):
                            self.waypoints.append([float(waypoint_value[i]), float(waypoint_value[i + 1])])

                # Fall 2: redan lista av listor, t.ex. [[1.0, 2.0], [3.0, 4.0]]
                elif all(isinstance(v, list) and len(v) == 2 for v in waypoint_value):
                    self.waypoints = [[float(v[0]), float(v[1])] for v in waypoint_value]

        except Exception as e:
            self.get_logger().error(f"Failed to parse waypoints: {e}")
            self.waypoints = []

        self.current_waypoint_index = 0

    def update_pose(self, data):
        """Store the turtle's current position"""
        self.pose = data

    def euclidean_distance(self):
        """Distance between current position and goal"""
        return sqrt(
            (self.goal_pose.x - self.pose.x) ** 2
            + (self.goal_pose.y - self.pose.y) ** 2
        )

    def calculate_linear_velocity(self):
        """Calculate forward speed with deceleration near goal"""
        distance = self.euclidean_distance()

        decel_zone = self.distance_tolerance * 2.0

        if distance < decel_zone:
            speed = self.min_linear_speed + (
                self.max_linear_speed - self.min_linear_speed
            ) * (distance / decel_zone)
        else:
            speed = self.max_linear_speed

        return max(self.min_linear_speed, min(speed, self.max_linear_speed))

    def calculate_steering_angle(self):
        """Angle toward goal"""
        return atan2(self.goal_pose.y - self.pose.y, self.goal_pose.x - self.pose.x)

    def calculate_angular_velocity(self):
        """Calculate rotational speed for steering"""
        angle_diff = self.calculate_steering_angle() - self.pose.theta

        while angle_diff > pi:
            angle_diff -= 2 * pi
        while angle_diff < -pi:
            angle_diff += 2 * pi

        if abs(angle_diff) < 0.1:
            return angle_diff * self.angular_speed_factor * 0.8
        elif abs(angle_diff) < 0.5:
            return angle_diff * self.angular_speed_factor
        else:
            return angle_diff * self.angular_speed_factor * 1.2

    def set_next_waypoint(self):
        """Set next waypoint as current goal"""
        if self.current_waypoint_index < len(self.waypoints):
            waypoint = self.waypoints[self.current_waypoint_index]
            self.goal_pose.x = float(waypoint[0])
            self.goal_pose.y = float(waypoint[1])
            self.moving_to_goal = True
            self.get_logger().info(
                f"Moving to waypoint {self.current_waypoint_index + 1}: x={self.goal_pose.x}, y={self.goal_pose.y}"
            )
            self.current_waypoint_index += 1
        else:
            self.get_logger().info("All waypoints completed.")
            self.moving_to_goal = False

    def controller_callback(self):
        """Main control loop - called 10 times per second"""
        if not self.moving_to_goal:
            return

        current_time = time.time()
        if current_time - self.last_log_time >= 1.0:
            self.get_logger().info(
                f"Current position: x={self.pose.x:.2f}, y={self.pose.y:.2f}, distance_to_goal={self.euclidean_distance():.2f}"
            )
            self.last_log_time = current_time

        if self.euclidean_distance() < self.distance_tolerance:
            vel_msg = Twist()
            self.velocity_publisher.publish(vel_msg)

            self.get_logger().info("Goal reached!")

            if self.current_waypoint_index < len(self.waypoints):
                self.set_next_waypoint()
            else:
                self.moving_to_goal = False

            return

        vel_msg = Twist()

        linear_velocity = self.calculate_linear_velocity()

        angular_diff = abs(self.calculate_steering_angle() - self.pose.theta)
        while angular_diff > pi:
            angular_diff = abs(angular_diff - 2 * pi)

        turn_factor = 1.0
        if angular_diff > 0.5:
            turn_factor = max(0.4, 1.0 - angular_diff / pi)

        vel_msg.linear.x = linear_velocity * turn_factor
        vel_msg.angular.z = self.calculate_angular_velocity()

        self.velocity_publisher.publish(vel_msg)


def main():
    rclpy.init()
    turtlebot = TurtleBot()

    spin_thread = threading.Thread(target=rclpy.spin, args=(turtlebot,))
    spin_thread.daemon = True
    spin_thread.start()

    try:
        # If waypoints were sent as parameter, run them automatically
        if len(turtlebot.waypoints) > 0:
            turtlebot.set_next_waypoint()

            while rclpy.ok() and (
                turtlebot.moving_to_goal
                or turtlebot.current_waypoint_index < len(turtlebot.waypoints)
            ):
                time.sleep(200.5)

        else:
            while True:
                choice = input("\n1. Go to position, 2. Exit: ")

                if choice == "1":
                    try:
                        ansX = 0
                        while(ansX != 1):
                            x = float(input("X (0-11): "))
                            if 11 < x:
                                print("För stort tal prova igen:")
                            elif 0 > x:
                                print("För litet tal prova igen:")
                            else:
                                ansX = 1

                        ansY = 0
                        while(ansY != 1):
                            y = float(input("Y (0-11): "))
                            if 11 < y:
                                print("För stort tal prova igen:")
                            elif 0 > y:
                                print("För litet tal prova igen:")
                            else:
                                ansY = 1

                        turtlebot.get_logger().info(f"Moving to: x={x}, y={y}")
                        turtlebot.goal_pose.x = x
                        turtlebot.goal_pose.y = y
                        turtlebot.moving_to_goal = True

                        while turtlebot.moving_to_goal:
                            time.sleep(200.5)

                    except ValueError:
                        print("Please enter valid numbers")

                elif choice == "2":
                    break

                else:
                    print("Invalid choice")

    except KeyboardInterrupt:
        pass

    finally:
        turtlebot.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()