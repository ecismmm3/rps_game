# DATASET SETUP:
#
# dataset/
# ├── train/
# │   ├── paper/
# │   │   ├── 0.jpg
# │   │   └── ...
# │   ├── rock/
# │   │   └── ...
# │   └── scissors/
# │       └── ...
# └── val/
#     ├── paper/
#     ├── rock/
#     └── scissors/
#
# Folder names become class labels. ImageFolder sorts alphabetically:
#   0 = paper, 1 = rock, 2 = scissors
#
# What I Used: 80% train / 20% val, 250+ images per class.
#
# OUTPUT:
#   rps_model.pth       — saved model weights (uses best val accuracy)
#   loss_curve.png      — training vs validation loss plot
#   accuracy_curve.png  — training vs validation accuracy plot
# -----------------------------------------------------------------

import torch # pytorch, tensors = arrays
import torch.nn as nn # neural network module, contains layers and loss functions
import torch.optim as optim # optimization algorithms, contains optimizers like SGD, Adam, etc.
from torch.utils.data import Dataset, DataLoader # creating datasets and dataloaders
import torchvision.transforms as transforms # image transformations
from torchvision.datasets import ImageFolder # loads images from folders
import timm # library for pre-trained models
from PIL import Image

import matplotlib.pyplot as plt # for plotting
import numpy as np # calculations
from tqdm import tqdm # progress bar for loops

# -----------------------------------------------
# CONFIGURATION — edit these
# -----------------------------------------------

TRAIN_DIR     = "dataset/train"   # path to training images
VAL_DIR       = "dataset/val"     # path to validation images
NUM_CLASSES   = 3                 # rock, paper, scissors
BATCH_SIZE    = 32
NUM_EPOCHS    = 10
LEARNING_RATE = 0.0001
SAVE_PATH     = "rps_model.pth"   # where to save the best model

# -----------------------------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class RockPaperScissorsDataSet(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data = ImageFolder(data_dir, transform=transform)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

    @property
    def classes(self):
        return self.data.classes

train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15), 
    transforms.ColorJitter( 
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


class RockPaperScissorsModel(nn.Module):
    def __init__(self, num_classes=3):
        super(RockPaperScissorsModel, self).__init__()

        self.base_model = timm.create_model(
            "efficientnet_b0",
            pretrained=True,
            num_classes=0
        ) 

        enet_out_size = self.base_model.num_features 
        self.classifier = nn.Linear(enet_out_size, num_classes)

    def forward(self, x):
        x = self.base_model(x)
        output = self.classifier(x)
        return output


if __name__ == '__main__':

    train_dataset = RockPaperScissorsDataSet(data_dir=TRAIN_DIR, transform=train_transform)
    val_dataset   = RockPaperScissorsDataSet(data_dir=VAL_DIR,   transform=val_transform)

    print(f"Classes: {train_dataset.classes}")
    print(f"Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False)

    model = RockPaperScissorsModel(num_classes=NUM_CLASSES).to(device)

    criterion = nn.CrossEntropyLoss() 
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    train_losses, val_losses = [], []
    train_accuracies, val_accuracies = [], []
    best_val_accuracy = 0

    #TRAINING -----------------------------------------------------------------------------------------------------
    for epoch in range(NUM_EPOCHS):
        model.train()
        running_loss = 0.0 

        correct = 0
        total = 0

        loop = tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Train]")

        for images, labels in loop:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad() 
            outputs = model(images) 
            loss = criterion(outputs, labels) 
            loss.backward() 
            optimizer.step() 

            running_loss += loss.item() * images.size(0) 
            loop.set_postfix(loss=loss.item())

            predictions = outputs.argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

        train_loss = running_loss / len(train_loader.dataset)
        train_losses.append(train_loss)

        train_accuracy = correct / total
        train_accuracies.append(train_accuracy)

    #VALIDATION -----------------------------------------------------------------------------------------------------

        model.eval() 
        running_loss = 0.0

        correct = 0
        total = 0

        loop = tqdm(val_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Val]")

        with torch.no_grad(): 
            for images, labels in loop:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images) 

                predictions = outputs.argmax(dim=1)
                correct += (predictions == labels).sum().item()
                total += labels.size(0)

                loss = criterion(outputs, labels) 
                running_loss += loss.item() * images.size(0) 

                loop.set_postfix(loss=loss.item())

        val_loss = running_loss / len(val_loader.dataset) 
        val_losses.append(val_loss)

        val_accuracy = correct / total
        val_accuracies.append(val_accuracy)

        print(
            f"Epoch {epoch+1}/{NUM_EPOCHS} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Train Acc: {train_accuracy:.2%} | "
            f"Val Acc: {val_accuracy:.2%}"
        )

        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(model.state_dict(), SAVE_PATH)
            print(f"Saved best model → val accuracy: {val_accuracy:.2%}")

    print(f"\nTraining complete. Best val accuracy: {best_val_accuracy:.2%}")
    print(f"Model saved to: {SAVE_PATH}")
    print(f"\nClass order: {train_dataset.classes}")
    print("Update CLASS_NAMES in gesture_detection.py to match this order exactly.")

    plt.figure(figsize=(8, 5))
    plt.plot(train_losses, label="Training Loss")
    plt.plot(val_losses, label="Validation Loss")
    plt.legend()
    plt.title("Loss over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.savefig("loss_curve.png", dpi=300, bbox_inches="tight")
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(train_accuracies, label="Training Accuracy")
    plt.plot(val_accuracies, label="Validation Accuracy")
    plt.legend()
    plt.title("Accuracy over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.savefig("accuracy_curve.png", dpi=300, bbox_inches="tight")
    plt.show()