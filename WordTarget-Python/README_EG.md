# 🔫 WordTarget-Python - Word Shooting Game

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Pygame)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](README_EG.md) | [中文](README.md)

From Bluetooth light gun to word shooting — aim, shoot, and learn words with a real "gun"

## 🔥 Updates

- [x] 2026.5.14 First full release, supports Classic Mode (EN→CN / CN→EN / Listening) and Scene Mode.
- [x] 2026.5.13 Scene Mode implemented — select word cards by clicking specific positions on background images.
- [x] 2026.5.4 Core gameplay of Classic Mode completed, featuring dynamic card layout and real-time score feedback.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Installation & Dependencies](#️-installation--dependencies)
- [🎮 Quick Start](#-quick-start)
- [🔧 Configuration & Word Banks](#-configuration--word-banks)
- [📖 Gameplay](#-gameplay)
- [⌨️ Controls](#️-controls)
- [🔮 Creating Scene Mode](#-creating-scene-mode)
- [📝 Acknowledgements & License](#-acknowledgements--license)

## ✨ Features

- **Three Classic Game Modes**: English→Chinese, Chinese→English, and Listening. The Listening mode automatically reads words aloud to train listening comprehension.
- **Scene Mode**: Load custom scene images (e.g., bedroom, classroom) — word cards randomly appear at annotated positions on the image, enhancing immersion.
- **Native System Voice**: Uses SAPI or PowerShell fallback on Windows, `say` on macOS, and `espeak`/`festival` on Linux — no external API required.
- **Mouse / Light Gun Control**: Supports clicking answers with the mouse, and can be paired with the AirGun Bluetooth light gun to aim and shoot words with the cursor.
- **Dynamic Card Layout**: Each round randomly generates 5 options. Card positions automatically avoid overlaps, with intelligent truncation for long text.
- **Real-time Feedback & Scoring**: Correct answers flash green and award +10 points; wrong answers flash red. The game automatically proceeds to the next question.
- **Adjustable Sensitivity & Window**: Mouse sensitivity (10–50), window sizes (800x600 / 1024x768 / 1280x720), and fullscreen toggle.
- **Pause & Settings Menu**: Press ESC in-game to pause, adjust sensitivity, window size, or fullscreen, then continue or exit.

## 🛠️ Installation & Dependencies

### Requirements

- Python 3.7 or higher
- Operating system: Windows / macOS / Linux (voice features are natively supported on each platform)

### Installing Dependencies

<p>Create a virtual environment using conda:</p>

```bash
conda create -n word_hunt python=3.9 -y
conda activate word_hunt
```

<p>After switching to the created conda environment, simply install dependencies via pip:</p>

```bash
pip install requirements.txt
```

If pywin32 is not installed, the program will automatically use a PowerShell fallback.

### Running from Source

Place `wordhunt.py` and `scene_game.py` in the same directory, and create the `resource/` folder structure (see configuration instructions below).

```bash
python -m wordhunt
python wordhunt.py
```

## 🎮 Quick Start

1. **Run the game**: Execute `python wordhunt.py` to enter the main menu.
2. **Choose a mode**:
   - **Classic Mode**: Select a word bank (e.g., CET-4, Elementary English), game mode (EN→CN / CN→EN / Listening), game duration (30–180 seconds), and mouse sensitivity.
   - **Scene Mode**: Choose a preset scene (e.g., bathroom, classroom) — word cards will appear at annotated positions on the scene image.
3. **Start the game**: Click "Start Game", aim at a word card with the mouse or light gun, and click the left button.
4. **Score & continue**: Each correct answer gives 10 points; wrong answers do not deduct points. The question automatically refreshes.
5. **End**: When time runs out, the final score is displayed, and you can choose "Play Again" or "Return to Main Menu".

## 🔧 Configuration & Word Banks

### Word Bank Format (JSON)

Word banks are stored in the `resource/` directory, each as a `.json` file. Two formats are supported:

**Format 1 (recommended, with Chinese and pronunciation)**:
```json
{
  "name": "CET-4",
  "1": {
    "english": "abandon",
    "chinese_trans": "v. 遗弃；放弃",
    "spell": "[əˈbændən]"
  },
  "2": {
    "english": "absence",
    "chinese_trans": "n. 缺席；缺乏",
    "spell": "[ˈæbsəns]"
  }
}
```

**Format 2 (word list only)**:
```json
["apple", "banana", "orange"]
```

If a word bank has fewer than 5 entries, the game will automatically repeat entries to ensure enough options.

### Scene Mode Configuration

Scene files are located in `resource/scene/`, and images are in `resource/scene_img/`. The scene JSON format:

```json
{
  "image_path": "scene_img/bathroom.jpg",
  "annotations": {
    "soap": {
      "chinese": "肥皂",
      "pos": [[120, 300], [130, 310]]
    },
    "mirror": {
      "chinese": "镜子",
      "pos": [[400, 150], [410, 160]]
    }
  }
}
```

- `image_path`: The image file name (relative to `resource/scene_img/`).
- `annotations`: Each word corresponds to an object; `chinese` is the Chinese translation, and `pos` is one or more coordinates `(x, y)`. The game will randomly choose a coordinate to place the card.

When the program runs for the first time, if the `resource/` directory does not exist, default "CET-4" and "Elementary English" word bank samples will be automatically generated. Scene files must be created manually.

## 📖 Gameplay

### Classic Mode

- **English→Chinese**: An English word is shown in the center of the screen. Chinese translations appear on cards around it. Select the correct Chinese.
- **Chinese→English**: A Chinese word is shown. Select the corresponding English word.
- **Listening**: The system reads an English word aloud, and the screen displays "Listen and choose". Select the correct spelling from the cards. The voice plays automatically; a repeat button is not implemented, but each new question automatically reads the word once.

### Scene Mode

- The background is a real scene image (e.g., bathroom, classroom). Word cards appear as semi-transparent rounded rectangles near annotated positions on the image.
- The English word to shoot (e.g., `soap`) is displayed at the top of the screen. The player must click the card labeled with its Chinese translation (e.g., "肥皂").
- Card positions are determined by the `pos` coordinates in the JSON, and the system automatically maps them according to screen scaling.
- This mode is especially suitable for pairing with a light gun: aim at the object in the image (e.g., soap) and pull the trigger to hit the corresponding card.

## ⌨️ Controls

| Action                                 | Key / Action                      |
| -------------------------------------- | --------------------------------- |
| Select an option (shoot)               | Mouse left button / light gun left button |
| Pause/Resume game (Classic Mode)       | ESC                               |
| Exit Scene Mode                        | ESC (directly returns to main menu) |
| Scroll through scene list (Scene selection) | Mouse wheel                   |
| Adjust sliders / buttons               | Drag or click with mouse           |

The in-game pause menu provides options for "Resume", "Settings", "End Current Game", and "Return to Main Menu". In the settings, you can adjust mouse sensitivity and window size in real time.

## 🔮 Creating Scene Mode

1. Prepare a background image (recommended 1920x1080 or 1280x720) and place it in `resource/scene_img/`.
2. Create a JSON file with the same name (e.g., `bedroom.json`) in `resource/scene/`.
3. Annotate words: Decide which words the player will shoot (e.g., `pillow`), provide the Chinese translation and at least one coordinate (coordinates can be obtained using image editing software to find pixel positions).
4. Launch the game and select "Scene Mode" from the main menu — you will see the new scene.

## 📝 Acknowledgements & License

- Game engine: [Pygame](https://www.pygame.org/) and [Pygame-Menu](https://pygame-menu.readthedocs.io/)
- Voice solutions: Windows SAPI, macOS `say`, Linux `espeak`/`festival` open-source tools
- Font support: Prioritizes system‑provided Chinese fonts (Microsoft YaHei, Source Han Sans, etc.) to ensure proper Chinese display.

This project is for learning and communication purposes only. The code is released under the MIT license. You are welcome to extend the word banks, scenes, or add online multiplayer features.