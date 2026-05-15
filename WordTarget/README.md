# VocaBee - 互动式英语词汇学习游戏

[![Godot Version](https://img.shields.io/badge/Godot-4.6+-blue.svg)](https://godotengine.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.1-orange.svg)]()

[English](README_EG.md) | [中文](README.md)

VocaBee 是一个基于 Godot 4.6 开发的引人入胜的英语词汇学习平台。专为不同英语水平的学习者设计，提供多种互动游戏模式，让词汇学习既有效又有趣。

## 🎯 功能特性

### 游戏模式
- **听音选词**：基于音频的词汇识别，配有视觉单词卡片
- **场景游戏模式**：现实场景探索，互动识别物体
  - **看英文选中文**：根据英文单词在场景中点击对应中文翻译
  - **听音选英**（v0.1.1 新增）：播放音频提示，在场景中点击对应英文单词

### 学习内容
- **词汇集**：CET-4、CET-6、TEM-4、TEM-8、大学入学考试、高中入学考试
- **场景环境**：14 个生活场景（浴室、海滩、卧室、教室、餐厅等）
- **双语支持**：英语单词配中文翻译和音标

### 游戏机制
- **评分系统**：正确答案得分
- **生命/计时模式**：选择生命制或限时玩法
- **动态卡片布局**：智能定位防止重叠，确保公平游戏
- **文字转语音**：词汇发音（依赖系统）
- **消灭特效**（v0.1.1 新增）：答对时触发烟火粒子、屏幕震动、卡片分裂动画
- **自定义光标系统**（v0.1.1 新增）：支持静态准星和动态动画准星

### 光标系统
- **静态准星**：`target.png`（靶心准星）和 `crosshair.png`（十字准星），通过 `DisplayServer.cursor_set_custom_image()` 设置，由操作系统层渲染，跟手流畅无延迟
- **动态准星**：12 帧序列动画（由 `tool/TargetCursorAnimation.py` 使用 Manim 生成），通过 Sprite2D + CanvasLayer 实现，每帧跟随鼠标位置
- **当前问题**：动态准星使用 `_process()` 中 `get_viewport().get_mouse_position()` 更新位置，存在一帧延迟，跟手性不如静态准星（静态准星由 OS 层直接处理鼠标事件）

## 🚀 快速开始

### 前置要求
- **Godot 引擎 4.6 或更高版本** - 从 [godotengine.org](https://godotengine.org/download) 下载
- **操作系统**：Windows 10+、macOS 10.14+、Linux (Ubuntu 18.04+)

### 安装

1. **克隆仓库**：
   ```bash
   git clone <仓库地址> VocaBee
   cd VocaBee
   ```

2. **在 Godot 中打开**：
   - 启动 Godot 引擎
   - 点击 "导入" → 选择 VocaBee 文件夹中的 `project.godot`
   - 等待资源导入完成（首次可能需要 1-2 分钟）

3. **运行游戏**：
   - 按 `F5` 或点击 Godot 中的 "播放" 按钮
   - 游戏将从主菜单开始

### 独立分发

创建可执行文件进行分发：

1. 在 Godot 中打开项目
2. 转到 **项目 → 导出**
3. 点击 **添加...** 并选择目标平台（Windows、macOS、Linux）
4. 根据需要配置导出设置
5. 点击 **导出项目** 并选择保存位置
6. 可执行文件将在指定位置创建

## 📁 项目结构

```
VocaBee/
├── project.godot              # Godot 项目配置
├── icon.svg                   # 游戏图标
├── assets/
│   ├── cursor/                # 光标素材
│   │   ├── target.png         # 静态准星 1（靶心）
│   │   ├── crosshair.png      # 静态准星 2（十字）
│   │   └── cursor_frames/     # 动态准星序列帧（12帧）
│   ├── scene_imgs/            # 场景背景图片（14个场景）
│   └── sound_icon.png         # 音量图标
├── data/
│   ├── *.json                 # 词汇数据集（6套）
│   └── scene_data/
│       └── *.json             # 场景标注数据（14个场景）
├── scenes/                    # Godot 场景文件 (.tscn)
│   ├── autoload/              # 全局场景管理器
│   ├── common/                # 可复用 UI 组件
│   ├── menu/                  # 菜单场景
│   └── mods/                  # 游戏模式场景
├── scripts/                   # GDScript 源文件
│   ├── autoload/              # 全局脚本
│   ├── common/                # 共享组件
│   ├── menu/                  # 菜单逻辑
│   └── mods/                  # 游戏模式逻辑
├── tool/
│   ├── annotate.py            # 场景标注工具（Python/Tkinter）
│   └── TargetCursorAnimation.py  # 动态光标生成工具（Python/Manim）
└── doc/                       # 项目文档
```

## 🎮 玩法说明

### 主场景
- 主场景是 `main_menu.tscn`，这是游戏的入口点。

1. **主菜单**：选择偏好的游戏模式
2. **模式选择**：在听音选词或场景游戏模式之间选择
3. **词汇选择**：从可用单词集中选择
4. **游戏玩法**：
   - **听音选词**：聆听发音，选择正确的单词卡片
   - **场景游戏模式**：在场景中点击高亮物体来识别单词
5. **评分**：正确答案得分，错误则失去生命/时间

### 注意事项
- 登录和注册按钮：这些按钮设计用于进入游戏模式选择，但目前尚未完善。
- 退出按钮：退出游戏的功能尚未实现。
- 设置按钮：游戏设置功能尚未完善。

## 🛠️ 开发

### 要求
- Godot 4.6+
- Python 3.x（用于标注工具和光标生成工具）

### 从源码构建
1. 确保安装 Godot 4.6+
2. 克隆仓库
3. 在 Godot 中打开 `project.godot`
4. 进行修改
5. 提交前进行全面测试

### 添加新内容

#### 词汇集
在 `data/` 中添加新的 JSON 文件，格式如下：
```json
{
  "1": {
    "english": "word",
    "chinese_trans": "翻译",
    "spell": "/音标/"
  }
}
```

#### 场景数据
使用 `tool/annotate.py` 创建场景标注：
```bash
python tool/annotate.py --image path/to/image.png --output data/scene_data/new_scene.json
```

#### 动态光标
使用 `tool/TargetCursorAnimation.py` 生成动态光标序列帧：
```bash
manim -pql tool/TargetCursorAnimation.py --format=png --transparent
```

## 🔧 故障排除

### 常见问题

**"JSON 文件未找到" 错误**
- 确保 `data/` 目录中的所有文件都存在
- 检查脚本中的文件路径是否与实际位置匹配

**图片无法加载**
- 验证 `assets/scene_imgs/` 包含所有必需的 PNG 文件
- 检查 Godot 中的导入设置

**文字转语音不工作**
- TTS 依赖系统功能
- 没有音频的情况下游戏仍可完全游玩

**卡片重叠或超出屏幕**
- 布局算法自动处理定位
- 检查 `LayoutSolver2D.gd` 中的边界设置

**场景过渡失败**
- 验证 `scenes/` 目录中存在所有场景文件 (.tscn)
- 检查过渡脚本中的场景路径

**动态光标跟手不佳**
- 动态准星通过 Sprite2D 在 `_process()` 中跟随鼠标，存在固有延迟
- 建议优先使用静态准星（target.png / crosshair.png），由 OS 层渲染，跟手流畅

### 性能提示
- 游戏时关闭其他应用程序
- 确保足够的内存（推荐 2GB+）
- 更新显卡驱动以获得最佳性能

## 🤝 贡献

我们欢迎贡献！请：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 指南
- 遵循 Godot GDScript 风格指南
- 在不同平台上全面测试更改
- 为新功能更新文档
- 确保与 Godot 4.6+ 的兼容性

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 使用 [Godot 引擎](https://godotengine.org/) 构建
- 词汇数据来源于标准英语水平考试
- 场景图片来源于教育资源

---

**快乐学习！** 🐝📚