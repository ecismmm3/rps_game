# ---------------------------------------------------------------
# BEFORE RUNNING:
# 1. Train your model using train.py
# 2. Update MODEL_PATH to point to your trained .pth file.
# 3. Update CLASS_NAMES to match the class order
# 4. Update GESTURE_FILE to a path you create on your Windows machine.
#    In WSL2 this same path will appear as: /mnt/c/Users/<you>/gesture.txt
#    Update gesture_node.py in the ROS2 package to match this path.
#
# CONTROLS:
#   SPACE — start rock/paper/scissors/shoot countdown
#   Q     — quit
# ---------------------------------------------------------------

import torch
import torch.nn as nn
import torchvision.transforms as transforms
import timmz
from PIL import Image
import cv2 as cv

import random
import time
import numpy as np


# -----------------------------------------------
# CONFIGURATION — edit these to match your setup
# -----------------------------------------------

MODEL_PATH   = "rps_model.pth"
GESTURE_FILE = r"C:\Users\YourName\gesture.txt"  # in WSL2: /mnt/c/Users/YourName/gesture.txt
                                                  # update gesture_node.py to match

CLASS_NAMES = ['paper', 'rock', 'scissors']

# -----------------------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class RockPaperScissorsModel(nn.Module):
    def __init__(self, num_classes=3):
        super(RockPaperScissorsModel, self).__init__()

        self.base_model = timm.create_model(
            "efficientnet_b0",
            pretrained=False,
            num_classes=0
        )

        enet_out_size = self.base_model.num_features
        self.classifier = nn.Linear(enet_out_size, num_classes)

    def forward(self, x):
        x = self.base_model(x)
        output = self.classifier(x)
        return output


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def preprocess_image(frame, transform):
    if isinstance(frame, str):
        frame = cv.imread(frame)

    image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image_tensor = transform(image).unsqueeze(0)

    return image, image_tensor


def predict(model, image_tensor, device):
    model.eval()
    with torch.no_grad():
        image_tensor = image_tensor.to(device)
        output = model(image_tensor)
        probabilities = torch.nn.functional.softmax(output, dim=1)
    return probabilities.squeeze(0).cpu().numpy()


if __name__ == '__main__':

    model = RockPaperScissorsModel(num_classes=len(CLASS_NAMES)).to(device)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    vid = cv.VideoCapture(0, cv.CAP_DSHOW)
    vid.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    vid.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    vid.set(cv.CAP_PROP_FPS, 30)

    player_score = 0
    computer_score = 0
    computer_move = ""
    player_move = ""
    result = "Press SPACE to start"
    countdown_active = False
    countdown_start = 0

    while True:
        isTrue, frame = vid.read()

        if not isTrue or frame is None:
            continue

        original_image, image_tensor = preprocess_image(frame, transform)
        probabilities = predict(model, image_tensor, device)

        prediction_idx = np.argmax(probabilities)
        prediction = CLASS_NAMES[prediction_idx]

        with open(GESTURE_FILE, "w") as f:
            f.write(prediction)

        current_time = time.time()
        countdown_text = ""

        if countdown_active:
            elapsed = current_time - countdown_start

            if elapsed < 1:
                countdown_text = "ROCK"
            elif elapsed < 2:
                countdown_text = "PAPER"
            elif elapsed < 3:
                countdown_text = "SCISSORS"
            elif elapsed < 4:
                countdown_text = "SHOOT!"
            else:
                countdown_active = False
                player_move = prediction
                computer_move = random.choice(CLASS_NAMES)

                if player_move == computer_move:
                    result = "Tie"
                elif (
                    (player_move == "rock" and computer_move == "scissors") or
                    (player_move == "paper" and computer_move == "rock") or
                    (player_move == "scissors" and computer_move == "paper")
                ):
                    result = "You Win"
                    player_score += 1
                else:
                    result = "Computer Wins"
                    computer_score += 1

        cv.putText(frame, f"{prediction}", (20, 40),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv.putText(frame, f"Computer Move: {computer_move}", (20, 380),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv.putText(frame, f"{result}", (20, 420),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv.putText(frame, f"You {player_score} - {computer_score} Computer", (20, 460),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

        if countdown_text:
            (tw, th), _ = cv.getTextSize(countdown_text, cv.FONT_HERSHEY_SIMPLEX, 2, 4)
            cx = (frame.shape[1] - tw) // 2
            cy = frame.shape[0] // 2
            cv.putText(frame, countdown_text, (cx, cy),
                       cv.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

        prob_text = (
            f"P:{probabilities[0]:.2f} "
            f"R:{probabilities[1]:.2f} "
            f"S:{probabilities[2]:.2f}"
        )
        (text_w, text_h), _ = cv.getTextSize(prob_text, cv.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        x = frame.shape[1] - text_w - 10
        y = frame.shape[0] - 10
        cv.putText(frame, prob_text, (x, y),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv.imshow("Rock Paper Scissors", frame)

        key = cv.waitKey(1) & 0xFF

        if key == ord(' '):
            if not countdown_active:
                countdown_active = True
                countdown_start = time.time()
        elif key == ord('q'):
            break

    vid.release()
    cv.destroyAllWindows()