import time

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('frame_id', 'camera_frame')
        self.declare_parameter('startup_warmup_frames', 10)
        self.declare_parameter('reconnect_interval', 1.0)

        self.camera_device = self.get_parameter('camera_device').value
        self.frame_width = self.get_parameter('frame_width').value
        self.frame_height = self.get_parameter('frame_height').value
        self.frame_id = self.get_parameter('frame_id').value
        self.startup_warmup_frames = int(
            self.get_parameter('startup_warmup_frames').value
        )
        self.reconnect_interval = float(
            self.get_parameter('reconnect_interval').value
        )

        self.publisher = self.create_publisher(Image, '/image_raw', 10)
        self.bridge = CvBridge()

        self.cap = None
        self.camera_ready = False
        self.warmup_frames_remaining = 0
        self.last_reconnect_attempt = 0.0
        self.init_camera()

        self.timer = self.create_timer(0.05, self.publish_frame)  # 20 Hz
        self.get_logger().info('Camera node ready - publishing on /image_raw ...')

    def init_camera(self):
        self.get_logger().info('Initializing camera...')

        self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open camera {self.camera_device}')
            self.camera_ready = False
            return

        # config
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.camera_ready = True
        self.warmup_frames_remaining = max(0, self.startup_warmup_frames)

    def close_camera(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = None
        self.camera_ready = False

    def reconnect_camera(self):
        self.get_logger().warn('Reconnecting camera...')
        self.close_camera()
        self.init_camera()

    def publish_frame(self):
        now = time.monotonic()
        if self.cap is None or not self.cap.isOpened():
            if now - self.last_reconnect_attempt >= self.reconnect_interval:
                self.last_reconnect_attempt = now
                self.reconnect_camera()
            return

        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warn('No frame, camera will be reopened')
            self.close_camera()
            return

        if self.warmup_frames_remaining > 0:
            self.warmup_frames_remaining -= 1
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        self.publisher.publish(msg)

    def destroy_node(self):
        self.close_camera()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
