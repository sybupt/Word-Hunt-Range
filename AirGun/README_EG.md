# 🔫 AirGun: ESP32-based Bluetooth Light Gun

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](README_EG.md) | [中文](README.md)

From gyroscope to mouse movement — high-precision, low-latency wireless motion‑sensing aiming solution

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Hardware Requirements](#️-hardware-requirements)
- [🔌 Pin Connections](#-pin-connections)
- [⚙️ Software Installation](#️-software-installation)
- [🚀 Quick Start](#-quick-start)
- [🔧 Parameter Tuning](#-parameter-tuning)
- [📊 Performance Notes](#-performance-notes)
- [📝 Acknowledgements & License](#-acknowledgements--license)

## ✨ Features

- **High‑precision motion sensing**: Based on MPU6050 6‑axis gyroscope, supports configurable gain, dead zone, smoothing filter, and Y‑axis inversion.
- **Dynamic zero‑drift calibration**: Automatically updates gyroscope bias when stationary, eliminating temperature drift and long‑term accumulated error.
- **Dual‑core task architecture**: Sensor reading and BLE transmission are separated, ensuring 200Hz sampling rate while preventing Bluetooth stutter from affecting data acquisition.
- **Anti‑accumulation limiting**: Automatically truncates pending displacement when it exceeds the upper limit, preventing mouse jumps after severe BLE blocking.
- **Low‑power design**: BLE task is suspended when not connected; after connection it sends at fixed intervals, reducing idle power consumption.
- **Battery level reporting**: Reads battery voltage via ADC, automatically converts to percentage and reports to host over Bluetooth.
- **Button debouncing**: Hardware debouncing implemented with the Bounce2 library for accurate click response.

## 🛠️ Hardware Requirements

- Microcontroller: ESP32 (any dual‑core model, e.g., ESP32‑WROOM‑32)
- Motion sensor: MPU6050 (I2C)
- Button: One momentary switch (left button)
- Battery: Single‑cell Li‑ion (compatible with 1.8V ~ 2.5V range)
- Other: 10kΩ resistors (for battery voltage measurement, optional), USB‑Micro serial download cable

## 🔌 Pin Connections

| Component            | Pin   |
|----------------------|-------|
| Button               | GPIO 4|
| Battery voltage sense| GPIO 2|
| MPU6050 SDA          | GPIO21|
| MPU6050 SCL          | GPIO22|

The button uses internal pull‑up and is active low. For battery voltage detection, divide the battery positive voltage through two resistors (e.g., 100kΩ and 100kΩ) and connect to GPIO2, ensuring the divided voltage does not exceed 3.3V.

## ⚙️ Software Installation

1. **Install VSCode and PlatformIO plugin**  
   Install PlatformIO IDE from the Visual Studio Code extension marketplace.

2. **Clone or create a project**  
   Create a new PlatformIO project and place the provided `main.cpp` into the `src/` directory.

3. **Install library dependencies**  
   Add the following library dependencies to `platformio.ini`:
   ```ini
   lib_deps = 
       t-vk/ESP32 BLE Mouse @ ^0.3.1
       rfetick/MPU6050_light @ ^1.1.0
       thomasfredericks/Bounce2@^2.72
   ```
   Also set the board to `esp32dev` and upload speed to 921600.

4. **Compile and upload**  
   Connect the ESP32 and click the “Upload” button in PlatformIO. The first run will automatically calibrate the gyroscope; keep the device level and stationary.

## 🚀 Quick Start

1. **Power on**: After the ESP32 starts, “Init Done.” will be printed to the serial monitor, and the Bluetooth device name “AirMouse” will appear (you can modify the name in the `BleMouse` constructor).
2. **Pair**: Search for “AirMouse” in the Bluetooth settings of your computer/phone and connect. On successful connection, a buzzer (if present) or the serial monitor will output “[BLE] Connected”.
3. **Usage**:
   - Move the device: The cursor moves accordingly. Angle sensitivity can be adjusted via parameters like `GAIN`.
   - Press the button: Triggers a left mouse click.
   - Battery level: Reported automatically once after connection, then every 30 seconds.
4. **Disconnect**: Turn off the device or disconnect Bluetooth; the task will automatically pause and wait for reconnection.

## 🔧 Parameter Tuning

All core parameters are defined with `#define` at the top of the file. They can be modified according to hardware and user preference.

### Motion Control Parameters

| Macro               | Default | Description                                                              |
|---------------------|---------|--------------------------------------------------------------------------|
| `GAIN`              | 0.25    | Conversion gain from raw gyroscope angular velocity (rad/s) to cursor movement (pixels). Larger values give faster movement. |
| `DEAD_ZONE`         | 0.8     | Dead zone threshold (rad/s). Tiny jitter below this value is ignored.    |
| `SMOOTH_FACTOR`     | 0.5     | Exponential smoothing coefficient (0~1). Higher values give faster response, lower values give smoother motion. |
| `INVERT_Y`          | 1       | Y‑axis inversion switch (1 = invert, 0 = normal).                       |

### Stationary Detection and Zero‑Drift Calibration

| Macro                     | Default | Description                                                              |
|---------------------------|---------|--------------------------------------------------------------------------|
| `STILL_WIN`               | 60      | Sliding window length (frames) for stationary detection.                |
| `RANGE_THRESH`            | 1.2     | Threshold for angular velocity range within the window (rad/s). Below this value, considered candidate stationary. |
| `ABS_THRESH`              | 2.0     | Threshold for the absolute mean of angular velocity within the window.  |
| `STILL_COUNT_THRESH`      | 80      | Number of consecutive frames satisfying stationary conditions to confirm stillness and start bias update. |
| `MOTION_LOCK_COUNT`       | 100     | Number of frames locked after motion occurs; during this period bias is not updated. |
| `BIAS_ALPHA`              | 0.008   | Exponential weighted moving average coefficient for bias update.        |
| `ACCUM_CLEAR_MS`          | 1000    | Time (ms) to wait after confirming stillness before clearing unsent accumulated displacement. |

### BLE Transmission Parameters

| Macro                     | Default | Description                                                              |
|---------------------------|---------|--------------------------------------------------------------------------|
| `PENDING_LIMIT`           | 2000    | Upper limit of unsent displacement (pixels). Exceeding this limit triggers truncation to prevent large jumps caused by Bluetooth congestion. |
| `BLE_SEND_INTERVAL_MS`    | 60      | Fixed interval (ms) of the BLE transmission task. 60ms is most stable on Windows; can be changed to 45ms for better smoothness on Mac/Android. |

## 📊 Performance Notes

- **Sampling rate**: 200Hz (MPU6050 is read every 5ms)
- **Latency**: Total delay from sensor acquisition to Bluetooth transmission = READ_INTERVAL(5ms) + scheduling jitter(≈1ms) + half of BLE_SEND_INTERVAL(60ms) (average 30ms) ≈ 36ms. Actual feel is smooth with no noticeable lag.
- **Power consumption**: Approximately 40mA when not connected, approximately 60mA when connected (depends on Bluetooth transmit power and battery voltage).
- **Accuracy**: Bias can be stabilised within ±0.5 rad/s when stationary, drift rate < 1°/min when moving.

## 📝 Acknowledgements & License

The core algorithms and task architecture of this project reference many practices from the open‑source community. Special thanks to:

- The `BleMouse` library for providing the Bluetooth HID implementation.
- The `MPU6050_light` library for providing a convenient MPU6050 driver.
- The `Bounce2` library for robust button debouncing.

The code is released under the MIT license. You are free to use, modify, and distribute it, but please retain the original copyright notice.
