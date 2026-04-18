import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)

        self.camera_device = self.get_parameter('camera_device').value
        self.frame_width = self.get_parameter('frame_width').value
        self.frame_height = self.get_parameter('frame_height').value

        self.publisher = self.create_publisher(Image, '/image_raw', 10)
        self.bridge = CvBridge()

        self.cap = None
        self.init_camera()

        self.timer = self.create_timer(0.05, self.publish_frame)  # 20 Hz
        self.get_logger().info('Camera node ready - publishing on /image_raw ...')

    def init_camera(self):
        self.get_logger().info("Initializing camera...")

        self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            self.get_logger().error("Failed to open camera")
            return

        # config
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # warmup (IMPORTANT)
        for _ in range(10):
            self.cap.read()
            time.sleep(0.05)

    def reconnect_camera(self):
        self.get_logger().warn("Reconnecting camera...")
        if self.cap:
            self.cap.release()
        time.sleep(1.0)
        self.init_camera()

    def publish_frame(self):
        if self.cap is None or not self.cap.isOpened():
            self.reconnect_camera()
            return

        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warn("No frame → retry")
            self.reconnect_camera()
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    rclpy.spin(node)

    if node.cap:
        node.cap.release()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()