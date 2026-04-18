# launch/robot.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
 
    enable_camera_arg = DeclareLaunchArgument(
        'enable_camera',
        default_value='true',
        description='Lancer le nœud caméra (true/false)',
    )

    enable_serial_arg = DeclareLaunchArgument(
        'enable_serial',
        default_value='true',
        description='Lancer le nœud série (true/false)',
    )

    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyACM0',
        description='Port série de l\'Arduino',
    )

    baud_rate_arg = DeclareLaunchArgument(
        'baud_rate',
        default_value='115200',
        description='Baud rate de la liaison série',
    )

    camera_device = DeclareLaunchArgument(
        'camera_device',
        default_value='/dev/video0',
        description='camera device',
    )

     
    serial_node = Node(
        package='rpi_pkg',
        executable='serial_node',
        name='serial_node',
        output='screen',
        parameters=[{
            'serial_port': LaunchConfiguration('serial_port'),
            'baud_rate':   LaunchConfiguration('baud_rate'),
        }],
        condition=IfCondition(LaunchConfiguration('enable_serial')),
    )

    camera_node = Node(
        package='rpi_pkg',
        executable='camera_node',
        name='camera_node',
        output='screen',
        parameters=[{
            'camera_device': LaunchConfiguration('camera_device'),
        }],
        condition=IfCondition(LaunchConfiguration('enable_camera')),
    )

    return LaunchDescription([
        enable_camera_arg,
        enable_serial_arg,
        serial_port_arg,
        baud_rate_arg,
        camera_device,
        serial_node,
        camera_node,
    ])