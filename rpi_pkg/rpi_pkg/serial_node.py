#!/usr/bin/env python3
"""
ROS2 → Arduino Serial Bridge
Subscribes to /cmd_vel (Twist) and sends motor commands over USB serial.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import sys

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE   = 115200


class SerialBridge(Node):
    def __init__(self):
        super().__init__('serial_bridge')

        # Déclarer les paramètres avec leurs valeurs par défaut
        self.declare_parameter('serial_port', SERIAL_PORT)
        self.declare_parameter('baud_rate', BAUD_RATE)

        # Lire les valeurs (depuis la ligne de commande ou les défauts)
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value

        # Ouvrir la connexion série
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.get_logger().info(f'Connected to Arduino on {port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Cannot open serial port: {e}')
            sys.exit(1)

        # S'abonner aux commandes de vitesse
        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
        self.get_logger().info('Serial bridge ready - waiting for /cmd_vel ...')

    def cmd_vel_callback(self, msg):
        linear  = msg.linear.x
        angular = msg.angular.z

        # Mixer linéaire + angulaire en vitesses roue gauche/droite
        left  = int(max(-255, min(255, (linear + angular) * 255)))
        right = int(max(-255, min(255, (linear - angular) * 255)))

        packet = f'L:{left},R:{right}\n'
        self.ser.write(packet.encode())
        self.get_logger().info(f'Sent: {packet.strip()}')

    def destroy_node(self):
        # Arrêter les moteurs à l'extinction du nœud
        self.ser.write(b'L:0,R:0\n')
        self.ser.close()
        super().destroy_node()


def main():
    rclpy.init()
    node = SerialBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()