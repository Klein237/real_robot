#!/usr/bin/env python3
"""ROS2 to Arduino serial bridge.

Subscribes to `/cmd_vel` and sends bounded motor commands over USB serial.
"""
import sys

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
import serial

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200


class SerialBridge(Node):
    def __init__(self):
        super().__init__('serial_bridge')

        # Déclarer les paramètres avec leurs valeurs par défaut
        self.declare_parameter('serial_port', SERIAL_PORT)
        self.declare_parameter('baud_rate', BAUD_RATE)
        self.declare_parameter('command_timeout', 0.5)
        self.declare_parameter('reconnect_period', 1.0)

        # Lire les valeurs (depuis la ligne de commande ou les défauts)
        self.port = self.get_parameter('serial_port').value
        self.baud = self.get_parameter('baud_rate').value
        self.command_timeout = float(self.get_parameter('command_timeout').value)
        self.reconnect_period = float(self.get_parameter('reconnect_period').value)
        self.last_command_time = self.get_clock().now()
        self.last_packet = 'L:0,R:0\n'
        self.ser = None

        if not self.connect_serial():
            self.get_logger().warn(
                f'Starting without serial link, retrying every {self.reconnect_period:.1f}s'
            )

        # S'abonner aux commandes de vitesse
        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10,
        )
        self.watchdog_timer = self.create_timer(0.1, self.safety_check)
        self.reconnect_timer = self.create_timer(
            self.reconnect_period,
            self.reconnect_if_needed,
        )
        self.get_logger().info('Serial bridge ready - waiting for /cmd_vel ...')

    def connect_serial(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1, write_timeout=1)
            self.get_logger().info(f'Connected to Arduino on {self.port}')
            self.send_packet(self.last_packet, log_debug=False)
            return True
        except serial.SerialException as exc:
            self.ser = None
            self.get_logger().error(f'Cannot open serial port {self.port}: {exc}')
            return False

    def is_serial_ready(self):
        return self.ser is not None and self.ser.is_open

    def send_packet(self, packet, log_debug=True):
        if not self.is_serial_ready():
            self.get_logger().warn('Serial link unavailable, command dropped')
            return False

        try:
            self.ser.write(packet.encode())
            self.ser.flush()
            self.last_packet = packet
            if log_debug:
                self.get_logger().debug(f'Sent: {packet.strip()}')
            return True
        except serial.SerialException as exc:
            self.get_logger().error(f'Serial write failed: {exc}')
            self.handle_serial_failure()
            return False

    def handle_serial_failure(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except serial.SerialException:
                pass
        self.ser = None

    def reconnect_if_needed(self):
        if not self.is_serial_ready():
            self.connect_serial()

    def cmd_vel_callback(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z

        # Mixer linéaire + angulaire en vitesses roue gauche/droite
        left = int(max(-255, min(255, (linear + angular) * 255)))
        right = int(max(-255, min(255, (linear - angular) * 255)))

        packet = f'L:{left},R:{right}\n'
        if self.send_packet(packet):
            self.last_command_time = self.get_clock().now()

    def safety_check(self):
        elapsed = (
            self.get_clock().now() - self.last_command_time
        ).nanoseconds / 1e9
        if elapsed < self.command_timeout:
            return

        if self.last_packet != 'L:0,R:0\n':
            if self.send_packet('L:0,R:0\n', log_debug=False):
                self.get_logger().warn(
                    f'No /cmd_vel for {elapsed:.2f}s, motors forced to stop'
                )

    def destroy_node(self):
        # Arrêter les moteurs à l'extinction du nœud
        self.send_packet('L:0,R:0\n', log_debug=False)
        if self.ser is not None:
            try:
                self.ser.close()
            except serial.SerialException:
                pass
        super().destroy_node()


def main():
    rclpy.init()
    node = SerialBridge()
    if not rclpy.ok():
        sys.exit(1)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
