import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480) 

        camera_device = self.get_parameter('camera_device').value
        frame_width = self.get_parameter('frame_width').value
        frame_height = self.get_parameter('frame_height').value

        self.publisher = self.create_publisher(Image, '/image_raw', 10)
        self.bridge = CvBridge()

        # IMPORTANT : utiliser V4L2
        self.cap = cv2.VideoCapture(camera_device, cv2.CAP_V4L2)

        # Config caméra
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        self.timer = self.create_timer(0.03, self.publish_frame)
        self.get_logger().info('Camera node ready - publishing on /image_raw ...')

    def publish_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warn("No frame")
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    rclpy.spin(node)

    node.cap.release()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()