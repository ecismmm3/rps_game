from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'rps_game'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    ('share/' + package_name + '/launch', [
        'launch/game.launch.py',
    ]),
    ('share/' + package_name + '/urdf', ['urdf/rps_robot.urdf']),
    ('share/' + package_name + '/config', ['config/controllers.yaml', 'config/rviz_config.rviz',]),
    (os.path.join('lib', 'python3.10', 'site-packages', package_name),
        ['rps_game/model.pth']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ecism',
    maintainer_email='ecism@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': ['gesture_node = rps_game.gesture_node:main',
        'game_logic_node = rps_game.game_logic_node:main',
        'robot_controller_node = rps_game.robot_controller_node:main',
        ],
    },
)
