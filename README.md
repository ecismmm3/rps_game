# Gesture-Driven Human-Robot Interaction Framework

An interactive Rock-Paper-Scissors game using ROS2 where a computer vision model classifies user hand gestures in real time and a simulated robot arm responds with randomized moves.

## Overview

Built to learn the fundamentals of robotics in ROS2, computer vision, and machine learning-based classification. An OpenCV script reads webcam input frame by frame, runs each frame through a PyTorch EfficientNet-B0 model trained on 600+ images to classify rock, paper, or scissors, and writes the result to a shared communications file. On the ROS2 side, a 5-node pipeline reads the classification, runs automated game rounds with a countdown sequence, and drives a custom URDF robot arm in RViz2 to display the computer's randomized move.

## Tech Stack

ROS2 • RViz2 • PyTorch • OpenCV • Python • URDF

## How It Works

- OpenCV script reads and processes webcam input frame by frame
- Frames are run through a PyTorch EfficientNet-B0 model trained on 600+ images to classify rock, paper, or scissors
- Classification is written to a shared communications file bridging Windows and WSL2
- A custom URDF robot arm simulated in RViz2 runs automated rounds, displaying rock, paper, or scissors at random via procedural joint animation
- Game result is computed from the randomized computer choice and your detected pose

## Challenges

- Tuned the model multiple times to achieve consistent accuracy — adjusted lighting, backgrounds, learning rate, and epoch count, and addressed overfitting
- Webcam passthrough was inaccessible in WSL2 via usbipd; pivoted to a shared file bridge between the Windows inference script and the ROS2 gesture node

## Requirements

### Windows side
- Python 3.8+
- `pip install torch torchvision timm opencv-python Pillow numpy matplotlib tqdm`

### WSL2 / ROS2 side
- Ubuntu 22.04
- ROS2 Humble
- WSLg (built into recent Windows 11 builds) for RViz2 display
- `pip install timm`

## Setup

### 1. Train your model (Windows)
- Instructions in windows/train_val.py
- Note the class order printed at the end and update `CLASS_NAMES` in `gesture_detection.py` to match.

### 2. Configure the file bridge

In `windows/gesture_detection.py`, update `GESTURE_FILE` to a path on your Windows machine:

```python
GESTURE_FILE = r"C:\Users\YourName\gesture.txt"
```

In `rps_game/gesture_node.py`, update `self.gesture_file` to the same path in WSL2 format:

```python
self.gesture_file = '/mnt/c/Users/YourName/gesture.txt'
```

### 3. Build the ROS2 package (WSL2)

```bash
cd ~/ros2_ws
colcon build --packages-select rps_game
source install/setup.bash
```

### 4. Run

Start the gesture detection script on Windows: gesture_detection.py

Launch the ROS2 pipeline in WSL2:

```bash
ros2 launch rps_game game.launch.py
```

RViz2 will open automatically with the robot configured. The game runs automatically — hold up rock, paper, or scissors and watch the robot respond.









































