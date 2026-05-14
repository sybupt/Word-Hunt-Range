# Word-Hunt-Range

![License](https://img.shields.io/badge/License-MIT-green.svg)

[English](README_EG.md) | [中文](README.md)

**Word-Hunt-Range** is a complete word learning ecosystem consisting of three sub-projects: `AirGun`, a Bluetooth motion‑sensing gun hardware driver; `WordTarget`, a cross‑platform game built with the Godot engine; and `WordTarget-Python`, a lightweight game based on Python/Pygame.  
The project aims to make English vocabulary learning lively and efficient through motion‑sensing interaction and fun gameplay.

## 📦 Sub‑projects Overview

| Sub‑project          | Tech Stack          | Role                                           | Core Features                                                                 |
|----------------------|---------------------|------------------------------------------------|--------------------------------------------------------------------------------|
| **AirGun**           | ESP32 / C++         | Bluetooth motion‑sensing gun driver           | Converts physical aiming into mouse cursor movement, supports left‑click shooting |
| **WordTarget**       | Godot 4.6 / GDScript| Cross‑platform word learning game (primary)   | Listening & word selection, scene exploration, lives/timer mode, rich preset word banks and scenes |
| **WordTarget-Python**| Python / Pygame     | Lightweight word shooting game                | EN→CN / CN→EN / listening modes, scene word selection, dynamic card layout, native system voice |

## 🎯 Overall Architecture

```
Word-Hunt-Range
├── AirGun                    # Hardware layer: ESP32 motion‑sensing gun, emulates mouse via BLE HID
├── WordTarget                # Application layer (primary): Godot game, supports Windows/macOS/Linux
└── WordTarget-Python         # Application layer (lightweight): Python game, suitable for quick testing and further development
```

- **AirGun** works with either game: the game recognises shooting via mouse left‑click; AirGun’s movement controls the cursor position and pulling the trigger triggers a left‑click.
- **WordTarget** and **WordTarget-Python** are fully compatible in data format (word bank JSON, scene annotation JSON), and can share learning resources under the `resource/` directory.

## 🔫 Detailed Sub‑project Introduction

### 1. AirGun – ESP32‑based Bluetooth Motion‑Sensing Gun

[![License](https://img.shields.io/badge/License-MIT-green.svg)](AirGun/LICENSE)

From gyroscope to mouse movement — high‑precision, low‑latency wireless motion‑sensing aiming solution.

**Main Features**:
- MPU6050 6‑axis gyroscope with configurable gain, dead zone, and smoothing filter
- Dynamic zero‑drift calibration eliminates temperature drift and accumulated error
- Dual‑core task architecture: 200Hz sampling + independent BLE transmission
- Anti‑accumulation limiting prevents cursor jumps during BLE congestion
- Low‑power design, automatic battery level reporting
- Hardware button debouncing for accurate response

**Hardware Requirements**: ESP32 development board, MPU6050 sensor, momentary switch, single‑cell Li‑ion battery (1.8V~2.5V).

**Software Installation**: Using VSCode + PlatformIO, depend on `ESP32 BLE Mouse`, `MPU6050_light`, `Bounce2` libraries.

> For detailed hardware connections, parameter tuning, and performance notes, see [AirGun/README.md](AirGun/README.md)

### 2. WordTarget – Interactive English Vocabulary Learning Game

[![Godot Version](https://img.shields.io/badge/Godot-4.6+-blue.svg)](https://godotengine.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](WordTarget/LICENSE)

An engaging English vocabulary learning platform built with Godot 4.6, designed for learners at different English proficiency levels.

**Game Modes**:
- **Listening & Word Selection**: Choose the correct word card based on audio
- **Scene Game Mode**: Tap objects in real‑life scene images (bedroom, classroom, hospital, etc.) to learn words

**Learning Content**:
- Word banks: CET-4, CET-6, TEM-4, TEM-8, College Entrance Exam, High School Entrance Exam
- Scene environments: bedroom, classroom, hospital, restaurant, supermarket
- Bilingual support: English word, Chinese translation, pronunciation guide

**Game Mechanics**:
- Score for correct answers, lose lives or time for mistakes
- Dynamic card layout intelligently avoids overlaps
- Optional system text‑to‑speech

**Quick Start**:
1. Install Godot 4.6+
2. Clone the repository and open `project.godot` in Godot
3. Press `F5` to run

> For detailed project structure, content addition, and troubleshooting, see [WordTarget/README.md](WordTarget/README.md)

### 3. WordTarget-Python – Word Shooting Game (Python Implementation)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Pygame)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](WordTarget-Python/LICENSE)

From Bluetooth light gun to word shooting — aim, shoot, and learn words with a real "gun".

**Features**:
- Three classic modes: EN→CN, CN→EN, Listening (auto‑read aloud)
- Scene word selection mode: custom scene images, word cards appear at annotated positions
- Native system voice (Windows SAPI/PowerShell, macOS `say`, Linux `espeak`)
- Mouse / motion‑sensing gun control
- Dynamic card layout with intelligent truncation for long text
- Real‑time score feedback, adjustable mouse sensitivity and window size
- Pause menu and settings

**Runtime Environment**: Python 3.7+, dependencies `pygame`, `pygame-menu`.

**Quick Start**:
```bash
conda create -n word_hunt python=3.9 -y
conda activate word_hunt
pip install -r requirements.txt
python wordhunt.py
```

> For detailed configuration (word bank JSON, scene JSON) and controls, see [WordTarget-Python/README.md](WordTarget-Python/README.md)

## 🚀 Overall Quick Start

1. **Build the AirGun** – Connect components as per [AirGun Hardware Requirements](AirGun/README.md#️-hardware-requirements) and flash the firmware.
2. **Choose a game client**:
   - For cross‑platform and richer scene experiences, we recommend **WordTarget**.
   - For lightweight operation or further development, use **WordTarget-Python**.
3. **Prepare word banks and scenes**:
   - Place word bank JSON files into `data/` (WordTarget) or `resource/` (WordTarget-Python).
   - Place scene images and annotation files into the corresponding directories.
4. **Pair Bluetooth** – In your computer/phone Bluetooth settings, connect to the device named “AirMouse”.
5. **Start the game**:
   - Select Classic Mode or Scene Mode from the main menu.
   - Aim at the cards on the screen with the motion‑sensing gun and pull the trigger to shoot the correct word.

## 🤝 Contribution & License

All three sub‑projects are released under the **MIT License**. Issues, Pull Requests, and custom word banks/scenes are welcome.

- Please read the contribution guidelines (if any) in each sub‑project before contributing.
- All code is for learning and communication purposes only; commercial use is prohibited.

## 📖 More Information

- **AirGun Parameter Tuning**: see [AirGun/README.md#-parameter-tuning](AirGun/README.md#-parameter-tuning)
- **Adding New Content to WordTarget**: see [WordTarget/README.md#adding-new-content](WordTarget/README.md#adding-new-content)
- **Creating Scene Mode in WordTarget-Python**: see [WordTarget-Python/README.md#-creating-scene-mode](WordTarget-Python/README.md#-creating-scene-mode)

---

**Happy shooting, happy learning!** 🎯📚
