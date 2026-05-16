# Word-Hunt-Range

![License](https://img.shields.io/badge/License-MIT-green.svg)

[English](README_EG.md) | [中文](README.md)

**Word-Hunt-Range** 是一个完整的单词学习生态系统，由三个子项目组成：蓝牙体感枪硬件驱动 `AirGun`、基于 Godot 引擎的跨平台游戏 `WordTarget`，以及基于 Python/Pygame 的轻量级游戏 `WordTarget-Python`。  
该项目旨在通过体感交互和趣味游戏，让英语词汇学习变得生动、高效。

产品：https://sybupt.github.io/Word-Hunt-Range/

## 📦 子项目一览

| 子项目 | 技术栈 | 定位 | 核心特性 |
|--------|--------|------|----------|
| **AirGun** | ESP32 / C++ | 蓝牙体感枪硬件驱动 | 将物理枪械的瞄准动作转换为鼠标光标移动，支持左键射击 |
| **WordTarget** | Godot 4.6 / GDScript | 跨平台单词学习游戏（主推荐） | 听音选词、场景探索、生命/计时模式、丰富的预置词库与场景 |
| **WordTarget-Python** | Python / Pygame | 轻量级单词射击游戏 | 英译中/中译英/听音选词、场景选词、动态卡片布局、系统原生语音 |

## 🎯 整体架构

```
Word-Hunt-Range
├── AirGun                    # 硬件层：ESP32 体感枪，通过 BLE HID 模拟鼠标
├── WordTarget                # 应用层（主力）：Godot 游戏，支持 Windows/macOS/Linux
└── WordTarget-Python         # 应用层（轻量）：Python 游戏，适合快速体验和二次开发
```

- **AirGun** 与任意一个游戏配合使用：游戏通过鼠标左键识别射击，AirGun 的移动控制光标位置，扣下扳机即触发左键点击。
- **WordTarget** 和 **WordTarget-Python** 的数据格式（词库 JSON、场景标注 JSON）完全兼容，可以共用 `resource/` 目录下的学习资源。

## 🔫 子项目详细介绍

### 1. AirGun – 基于 ESP32 的蓝牙体感枪

[![License](https://img.shields.io/badge/License-MIT-green.svg)](AirGun/LICENSE)

从陀螺仪到鼠标移动——高精度、低延迟的无线体感瞄准方案。

**主要特性**：
- MPU6050 六轴陀螺仪，可配置增益、死区、平滑滤波
- 动态零漂校准，消除温漂和累积误差
- 双核任务架构：200Hz 采样 + 独立 BLE 发送
- 防累积限幅，防止蓝牙卡顿时光标瞬移
- 低功耗设计，电池电量自动上报
- 按键硬件消抖，响应准确

**硬件需求**：ESP32 开发板、MPU6050 传感器、轻触开关、单节锂电池（1.8V~2.5V）。

**软件安装**：使用 VSCode + PlatformIO，依赖 `ESP32 BLE Mouse`、`MPU6050_light`、`Bounce2` 库。

> 详细硬件连接、参数调校和性能说明请参阅 [AirGun/README.md](AirGun/README.md)

### 2. WordTarget – 互动式英语词汇学习游戏

[![Godot Version](https://img.shields.io/badge/Godot-4.6+-blue.svg)](https://godotengine.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](VocaBee/LICENSE)

基于 Godot 4.6 开发的引人入胜的英语词汇学习平台，专为不同英语水平的学习者设计。

**游戏模式**：
- **听音选词**：根据音频选择正确的单词卡片
- **场景游戏模式**：在真实场景图片（卧室、教室、医院等）中点击物体学习单词

**学习内容**：
- 词汇集：CET-4、CET-6、TEM-4、TEM-8、高考、中考
- 场景环境：卧室、教室、医院、餐厅、超市
- 双语支持：单词、中文翻译、音标

**游戏机制**：
- 正确答案得分，错误扣除生命值或时间
- 动态卡片布局，智能防止重叠
- 依赖系统文字转语音（可选）

**快速开始**：
1. 安装 Godot 4.6+
2. 克隆仓库，在 Godot 中打开 `project.godot`
3. 按 `F5` 运行

> 详细项目结构、内容添加和故障排除请参阅 [WordTarget/README.md](WordTarget/README.md)

### 3. WordTarget-Python – 单词射击游戏（Python 实现）

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Pygame)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](WordTarget-Python/LICENSE)

从蓝牙体感枪到单词射击——用真正的“枪”瞄准、射击、学单词。

**特性**：
- 三种经典模式：英译中、中译英、听音选词（自动朗读）
- 场景选词模式：自定义场景图片，单词卡片出现在标注位置
- 系统原生语音（Windows SAPI/PowerShell、macOS `say`、Linux `espeak`）
- 鼠标 / 体感枪控制
- 动态卡片布局，长文本智能截断
- 实时得分反馈，可调鼠标灵敏度和窗口大小
- 暂停菜单与设置

**运行环境**：Python 3.7+，依赖 `pygame`、`pygame-menu`。

**快速开始**：
```bash
conda create -n word_hunt python=3.9 -y
conda activate word_hunt
pip install -r requirements.txt
python wordhunt.py
```

> 详细配置（词库 JSON、场景 JSON）和操作指南请参阅 [WordTarget-Python/README.md](WordTarget-Python/README.md)

## 🚀 整体快速开始

1. **制作 AirGun 体感枪**：按照 [AirGun 硬件需求](AirGun/README.md#️-硬件需求) 连接组件，烧录固件。
2. **选择游戏客户端**：
   - 若追求跨平台和更丰富的场景体验，推荐 **WordTarget**。
   - 若希望轻量级运行或二次开发，使用 **WordTarget-Python**。
3. **准备词库与场景**：
   - 词库 JSON 文件放入 `data/`（WordTarget）或 `resource/`（WordTarget-Python）。
   - 场景图片与标注文件放入相应目录。
4. **配对蓝牙**：在电脑/手机蓝牙设置中连接名为 “AirMouse” 的设备。
5. **开始游戏**：
   - 在游戏主菜单中选择经典模式或场景模式。
   - 用体感枪瞄准屏幕上的卡片，扣动扳机射击正确的单词。

## 🤝 贡献与许可证

三个子项目均采用 **MIT 许可证**，欢迎提交 Issue、Pull Request 或自行扩展词库和场景。

- 贡献前请阅读各子项目中的贡献指南（如有）。
- 所有代码仅供学习交流，严禁商用。

## 📖 更多信息

- **AirGun 参数调校**：见 [AirGun/README.md#-参数调校](AirGun/README.md#-参数调校)
- **WordTarget 添加新内容**：见 [WordTarget/README.md#添加新内容](WordTarget/README.md#添加新内容)
- **WordTarget-Python 场景制作**：见 [WordTarget-Python/README.md#-场景模式制作](WordTarget-Python/README.md#-场景模式制作)

---

**快乐射击，快乐学单词！** 🎯📚
