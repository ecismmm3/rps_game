import os 
from launch import LaunchDescription # everything you want to launch
from launch_ros.actions import Node # tells ROS to start a specific node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description(): # must have this specific name
    
    # reads URDF file:
    pkg_share = get_package_share_directory('rps_game')
    urdf_file = os.path.join(pkg_share, 'urdf', 'rps_robot.urdf')

    return LaunchDescription([

        Node( # publishes URDF to /robot_description, calculates and publishes position of all links to /tf
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': open(urdf_file).read(),
            }]
        ),

        Node( # visualizes robot model using /tf
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(pkg_share, 'config', 'rviz_config.rviz')]
        ),

        Node( # reads /robot_choice, publishes /joint_states to move robot
            package='rps_game',
            executable='robot_controller_node',
            name='robot_controller_node',
            output='screen'
        ),

        Node(
            package='rps_game', 
            executable='gesture_node', # node to run
            name='gesture_node', # name of instance
            output='screen'
        ),

        Node(
            package='rps_game',
            executable='game_logic_node',
            name='game_logic_node',
            output='screen'
        ),
    ])

# WORKFLOW:

# game.launch.py starts RViz2
#     → robot_state_publisher reads URDF, publishes /robot_description
#     → robot_state_publisher listens to /joint_states, publishes /tf
#     → robot_controller_node subscribes to /robot_choice
#     → robot_controller_node publishes joint positions to /joint_states
#     → RViz2 reads /tf and draws the robot moving